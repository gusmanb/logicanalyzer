##
## This file is part of the libsigrokdecode project.
##
## Copyright (C) 2012 Bert Vermeulen <bert@biot.com>
## Copyright (C) 2012 Uwe Hermann <uwe@hermann-uwe.de>
##
## This program is free software; you can redistribute it and/or modify
## it under the terms of the GNU General Public License as published by
## the Free Software Foundation; either version 3 of the License, or
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

# TODO
# - Accept other slave address forms than decimal numbers?
# - Support for filtering out multiple slave/direction pairs?
# - Support 10bit slave addresses?

import copy
import sigrokdecode as srd

class Decoder(srd.Decoder):
    api_version = 3
    id = 'i2cfilter'
    name = 'I²C filter'
    longname = 'I²C filter'
    desc = 'Filter out addresses/directions in an I²C stream.'
    license = 'gplv3+'
    inputs = ['i2c']
    outputs = ['i2c']
    tags = ['Util']
    options = (
        {'id': 'address', 'desc': 'Slave address to filter (decimal)',
            'default': 0},
        {'id': 'direction', 'desc': 'Direction to filter', 'default': 'both',
            'values': ('read', 'write', 'both')}
    )

    def __init__(self):
        self.reset()

    def reset(self):
        self.seen_packets = []
        self.do_forward = None

    def start(self):
        self.out_python = self.register(srd.OUTPUT_PYTHON, proto_id='i2c')
        if self.options['address'] not in range(0, 127 + 1):
            raise Exception('Invalid slave (must be 0..127).')
        self.want_addrs = []
        if self.options['address']:
            self.want_addrs.append(self.options['address'])
        self.want_dir = {
            'read': 'READ', 'write': 'WRITE',
        }.get(self.options['direction'], None)

    def _need_to_forward(self, slave_addr, direction):
        if self.want_addrs and slave_addr not in self.want_addrs:
            return False
        if self.want_dir and direction != self.want_dir:
            return False
        return True

    # Accumulate observed I2C packets until a STOP or REPEATED START
    # condition is seen. These are conditions where transfers end or
    # where direction potentially changes. Forward all previously
    # accumulated traffic if it passes the slave address and direction
    # filter. This assumes that the slave address as well as the read
    # or write direction was part of the observed traffic. There should
    # be no surprise when incomplete traffic does not match the filter
    # condition.
    def decode(self, ss, es, data):

        # Unconditionally accumulate every lower layer packet we see.
        # Keep deep copies for later, only reference caller's values
        # as long as this .decode() invocation executes.
        self.seen_packets.append([ss, es, copy.deepcopy(data)])
        cmd, _ = data

        # Check the slave address and transfer direction early when
        # we see them. Keep accumulating packets while it's already
        # known here whether to forward them. This simplifies other
        # code paths. Including future handling of 10bit addresses.
        if cmd in ('ADDRESS READ', 'ADDRESS WRITE'):
            direction = cmd[len('ADDRESS '):]
            _, slave_addr = data
            self.do_forward = self._need_to_forward(slave_addr, direction)
            return

        # Forward previously accumulated packets as we see their
        # completion, and when they pass the filter condition. Prepare
        # to handle the next transfer (the next read/write part of it).
        if cmd in ('STOP', 'START REPEAT'):
            if self.do_forward:
                for ss, es, data in self.seen_packets:
                    self.put(ss, es, self.out_python, data)
            self.seen_packets.clear()
            self.do_forward = None
            return
