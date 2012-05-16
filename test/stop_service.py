#!/usr/bin/python
# -*- mode: python; coding: utf-8 -*-

import sys
import Ice
import IceBox


ic = Ice.initialize()
prx = ic.stringToProxy(sys.argv[1])
prx = IceBox.ServiceManagerPrx.checkedCast(prx)

prx.stopService("TestService")
