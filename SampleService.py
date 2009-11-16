# -*- mode: python; coding: utf-8 -*-

# Copyright (c) 2009 Arco Labs.

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


import IceBox

print "  -->  1: SampleService module loaded"

# This is a simple service written in Python
class Service(IceBox.Service):

    def __init__(self):
        print "  -->  2: service object constructed"
        self.name = "Unknown"

    def start(self, name, communicator, args):
        self.name = name
        print "  -->  3: service[%s] call to start" % self.name

    def stop(self):
        print "  -->  4: service[%s] call to stop" % self.name

    def __del__(self):
        print "  -->  5: service[%s] object deleted" % self.name

