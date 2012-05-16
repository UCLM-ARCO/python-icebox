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


import sys

import Ice
Ice.loadSlice("{0}/Ice/Process.ice".format(Ice.getSliceDir()))


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
