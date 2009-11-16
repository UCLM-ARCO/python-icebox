#!/usr/bin/python
# -*- mode: python; coding; utf-8 -*-

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
import Ice

from ServiceManagerI import ServiceManagerI


class Server(Ice.Application):

    def usage(self):

        print >> sys.stderr, (
            "Usage: IceBox.Server [options] --Ice.Config=<file>\n"
            "Options:\n"
            "-h, --help           Show this message.")


    def main(self, args):

        initData = Ice.InitializationData()
        initData.properties = Ice.createProperties()
        initData.properties.setProperty("Ice.Admin.DelayCreation", "1")

        return Ice.Application.main(self, args, initData=initData)


    def run(self, args):

        for i in args[1:]:
            if i in ["-h", "--help"]:
                self.usage()
                return 0

            elif not i.startswith("--"):
                print >> sys.stderr, "Server: unknown option '%s'" % i

                self.usage()
                return 1

        # Don't move after the adapter activation. This allows
        # applications to wait for the service manager to be
        # reachable before sending a signal to shutdown the
        # IceBox.
        self.shutdownOnInterrupt()

        serviceManagerImpl = ServiceManagerI(self.communicator(), args)
        return serviceManagerImpl.run()


if __name__ == "__main__":
    sys.exit(Server().main(sys.argv))
