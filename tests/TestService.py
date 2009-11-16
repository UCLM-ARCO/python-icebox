# -*- mode: python; coding: utf-8 -*-

import Ice
import IceBox

import os
cwd = os.path.dirname(__file__)
Ice.loadSlice("%s/Test.ice -I /usr/share/slice" % cwd)
import Test


class TestIntfI(Test.TestIntf):

    def __init__(self, args):
        self._args = args

    def getProperty(self, name, current):
        props = current.adapter.getCommunicator().getProperties()
        return props.getProperty(name)

    def getArgs(self, current):
        return self._args


class ServiceI(IceBox.Service):

    def start(self, name, communicator, args):

        self._oa = communicator.createObjectAdapter(name + "OA")
        srv = TestIntfI(args)
        oid = communicator.stringToIdentity(name + "Object")
        print "PRX: '" + str(self._oa.add(srv, oid)) + "'"

        self._oa.activate()

    def stop(self):
        self._oa.deactivate()
        self._oa.destroy()

