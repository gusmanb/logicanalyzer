##
## This file is part of the libsigrokdecode project.
##
## Copyright (C) 2012 Uwe Hermann <uwe@hermann-uwe.de>
##
## This program is free software; you can redistribute it and/or modify
## it under the terms of the GNU General Public License as published by
## the Free Software Foundation; either version 2 of the License, or
## (at your option) any later version.
##
## This program is distributed in the hope that it will be useful,
## but WITHOUT ANY WARRANTY; without even the implied warranty of
## MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
## GNU General Public License for more details.
##
## You should have received a copy of the GNU General Public License
## along with this program; if not, see <http://www.gnu.org/licenses/>.
##

import sigrokdecode as srd

class Decoder(srd.Decoder):
    api_version = 3
    id = 'i2cdemux'
    name = 'I²C demux'
    longname = 'I²C demultiplexer'
    desc = 'Demux I²C packets into per-slave-address streams.'
    license = 'gplv2+'
    inputs = ['i2c']
    outputs = [] # TODO: Only known at run-time.
    tags = ['Util']

    def __init__(self):
        self.reset()

    def reset(self):
        self.packets = [] # Local cache of I²C packets
        self.slaves = [] # List of known slave addresses
        self.stream = -1 # Current output stream
        self.streamcount = 0 # Number of created output streams

    def start(self):
        self.out_python = []

    # Grab I²C packets into a local cache, until an I²C STOP condition
    # packet comes along. At some point before that STOP condition, there
    # will have been an ADDRESS READ or ADDRESS WRITE which contains the
    # I²C address of the slave that the master wants to talk to.
    # We use this slave address to figure out which output stream should
    # get the whole chunk of packets (from START to STOP).
    def decode(self, ss, es, data):

        cmd, databyte = data

        # Add the I²C packet to our local cache.
        self.packets.append([ss, es, data])

        if cmd in ('ADDRESS READ', 'ADDRESS WRITE'):
            if databyte in self.slaves:
                self.stream = self.slaves.index(databyte)
                return

            # We're never seen this slave, add a new stream.
            self.slaves.append(databyte)
            self.out_python.append(self.register(srd.OUTPUT_PYTHON,
                                   proto_id='i2c-%s' % hex(databyte)))
            self.stream = self.streamcount
            self.streamcount += 1
        elif cmd == 'STOP':
            if self.stream == -1:
                raise Exception('Invalid stream!') # FIXME?

            # Send the whole chunk of I²C packets to the correct stream.
            for p in self.packets:
                self.put(p[0], p[1], self.out_python[self.stream], p[2])

            self.packets = []
            self.stream = -1
        else:
            pass # Do nothing, only add the I²C packet to our cache.
