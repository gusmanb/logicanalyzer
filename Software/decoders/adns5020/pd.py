##
## This file is part of the libsigrokdecode project.
##
## Copyright (C) 2015 Karl Palsson <karlp@tweak.net.au>
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

regs = {
    0: 'Product_ID',
    1: 'Revision_ID',
    2: 'Motion',
    3: 'Delta_X',
    4: 'Delta_Y',
    5: 'SQUAL',
    6: 'Shutter_Upper',
    7: 'Shutter_Lower',
    8: 'Maximum_Pixel',
    9: 'Pixel_Sum',
    0xa: 'Minimum_Pixel',
    0xb: 'Pixel_Grab',
    0xd: 'Mouse_Control',
    0x3a: 'Chip_Reset',
    0x3f: 'Inv_Rev_ID',
    0x63: 'Motion_Burst',
}

class Decoder(srd.Decoder):
    api_version = 3
    id = 'adns5020'
    name = 'ADNS-5020'
    longname = 'Avago ADNS-5020'
    desc = 'Bidirectional optical mouse sensor protocol.'
    license = 'gplv2+'
    inputs = ['spi']
    outputs = []
    tags = ['IC', 'PC', 'Sensor']
    annotations = (
        ('read', 'Register read'),
        ('write', 'Register write'),
        ('warning', 'Warning'),
    )
    annotation_rows = (
        ('reads', 'Reads', (0,)),
        ('writes', 'Writes', (1,)),
        ('warnings', 'Warnings', (2,)),
    )

    def __init__(self):
        self.reset()

    def reset(self):
        self.ss_cmd, self.es_cmd = 0, 0
        self.mosi_bytes = []

    def start(self):
        self.out_ann = self.register(srd.OUTPUT_ANN)

    def putx(self, data):
        self.put(self.ss_cmd, self.es_cmd, self.out_ann, data)

    def put_warn(self, pos, msg):
        self.put(pos[0], pos[1], self.out_ann, [2, [msg]])

    def decode(self, ss, es, data):
        ptype = data[0]
        if ptype == 'CS-CHANGE':
            # If we transition high mid-stream, toss out our data and restart.
            cs_old, cs_new = data[1:]
            if cs_old is not None and cs_old == 0 and cs_new == 1:
                if len(self.mosi_bytes) not in [0, 2]:
                    self.put_warn([self.ss_cmd, es], 'Misplaced CS#!')
                    self.mosi_bytes = []
            return

        # Don't care about anything else.
        if ptype != 'DATA':
            return
        mosi, miso = data[1:]

        self.ss, self.es = ss, es

        if len(self.mosi_bytes) == 0:
            self.ss_cmd = ss
        self.mosi_bytes.append(mosi)

        # Writes/reads are mostly two transfers (burst mode is different).
        if len(self.mosi_bytes) != 2:
            return

        self.es_cmd = es
        cmd, arg = self.mosi_bytes
        write = cmd & 0x80
        reg = cmd & 0x7f
        reg_desc = regs.get(reg, 'Reserved %#x' % reg)
        if reg > 0x63:
            reg_desc = 'Unknown'
        if write:
            self.putx([1, ['%s: %#x' % (reg_desc, arg)]])
        else:
            self.putx([0, ['%s: %d' % (reg_desc, arg)]])

        self.mosi_bytes = []
