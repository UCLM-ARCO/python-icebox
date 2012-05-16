#!/usr/bin/python
# -*- mode: python; coding: utf-8 -*-

import sys
import Ice

Ice.loadSlice("test/Test.ice -I /usr/share/Ice/slice")
import Test


ic = Ice.initialize()
prx = ic.stringToProxy(sys.argv[1])
Test.TestIntfPrx.checkedCast(prx)

