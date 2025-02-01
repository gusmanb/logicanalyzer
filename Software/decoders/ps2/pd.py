##
## This file is part of the libsigrokdecode project.
##
## Copyright (C) 2016 Daniel Schulte <trilader@schroedingers-bit.net>
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
from collections import namedtuple

class Ann:
    BIT, START, STOP, PARITY_OK, PARITY_ERR, DATA, WORD = range(7)

Bit = namedtuple('Bit', 'val ss es')

class Decoder(srd.Decoder):
    api_version = 3
    id = 'ps2'
    name = 'PS/2'
    longname = 'PS/2'
    desc = 'PS/2 keyboard/mouse interface.'
    license = 'gplv2+'
    inputs = ['logic']
    outputs = []
    tags = ['PC']
    channels = (
        {'id': 'clk', 'name': 'Clock', 'desc': 'Clock line'},
        {'id': 'data', 'name': 'Data', 'desc': 'Data line'},
    )
    annotations = (
        ('bit', 'Bit'),
        ('start-bit', 'Start bit'),
        ('stop-bit', 'Stop bit'),
        ('parity-ok', 'Parity OK bit'),
        ('parity-err', 'Parity error bit'),
        ('data-bit', 'Data bit'),
        ('word', 'Word'),
    )
    annotation_rows = (
        ('bits', 'Bits', (0,)),
        ('fields', 'Fields', (1, 2, 3, 4, 5, 6)),
    )

    def __init__(self):
        self.reset()

    def reset(self):
        self.bits = []
        self.bitcount = 0

    def start(self):
        self.out_ann = self.register(srd.OUTPUT_ANN)

    def putb(self, bit, ann_idx):
        b = self.bits[bit]
        self.put(b.ss, b.es, self.out_ann, [ann_idx, [str(b.val)]])

    def putx(self, bit, ann):
        self.put(self.bits[bit].ss, self.bits[bit].es, self.out_ann, ann)

    def handle_bits(self, datapin):
        # Ignore non start condition bits (useful during keyboard init).
        if self.bitcount == 0 and datapin == 1:
            return

        # Store individual bits and their start/end samplenumbers.
        self.bits.append(Bit(datapin, self.samplenum, self.samplenum))

        # Fix up end sample numbers of the bits.
        if self.bitcount > 0:
            b = self.bits[self.bitcount - 1]
            self.bits[self.bitcount - 1] = Bit(b.val, b.ss, self.samplenum)
        if self.bitcount == 11:
            self.bitwidth = self.bits[1].es - self.bits[2].es
            b = self.bits[-1]
            self.bits[-1] = Bit(b.val, b.ss, b.es + self.bitwidth)

        # Find all 11 bits. Start + 8 data + odd parity + stop.
        if self.bitcount < 11:
            self.bitcount += 1
            return

        # Extract data word.
        word = 0
        for i in range(8):
            word |= (self.bits[i + 1].val << i)

        # Calculate parity.
        parity_ok = (bin(word).count('1') + self.bits[9].val) % 2 == 1

        # Emit annotations.
        for i in range(11):
            self.putb(i, Ann.BIT)
        self.putx(0, [Ann.START, ['Start bit', 'Start', 'S']])
        self.put(self.bits[1].ss, self.bits[8].es, self.out_ann, [Ann.WORD,
                 ['Data: %02x' % word, 'D: %02x' % word, '%02x' % word]])
        if parity_ok:
            self.putx(9, [Ann.PARITY_OK, ['Parity OK', 'Par OK', 'P']])
        else:
            self.putx(9, [Ann.PARITY_ERR, ['Parity error', 'Par err', 'PE']])
        self.putx(10, [Ann.STOP, ['Stop bit', 'Stop', 'St', 'T']])

        self.bits, self.bitcount = [], 0

    def decode(self):
        while True:
            # Sample data bits on the falling clock edge (assume the device
            # is the transmitter). Expect the data byte transmission to end
            # at the rising clock edge. Cope with the absence of host activity.
            _, data_pin = self.wait({0: 'f'})
            self.handle_bits(data_pin)
            if self.bitcount == 1 + 8 + 1 + 1:
                _, data_pin = self.wait({0: 'r'})
                self.handle_bits(data_pin)
