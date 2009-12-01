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


class TraceLevels:

    def __init__(self, properties):

        self.networkCat = "Network"
        self.protocolCat = "Protocol"
        self.retryCat = "Retry"
        self.locationCat = "Locator"
        self.slicingCat = "Slicing"

        keyBase = "Ice.Trace."

        self.network = properties.getPropertyAsInt(keyBase + self.networkCat)
        self.protocol = properties.getPropertyAsInt(keyBase + self.protocolCat)
        self.retry = properties.getPropertyAsInt(keyBase + self.retryCat)
        self.location = properties.getPropertyAsInt(keyBase + self.locationCat)
        self.slicing = properties.getPropertyAsInt(keyBase + self.slicingCat)
