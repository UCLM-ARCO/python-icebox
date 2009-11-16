# -*- mode: python; coding: utf-8 -*-

# Copyright (c) 2009 Arco Labs.
# Based on Java version of IceBox, by ZeroC Inc.

# This file is part of IceBoxPy.
#
# IceBoxPy is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, version 2 of the License.
#
# IceBoxPy is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with IceBoxPy.  If not, see <http://www.gnu.org/licenses/>.


from __future__ import with_statement

import sys
import copy
import traceback
from threading import RLock, Event
from StringIO import StringIO

import Ice
import IceBox

import UtilInternal
from PropertiesAdminI import PropertiesAdminI
from Util import synchronized


# format traceback messages
def _ftrace(msg):
    r = []
    for c in msg:
        if c == "\n": c = "\n    ->  "
        r.append(c)
    return "".join(r)


class ServiceManagerI(IceBox.ServiceManager):

    def __init__(self, communicator, args):
        # NOTE: the python version of Communicator does not have "Admin" methods
        # (getAdmin, addAdminFacet, removeAdminFacet), so this wrapper
        # will do the trick for us.
        self._communicator = UtilInternal.Communicator(communicator)
        self._sharedCommunicator = None

        self._logger = self._communicator.getLogger()

        self._argv = args
        self._services = []

        self._statusChangesDone = Event()
        self._statusChangesDone.set()

        self._observers = []

        props = self._communicator.getProperties()
        key = "IceBox.Trace.ServiceObserver"
        self._traceServiceObserver = props.getPropertyAsInt(key)

        # for using on synchronized methods
        self._lock = RLock()


    def getSliceChecksums(self, current):
        return Ice.sliceChecksums


    def startService(self, name, current):
        info = None
        with self._lock:

           # Search would be more efficient if services were contained in
           # a map, but order is required for shutdown.

            for s in self._services:
                if s.name == name:
                    if s.status == self.StatusStarted:
                        raise IceBox.AlreadyStartedException()

                    s.status = self.StatusStarting
                    info = s.clone()
                    break

            if not info:
                raise IceBox.NoSuchServiceException()

            self._statusChangesDone.clear()

        started = False

        try:
            if info.communicator: comm = info.communicator
            else: comm = self._sharedCommunicator
            info.service.start(name, comm, info.args)
            started = True

        except Exception, e:
            sio = StringIO()
            traceback.print_exc(file=sio)
            self._logger.warning(
                "ServiceManager: exception in start for service " + info.name + "\n" +
                _ftrace(sio.getvalue()))

        with self._lock:
            for s in self._services:
                if s.name == name:
                    if started:
                        s.status = self.StatusStarted
                        self._servicesStarted([name], self._observers)

                    else:
                        s.status = self.StatusStopped

                    break

            # notifyAll() is implicit
            self._statusChangesDone.set()


    def stopService(self, name, current):
        info = None
        with self._lock:
            # Search would be more efficient if services were contained in
            # a map, but order is required for shutdown.

            for s in self._services:
                if s.name == name:
                    if s.status == self.StatusStopped:
                        raise IceBox.AlreadyStoppedException()

                    s.status = self.StatusStopping
                    info = s.clone()
                    break

            if not info:
                raise IceBox.NoSuchServiceException()

            self._statusChangesDone.clear()

        stopped = False
        try:
            info.service.stop()
            stopped = True

        except Exception, e:
            sio = StringIO()
            traceback.print_exc(file=sio)
            self._logger.warning(
                "ServiceManager: exception in stop for service " + info.name + "\n" +
                _ftrace(sio.getvalue()))

        with self._lock:
            for s in self._services:
                if s.name == name:
                    if stopped:
                        s.status = self.StatusStopped
                        self._servicesStopped([name], self._observers)

                    else:
                        s.status = self.StatusStarted

                    break

            # notifyAll() is implicit
            self._statusChangesDone.set()


    def addObserver(self, observer, current):
        activeServices = []

        # Null observers and duplicate registrations are ignored
        with self._lock:
            if observer and not observer in self._observers:
                self._observers.append(observer)

                if self._traceServiceObserver >= 1:
                    self._logger.trace("IceBox.ServiceObserver",
                                       "Added service observer " + self._communicator.proxyToString(observer))

                for info in self._services:
                    if info.status == self.StatusStarted:
                        activeServices.append(info.name)

        if activeServices:

            class AMI_ServiceObserver_servicesStarted:
                def ice_response():
                    # ok, success
                    pass

                def ice_exception(ex):
                    # Drop this observer
                    self._removeObserver(observer, ex)

            cb = AMI_ServiceObserver_servicesStarted()
            observer.servicesStarted_async(cb, activeServices)


    def shutdown(self, current):
        self._communicator.shutdown()


    def run(self):
        try:
            properties = self._communicator.getProperties()

            # Create an object adapter. Services probably should NOT share
            # this object adapter, as the endpoint(s) for this object adapter
            # will most likely need to be firewalled for security reasons.

            adapter = None
            if properties.getProperty("IceBox.ServiceManager.Endpoints"):

                adapter = self._communicator.createObjectAdapter("IceBox.ServiceManager")

                identity = Ice.Identity()
                identity.category = properties.getPropertyWithDefault("IceBox.InstanceName", "IceBox")
                identity.name = "ServiceManager"
                adapter.add(self, identity)

            # Parse the property set with the prefix "IceBox.Service.". These
            # properties should have the following format:
            #
            # IceBox.Service.ServiceName = Module.Class [args]
            #
            # We parse the service properties specified in IceBox.LoadOrder
            # first, then the ones from remaining services.

            prefix = "IceBox.Service."
            services = properties.getPropertiesForPrefix(prefix)
            loadOrder = properties.getPropertyAsList("IceBox.LoadOrder")
            servicesInfo = []

            for i in loadOrder:
                key = prefix + i

                try:
                    value = services[key]
                except KeyError:
                    raise IceBox.FailureException("ServiceManager: no service definition for '%s'" % i)

                servicesInfo.append(self.StartServiceInfo(i, value, self._argv))
                services.pop(key)

            for k,value in services.items():
                name = k.replace(prefix, "")
                servicesInfo.append(self.StartServiceInfo(name, value, self._argv))

            # Check if some services are using the shared communicator in which
            # case we create the shared communicator now with a property set
            # which is the union of all the service properties (services which
            # are using the shared communicator).

            if properties.getPropertiesForPrefix("IceBox.UseSharedCommunicator."):
                initData = Ice.InitializationData()
                initData.properties = self._createServiceProperties("SharedCommunicator")

                for service in servicesInfo:
                    if properties.getPropertyAsInt("IceBox.UseSharedCommunicator." + service.name) <= 0:
                        continue

                    # Load the service properties using the shared communicator
                    # properties as the default properties.
                    svcProperties = Ice.createProperties(service.args, initData.properties)

                    # Erase properties from the shared communicator which don't
                    # exist in the service properties (which include the shared
                    # communicator properties overriden by the service properties).
                    allProps = initData.properties.getPropertiesForPrefix("")
                    for key in allProps:
                        if not svcProperties.getProperty(key):
                            initData.properties.setProperty(key, "")

                    # Add the service properties to the shared communicator
                    # properties.
                    for k,v in svcProperties.getPropertiesForPrefix("").items():
                        initData.properties.setProperty(k, v)

                    # Parse <service>.* command line options (the Ice command line
                    # options were parsed by the createProperties above)
                    service.args = initData.properties.parseCommandLineOptions(service.name, service.args)

                self._sharedCommunicator = Ice.initialize(data=initData)

            for s in servicesInfo:
                self._start(s.name, s.classPath, s.args)

            # We may want to notify external scripts that the services
            # have started. This is done by defining the property:
            #
            # IceBox.PrintServicesReady=bundleName
            #
            # Where bundleName is whatever you choose to call this set of
            # services. It will be echoed back as "bundleName ready".
            #
            # This must be done after start() has been invoked on the
            # services.

            bundleName = properties.getProperty("IceBox.PrintServicesReady")
            if bundleName:
                print bundleName + " ready"

            # Register "this" as a facet to the Admin object and
            # create Admin object

            try:
                self._communicator.addAdminFacet(self, "IceBox.ServiceManager")

                # Add a Properties facet for each service
                for info in self._services:
                    communicator = info.communicator if info.communicator else self._sharedCommunicator
                    self._communicator.addAdminFacet(PropertiesAdminI(communicator.getProperties()),
                                                     "IceBox.Service." + info.name + ".Properties")
                self._communicator.getAdmin()

            except Ice.ObjectAdapterDeactivatedException, ex:
                pass

            if adapter:
                try:
                    adapter.activate()
                except Ice.ObjectAdapterDeactivatedException, ex:
                    pass

            self._communicator.waitForShutdown()

            # Invoke stop() on the services.
            self._stopAll()

        except IceBox.FailureException, ex:
            sio = StringIO()
            sio.write(ex.reason + "\n")
            traceback.print_exc(file=sio)
            self._logger.error(_ftrace(sio.getvalue()))
            self._stopAll()
            return 1

        except Ice.LocalException, ex:
            sio = StringIO()
            traceback.print_exc(file=sio)
            self._logger.error("ServiceManager: " + str(ex) + "\n" + _ftrace(sio.getvalue()))
            self._stopAll()
            return 1

        except Exception, ex:
            sio = StringIO()
            traceback.print_exc(file=sio)
            self._logger.error("ServiceManager: unknown exception: " + str(ex) +
                               "\n" + _ftrace(sio.getvalue()))
            self._stopAll()
            return 1

        return 0


    @synchronized
    def _start(self, service, classPath, args):
        # Instantiate the class.
        info = self.ServiceInfo()
        info.name = service
        info.status = self.StatusStopped
        info.args = args

        try:
            try:
                moduleName, className = classPath.split(".")
            except ValueError:
                raise IceBox.FailureException(
                    "ServiceManager: unable to retrieve class" + classPath)

            try:
                m = sys.modules[moduleName]
            except KeyError:
                m = __import__(moduleName)

            c = getattr(m, className)
            obj = c()

            if not isinstance(obj, IceBox.Service):
                raise IceBox.FailureException(
                    "ServiceManager: class " + classPath + " does not implement IceBox.Service")

            info.service = obj

        except ImportError, ex:
            raise IceBox.FailureException(
                "ServiceManager: class " + classPath + " not found\n" + str(ex))

        except AttributeError, ex:
            raise FailureException(
                "ServiceManager: module " + moduleName + " has not member " + className +
                "\n" + str(ex))

        except TypeError, ex:
            raise IceBox.FailureException(
                "ServiceManager: unable to instantiate class " + classPath +
                "\n" + str(ex))

        # Invoke Service::start().
        try:
            # If Ice.UseSharedCommunicator.<name> is defined, create a
            # communicator for the service. The communicator inherits
            # from the shared communicator properties. If it's not
            # defined, add the service properties to the shared
            # commnunicator property set.

            commnunicator = None
            if self._communicator.getProperties().getPropertyAsInt(
                "IceBox.UseSharedCommunicator." + service) > 0:
                assert self._sharedCommunicator, "invalid shared communicator"
                communicator = self._sharedCommunicator

            else:
                # Create the service properties. We use the communicator properties as the default
                # properties if IceBox.InheritProperties is set.

                initData = Ice.InitializationData()
                initData.properties = self._createServiceProperties(service)

                if info.args:
                    # Create the service properties with the given service arguments. This should
                    # read the service config file if it's specified with --Ice.Config.

                    initData.properties = Ice.createProperties(info.args, initData.properties)

                    # Next, parse the service "<service>.*" command line options (the Ice command
                    # line options were parsed by the createProperties above)

                    info.args = initData.properties.parseCommandLineOptions(service, info.args)

                # Remaining command line options are passed to the communicator. This is
                # necessary for Ice plug-in properties (e.g.: IceSSL).

                info.communicator = Ice.initialize(info.args, initData)
                communicator = info.communicator

            try:
                info.service.start(service, communicator, info.args)
                info.status = self.StatusStarted

                # There is no need to notify the observers since the 'start all'
                # (that indirectly calls this method) occurs before the creation of
                # the Server Admin object, and before the activation of the main
                # object adapter (so before any observer can be registered)

            except Exception, ex:
                if info.communicator:
                    try:
                        info.communicator.shutdown()
                        info.communicator.waitForShutdown()

                    except Ice.CommunicatorDestroyedException, ex:
                        # Ignore, the service might have already destroyed
                        # the communicator for its own reasons.
                        pass

                    except Exception, e:
                        sio = StringIO()
                        traceback.print_exc(file=sio)
                        self._logger.warning(
                            "ServiceManager: exception in shutting down communicator for service "
                            + service + "\n" + _ftrace(sio.getvalue()))

                    try:
                        info.communicator.destroy()
                    except Exception, e:
                        sio = StringIO()
                        traceback.print_exc(file=sio)
                        self._logger.warning(
                            "ServiceManager: exception in destroying communicator for service"
                            + service + "\n" + _ftrace(sio.getvalue()))

                raise

            self._services.append(info)

        except IceBox.FailureException, ex:
            raise

        except Exception, ex:
            raise IceBox.FailureException(
                "ServiceManager: exception while starting service " + service + ": " + str(ex))


    @synchronized
    def _stopAll(self):
        # First wait for any active startService/stopService calls to complete.
        self._statusChangesDone.wait()

        # For each service, we call stop on the service and flush its database environment to
        # the disk. Services are stopped in the reverse order of the order they were started.

        stoppedServices = []
        for info in reversed(self._services):
            if info.status == self.StatusStarted:

                try:
                    info.service.stop()
                    info.status = self.StatusStopped
                    stoppedServices.append(info.name)

                except Exception, e:
                    sio = StringIO()
                    traceback.print_exc(file=sio)
                    self._logger.warning(
                        "ServiceManager: exception in stop for service " + info.name + "\n" +
                        _ftrace(sio.getvalue()))

            try:
                self._communicator.removeAdminFacet(
                    "IceBox.Service." + info.name + ".Properties")

            except Ice.LocalException, e:
                # Ignored
                pass

            if info.communicator:
                try:
                    info.communicator.shutdown()
                    info.communicator.waitForShutdown()

                except Ice.CommunicatorDestroyedException, e:

                    # Ignore, the service might have already destroyed
                    # the communicator for its own reasons.
                    pass

                except Exception, e:
                    sio = StringIO()
                    traceback.print_exc(file=sio)
                    self._logger.warning(
                        "ServiceManager: exception in stop for service " + info.name + "\n" +
                        _ftrace(sio.getvalue()))

                try:
                    info.communicator.destroy()

                except Exception, e:
                    sio = StringIO()
                    traceback.print_exc(file=sio)
                    self._logger.warning(
                        "ServiceManager: exception in stop for service " + info.name + "\n" +
                        _ftrace(sio.getvalue()))

        if self._sharedCommunicator:
            try:
                self._sharedCommunicator.destroy()

            except Exception, e:
                sio = StringIO()
                traceback.print_exc(file=sio)
                self._logger.warning(
                    "ServiceManager: unknown exception while destroying shared communicator:\n" +
                    _ftrace(sio.getvalue()))

            self._sharedCommunicator = None

        self._services = []
        self._servicesStopped(stoppedServices, self._observers)


    def _servicesStarted(self, services, observers):
        if services:

            class AMI_ServiceObserver_servicesStarted:
                def ice_response():
                    # ok, success
                    pass

                def ice_exception(ex):
                    # Drop this observer
                    self._removeObserver(observer, ex)

            for observer in observers:
                cb = AMI_ServiceObserver_servicesStarted()
                observer.servicesStarted_async(cb, services)


    def _servicesStopped(self, services, observers):
        if services:

            class AMI_ServiceObserver_servicesStopped:
                def ice_response():
                    # ok, success
                    pass

                def ice_exception(ex):
                    # Drop this observer
                    self._removeObserver(observer, ex)

            for observer in observers:
                cb = AMI_ServiceObserver_servicesStopped()
                observer.servicesStopped_async(cb, services)


    @synchronized
    def _removeObserver(observer, ex):
        if observer in self._observers:
            self.observers.remove(observer)
            self.observerRemoved(observer, ex)


    def observerRemoved(observer, ex):
        if self._traceServiceObserver >= 1:

            # CommunicatorDestroyedException may occur during shutdown. The observer notification has
            # been sent, but the communicator was destroyed before the reply was received. We do not
            # log a message for this exception.

            if not isinstance(ex, Ice.CommunicatorDestroyedException):
                self._logger.trace(
                    "IceBox.ServiceObserver",
                    "Removed service observer " + self._communicator.proxyToString(observer) +
                    "\nafter catching " + str(ex))


    StatusStopping, StatusStopped, StatusStarting, StatusStarted = range(4)


    class ServiceInfo:

        def __init__(self):
            self.name = ""
            self.service = None
            self.communicator = None
            self.status = 0
            self.args = []

        def clone(self):
            return copy.copy(self)


    class StartServiceInfo:

        def __init__(self, service, value, serverArgs):
            self.name = service

            # Separate the entry point from the arguments.
            # split will use any whitespace string as separator (' ', \t, \n)
            fields = value.split()

            if len(fields) < 2:
                self.classPath = value
                self.args = []

            else:
                self.classPath = fields[0]
                try:
                    self.args = UtilInternal.Options.split(" ".join(fields[1:]))

                except UtilInternal.Options.BadQuote, ex:
                    raise IceBox.FailureException(
                        "ServiceManager: invalid arguments for service '" +
                        self.name + "':\n" + str(ex))

            for j in serverArgs:
                if j.startswith("--" + service + "."):
                    self.args.append(j)



    # private
    def _createServiceProperties(self, service):
        properties = Ice.createProperties()
        communicatorProperties = self._communicator.getProperties()

        if communicatorProperties.getPropertyAsInt(
            "IceBox.InheritProperties") > 0:

            properties = communicatorProperties.clone()
            # Inherit all except Ice.Admin.Endpoints!
            properties.setProperty("Ice.Admin.Endpoints", "")

        programName = communicatorProperties.getProperty("Ice.ProgramName")
        if not programName:
            properties.setProperty("Ice.ProgramName", service)
        else:
            properties.setProperty("Ice.ProgramName", programName +"-"+ service)

        return properties

