##
## This file is part of the libsigrokdecode project.
##
## Copyright (C) 2015 Paul Evans <leonerd@leonerd.org.uk>
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

def _decode_intensity(val):
    intensity = val & 0x0f
    if intensity == 0:
        return 'min'
    elif intensity == 15:
        return 'max'
    else:
        return intensity

registers = {
    0x00: ['No-op', lambda _: ''],
    0x09: ['Decode', lambda v: '0b{:08b}'.format(v)],
    0x0A: ['Intensity', _decode_intensity],
    0x0B: ['Scan limit', lambda v: 1 + v],
    0x0C: ['Shutdown', lambda v: 'off' if v else 'on'],
    0x0F: ['Display test', lambda v: 'on' if v else 'off']
}

ann_chip, ann_reg, ann_digit, ann_warning = range(4)

class Decoder(srd.Decoder):
    api_version = 3
    id = 'max72xx'
    name = 'MAX72xx'
    longname = 'Maxim MAX7219/MAX7221'
    desc = 'Maxim MAX72xx series 8-digit LED display driver'
    license = 'gplv2+'
    inputs = ['spi']
    outputs = []
    tags = ['Display']
    options = (
        {'id': 'numofdrivers', 'desc': 'Number of daisy-chained chips', 'default': 1},
    )
    annotations = (
        ('chip', 'Index of chip in daisy chain'),
        ('register', 'Registers written to the device'),
        ('digit', 'Digits displayed on the device'),
        ('warning', 'Human-readable warnings'),
    )
    annotation_rows = (
        ('chip_nr', 'Chip number', (ann_chip,)),
        ('commands', 'Commands', (ann_reg, ann_digit)),
        ('warnings', 'Warnings', (ann_warning,)),
    )

    def __init__(self):
        self.reset()

    def reset(self):
        pass

    def start(self):
        self.out_ann = self.register(srd.OUTPUT_ANN)
        self.pos = 0
        self.cs_start = 0
        self.num_of_drivers = self.options['numofdrivers']

    def putchip(self, ss, es, chip):
        self.put(ss, es, self.out_ann, [ann_chip, ['Chip %d' % (chip)]])

    def putreg(self, ss, es, reg, value):
        if value:
            self.put(ss, es, self.out_ann, [ann_reg, ['%s: %s' % (reg, value)]])
        else:
            self.put(ss, es, self.out_ann, [ann_reg, [reg]])

    def putdigit(self, ss, es, digit, value):
        self.put(ss, es, self.out_ann, [ann_digit, ['Digit %d: %02X' % (digit, value)]])

    def putwarn(self, ss, es, message):
        self.put(ss, es, self.out_ann, [ann_warning, [message]])

    def decode(self, ss, es, data):
        ptype, mosi, _ = data

        if ptype == 'DATA':
            if not self.cs_asserted:
                return

            if self.pos <= self.num_of_drivers * 2:
                if self.pos % 2 == 0:
                    self.addr = mosi
                    self.addr_start = ss
                elif self.pos % 2 == 1:
                    if self.num_of_drivers > 1:
                        self.putchip(self.addr_start, es, (self.pos // 2) + 1)
                    if self.addr >= 1 and self.addr <= 8:
                        self.putdigit(self.addr_start, es, self.addr, mosi)
                    elif self.addr in registers:
                        name, decoder = registers[self.addr]
                        self.putreg(self.addr_start, es, name, decoder(mosi))
                    else:
                        self.putwarn(self.addr_start, es,
                            'Unknown register %02X' % (self.addr))

            self.pos += 1
        elif ptype == 'CS-CHANGE':
            self.cs_asserted = mosi
            if self.cs_asserted:
                self.pos = 0
                self.cs_start = ss
            else:
                if self.pos > 0 and self.pos < 2 * self.num_of_drivers:
                    # Don't warn if pos=0 so that CS# glitches don't appear
                    # as spurious warnings.
                    self.putwarn(self.cs_start, es, 'Not enough bits sent for current number of chips')
                elif self.pos > 2 * self.num_of_drivers:
                    self.putwarn(self.cs_start, es, 'Too many bits sent for current number of chips')
