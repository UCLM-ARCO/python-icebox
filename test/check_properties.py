#!/usr/bin/python
# -*- mode: python; coding: utf-8 -*-

import sys
import Ice
Ice.loadSlice("test/Test.ice -I /usr/share/Ice/slice")
import Test


ic = Ice.initialize()
prx1 = Test.TestIntfPrx.checkedCast(ic.stringToProxy(sys.argv[1]))
prx2 = Test.TestIntfPrx.checkedCast(ic.stringToProxy(sys.argv[2]))

assert prx1.getProperty("Service1.UniqueProperty") is "1"
assert prx2.getProperty("Service1.UniqueProperty") is "1"

