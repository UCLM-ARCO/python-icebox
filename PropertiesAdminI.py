# -*- mode: python; coding: utf-8 -*-

# Copyright (c) 2009 Arco Labs.
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


import Ice

class PropertiesAdminI(Ice.PropertiesAdmin):

    def __init__(self, properties):
        self._properties = properties

    def getProperty(self, name, current):
        return self._properties.getProperty(name)

    def getPropertiesForPrefix(self, name, current):
        return self._properties.getPropertiesForPrefix(name)

