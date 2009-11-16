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


from __future__ import with_statement

# synchronized decorator
def synchronized(fn):
    def _deco(self, *args, **kwargs):
        with self._lock:
            return fn(self, *args, **kwargs)
    return _deco


