# -*- mode: python; coding: utf-8 -*-

# Copyright (c) 2009-2011 Oscar Aceña.
# Based on Java version of IceBox, by ZeroC, Inc.

# This file is part of PyIceBox.
#
# PyIceBox is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, version 2 of the License.
#
# PyIceBox is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with PyIceBox.  If not, see <http://www.gnu.org/licenses/>.

# This is a wrapper for Ice.Communicator objects,
# because the Python version does not have certain
# useful methods. If provided, this is of no use.

from __future__ import with_statement

from threading import Lock
import Ice

from ProcessI import ProcessI
from PropertiesAdminI import PropertiesAdminI
from TraceLevels import TraceLevels
from Util import synchronized


class Communicator(Ice.Communicator):

    # Communicator status, as these are private within Ice.Communicator
    StateActive, StateDestroyInProgress, StateDestroyed = range(3)

    def __init__(self, communicator):
        # private, only needed for wrapper
        self._communicator = communicator
        self._lock = Lock()

        self._adminAdapter = None
        self._adminIdentity = None
        self._adminFacetFilter = []
        self._traceLevels = TraceLevels(self._communicator.getProperties())

        # unmodified method redirection
        self.shutdown = self._communicator.shutdown
        self.waitForShutdown = self._communicator.waitForShutdown
        self.isShutdown = self._communicator.isShutdown
        self.stringToProxy = self._communicator.stringToProxy
        self.proxyToString = self._communicator.proxyToString
        self.propertyToProxy = self._communicator.propertyToProxy
        self.stringToIdentity = self._communicator.stringToIdentity
        self.identityToString = self._communicator.identityToString
        self.createObjectAdapter = self._communicator.createObjectAdapter
        self.createObjectAdapterWithEndpoints = self._communicator.createObjectAdapterWithEndpoints
        self.createObjectAdapterWithRouter = self._communicator.createObjectAdapterWithRouter
        self.addObjectFactory = self._communicator.addObjectFactory
        self.findObjectFactory = self._communicator.findObjectFactory
        self.getDefaultContext = self._communicator.getDefaultContext
        self.setDefaultContext = self._communicator.setDefaultContext
        self.getImplicitContext = self._communicator.getImplicitContext
        self.getProperties = self._communicator.getProperties
        self.getLogger = self._communicator.getLogger
        self.getStats = self._communicator.getStats
        self.getDefaultRouter = self._communicator.getDefaultRouter
        self.setDefaultRouter = self._communicator.setDefaultRouter
        self.getDefaultLocator = self._communicator.getDefaultLocator
        self.setDefaultLocator = self._communicator.setDefaultLocator
        self.getPluginManager = self._communicator.getPluginManager
        self.flushBatchRequests = self._communicator.flushBatchRequests

        # communicator state
        self._state = self.StateActive

        self._adminFacets = {
            "Properties": PropertiesAdminI(self._communicator.getProperties()),
            "Process": ProcessI(self._communicator)}


    # Destroy the communicator. Implemented to keep track of status.
    def destroy():
        with self._lock:
            if self._state != self.StateActive:
                return
            self._state = self.StateDestroyInProgress

        self._communicator.destroy()

        with self._lock:
            self._state = self.StateDestroyed


    # Get a proxy to the main facet of the Admin object.
    # returns -> Object*
    def getAdmin(self):

        adapter = None
        serverId = None
        defaultLocator = None

        props = self._communicator.getProperties()

        with self._lock:
            if self._state == self.StateDestroyed:
                raise Ice.CommunicatorDestroyedException()

            adminOA = "Ice.Admin"

            if self._adminAdapter:
                return self._adminAdapter.createProxy(self._adminIdentity)

            elif not props.getProperty(adminOA + ".Endpoints"):
                return None

            else:
                serverId = props.getProperty("Ice.Admin.ServerId")
                instanceName = props.getProperty("Ice.Admin.InstanceName")

                defaultLocator = self._communicator.getDefaultLocator()

                if (defaultLocator and serverId) or instancename:
                    if not self._adminIdentity:

                        if not instanceName:
                            instanceName = Ice.generateUUID()

                        self._adminIdentity = Ice.Identity("admin", instanceName)
                        # Afterwards, _adminIdentity is read-only

                    # Create OA
                    self._adminAdapter = self._communicator.createObjectAdapter(adminOA)

                    # Add all facets to OA
                    filteredFacets = {}
                    for key, value in self._adminFacets.items():
                        if not self._adminFacetFilter or key in self._adminFacetFilter:
                            self._adminAdapter.addFacet(value, self._adminIdentity, key)

                        else:
                            filteredFacets[key] = value

                    self._adminFacets = filteredFacets

                    adapter = self._adminAdapter

        if not adapter:
            return None

        try:
            adapter.activate()

        except Ice.LocalException, ex:

            # We cleanup _adminAdapter, however this error is not recoverable
            # (can't call again getAdmin() after fixing the problem)
            # since all the facets (servants) in the adapter are lost

            adapter.destroy()
            with self._lock:
                self._adminAdapter = None
            raise

        admin = adapter.createProxy(self._adminIdentity)

        if defaultLocator and serverId:
            process = Ice.ProcessPrx.uncheckedCast(admin.ice_facet("Process"))

            try:
                # Note that as soon as the process proxy is registered, the communicator might be
                # shutdown by a remote client and admin facets might start receiving calls.

                defaultLocator.getRegistry().setServerProcessProxy(serverId, process)

            except Ice.ServerNotFoundException, ex:
                if self._traceLevels.location >= 1:
                    self._communicator.getLogger().trace(
                        self._traceLevels.locationCat,
                        "couldn't register server '" + serverId + "' " +
                        "with the locator registry:\n" +
                        "the server is not known to the locator registry")

                raise Ice.InitializationException("Locator knows nothing about server '" + serverId + "'")

            except Ice.LocalException, ex:
                if self._traceLevels.location >= 1:
                    self._communicator.getLogger().trace(
                        self._traceLevels.locationCat,
                        "couldn't register server '" + serverId + "' " +
                        "with the locator registry:\n" + str(ex))

                raise

            if self._traceLevels.location >= 1:
                self._communicator.getLogger().trace(
                    self._traceLevels.locationCat,
                    "registered server '" + serverId + "' " +
                    "with the locator registry")

        return admin


    # Add a new facet to the Admin object.
    # servant:Object, facet:string
    @synchronized
    def addAdminFacet(self, servant, facet):
        if self._state == self.StateDestroyed:
            raise Ice.CommunicatorDestroyedException()

        if not self._adminAdapter or (self._adminFacetFilter and facet not in self._adminFacetFilter):
            if self._adminFacets.get(facet):
                raise Ice.AlreadyRegisteredException("facet", facet)

            self._adminFacets[facet] = servant

        else:
            self._adminAdapter.addFacet(servant, self._adminIdentity, facet)


    # Remove the following facet to the Admin object.
    # facet:string
    # returns -> Object
    @synchronized
    def removeAdminFacet(self, facet):
        if self._state == self.StateDestroyed:
            raise Ice.CommunicatorDestroyedException()

        result = None
        if not self._adminAdapter or (self._adminFacetFilter and not facet in self._adminFacetFilter):

            if not facet in self._adminFacets:
                raise Ice.NotRegisteredException("facet", facet)

            result = self._adminFacets.pop(facet)

        else:
            result = self._adminAdapter.removeFacet(self._adminIdentity, facet)

        return result


