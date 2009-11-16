# -*- mode: python; coding: utf-8 -*-

# Copyright (c) 2009 Arco Labs.
# Based on Java version of IceBox, by ZeroC Inc.

# This file is part of IceBoxPy.
#
# IceBoxPy is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# IceBoxPy is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with IceBoxPy.  If not, see <http://www.gnu.org/licenses/>.


import sys
import os

import Ice
cwd = os.path.dirname(__file__)
Ice.loadSlice("%s/Process.ice" % cwd)
del cwd


class ProcessI(Ice.Process):

    def __init__(self, communicator):
        self._communicator = communicator

    def shutdown(self, current):
        self._communicator.shutdown()

    def writeMessage(self, message, fd, current):
        if fd == 1:
            print message
        elif fd == 2:
            print >> sys.stderr, message
