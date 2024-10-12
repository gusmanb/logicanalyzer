##
## This file is part of the libsigrokdecode project.
##
## Copyright (C) 2018 Stefan Petersen <spe@ciellt.se>
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

import re
import sigrokdecode as srd

registers = {
    0x80: ['WRDS',  0, lambda _: ''],
    0x81: ['STO',   1, lambda _: ''],
    0x82: ['SLEEP', 2, lambda _: ''],
    0x83: ['WRITE', 3, lambda v: '0x%x' % v],
    0x84: ['WREN',  4, lambda _: ''],
    0x85: ['RCL',   5, lambda _: ''],
    0x86: ['READ',  6, lambda v: '0x%x' % v],
    0x87: ['READ',  6, lambda v: '0x%x' % v],
    # 0x86/0x87 are both valid READ commands (bit 0 is "don't care").
}

class Decoder(srd.Decoder):
    api_version = 3
    id = 'x2444m'
    name = 'X2444M/P'
    longname = 'Xicor X2444M/P'
    desc = 'Xicor X2444M/P nonvolatile static RAM protocol.'
    license = 'gplv2+'
    inputs = ['spi']
    outputs = []
    tags = ['IC', 'Memory']
    annotations = (
        ('wrds', 'Write disable'),
        ('sto', 'Store RAM data in EEPROM'),
        ('sleep', 'Enter sleep mode'),
        ('write', 'Write data into RAM'),
        ('wren', 'Write enable'),
        ('rcl', 'Recall EEPROM data into RAM'),
        ('read', 'Data read from RAM'),
    )

    def __init__(self):
        self.reset()

    def reset(self):
        self.cs_start = 0
        self.cs_asserted = False
        self.cmd_digit = 0

    def start(self):
        self.out_ann = self.register(srd.OUTPUT_ANN)

    def putreadwrite(self, ss, es, reg, idx, addr, value):
        self.put(ss, es, self.out_ann,
                 [idx, ['%s: %s => 0x%4.4x' % (reg, addr, value),
                        '%s: %s => 0x%4.4x' % (reg[0], addr, value), reg[0]]])

    def putcmd(self, ss, es, reg, idx):
        self.put(ss, es, self.out_ann, [idx, [reg, reg[0]]])

    def decode(self, ss, es, data):
        ptype, mosi, miso = data

        if ptype == 'DATA':
            if not self.cs_asserted:
                return

            if self.cmd_digit == 0:
                self.addr = mosi
                self.addr_start = ss
            elif self.cmd_digit > 0:
                self.read_value = (self.read_value << 8) + miso
                self.write_value = (self.write_value << 8) + mosi
            self.cmd_digit += 1
        elif ptype == 'CS-CHANGE':
            self.cs_asserted = (miso == 1)
            # When not asserted, CS has just changed from asserted to deasserted.
            if not self.cs_asserted:
                # Only one digit, simple command. Else read/write.
                if self.cmd_digit == 1:
                    name, idx, decoder = registers[self.addr & 0x87]
                    self.putcmd(self.addr_start, es, name, idx)
                elif self.cmd_digit > 1:
                    name, idx, decoder = registers[self.addr & 0x87]
                    if name == 'READ':
                        value = self.read_value
                    elif name == 'WRITE':
                        value = self.write_value
                    else:
                        value = 0
                    self.putreadwrite(self.addr_start, es, name, idx,
                                      decoder((self.addr >> 3) & 0x0f), value)

            if self.cs_asserted:
                self.cs_start = ss
                self.cmd_digit = 0
                self.read_value = 0
                self.write_value = 0
