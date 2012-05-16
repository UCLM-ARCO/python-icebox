# -*- mode: python; coding: utf-8 -*-

import Ice
import IceBox

import sys
import os
cwd = os.path.dirname(__file__)
Ice.loadSlice("%s/Test.ice -I /usr/share/Ice/slice" % cwd)
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
        self.name = name

        self._oa = communicator.createObjectAdapter(name + "OA")
        srv = TestIntfI(args)
        oid = communicator.stringToIdentity(name + "Object")
        self._oa.add(srv, oid)
        self._oa.activate()

        print self.name + " started"
        sys.stdout.flush()


    def stop(self):
        self._oa.deactivate()
        self._oa.destroy()

        print self.name + " stopped"
        sys.stdout.flush()

