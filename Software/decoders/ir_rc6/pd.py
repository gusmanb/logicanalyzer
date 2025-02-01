##
## This file is part of the libsigrokdecode project.
##
## Copyright (C) 2019 Benedikt Otto <benedikt_o@web.de>
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

class SamplerateError(Exception):
    pass

class Decoder(srd.Decoder):
    api_version = 3
    id = 'ir_rc6'
    name = 'IR RC-6'
    longname = 'IR RC-6'
    desc = 'RC-6 infrared remote control protocol.'
    license = 'gplv2+'
    inputs = ['logic']
    outputs = []
    tags = ['IR']
    channels = (
        {'id': 'ir', 'name': 'IR', 'desc': 'IR data line'},
    )
    options = (
        {'id': 'polarity', 'desc': 'Polarity', 'default': 'auto',
            'values': ('auto', 'active-low', 'active-high')},
    )
    annotations = (
        ('bit', 'Bit'),
        ('sync', 'Sync'),
        ('startbit', 'Startbit'),
        ('field', 'Field'),
        ('togglebit', 'Togglebit'),
        ('address', 'Address'),
        ('command', 'Command'),
    )
    annotation_rows = (
        ('bits', 'Bits', (0,)),
        ('fields', 'Fields', (1, 2, 3, 4, 5, 6)),
    )

    def __init__(self):
        self.reset()

    def reset(self):
        self.samplerate = None
        self.edges, self.deltas, self.bits = [], [], []
        self.state = 'IDLE'
        self.mode = 0

    def start(self):
        self.out_ann = self.register(srd.OUTPUT_ANN)

    def metadata(self, key, value):
        if key == srd.SRD_CONF_SAMPLERATE:
            self.samplerate = value
            # One bit: 0.889ms (one half low, one half high).
            self.halfbit = int((self.samplerate * 0.000889) / 2.0)

    def putb(self, bit, data):
        self.put(bit[0], bit[1], self.out_ann, data)

    def putbits(self, bit1, bit2, data):
        self.put(bit1[0], bit2[1], self.out_ann, data)

    def putx(self, ss, es, data):
        self.put(ss, es, self.out_ann, data)

    def handle_bit(self):
        if len(self.bits) != 6:
            return
        if self.bits[0][2] == 8 and self.bits[0][3] == 1:
            self.putb(self.bits[0], [1, ['Synchronisation', 'Sync']])
        else:
            return
        if self.bits[1][3] == 1:
            self.putb(self.bits[1], [2, ['Startbit', 'Start']])
        else:
            return
        self.mode = sum([self.bits[2 + i][3] << (2 - i) for i in range(3)])
        self.putbits(self.bits[2], self.bits[4], [3, ['Field: %d' % self.mode]])
        self.putb(self.bits[5], [4, ['Toggle: %d' % self.bits[5][3]]])

    def handle_package(self):
        # Sync and start bits have to be 1.
        if self.bits[0][3] == 0 or self.bits[1][3] == 0:
            return
        if len(self.bits) <= 6:
            return

        if self.mode == 0 and len(self.bits) == 22: # Mode 0 standard
            value = sum([self.bits[6 + i][3] << (7 - i) for i in range(8)])
            self.putbits(self.bits[6], self.bits[13], [5, ['Address: %0.2X' % value]])

            value = sum([self.bits[14 + i][3] << (7 - i) for i in range(8)])
            self.putbits(self.bits[14], self.bits[21], [6, ['Data: %0.2X' % value]])

            self.bits = []

        if self.mode == 6 and len(self.bits) >= 15: # Mode 6
            if self.bits[6][3] == 0: # Short addr, Mode 6A
                value = sum([self.bits[6 + i][3] << (7 - i) for i in range(8)])
                self.putbits(self.bits[6], self.bits[13], [5, ['Address: %0.2X' % value]])

                num_data_bits = len(self.bits) - 14
                value = sum([self.bits[14 + i][3] << (num_data_bits - 1 - i) for i in range(num_data_bits)])
                self.putbits(self.bits[14], self.bits[-1], [6, ['Data: %X' % value]])

                self.bits = []

            elif len(self.bits) >= 23: # Long addr, Mode 6B
                value = sum([self.bits[6 + i][3] << (15 - i) for i in range(16)])
                self.putbits(self.bits[6], self.bits[21], [5, ['Address: %0.2X' % value]])

                num_data_bits = len(self.bits) - 22
                value = sum([self.bits[22 + i][3] << (num_data_bits - 1 - i) for i in range(num_data_bits)])
                self.putbits(self.bits[22], self.bits[-1], [6, ['Data: %X' % value]])

                self.bits = []

    def decode(self):
        if not self.samplerate:
            raise SamplerateError('Cannot decode without samplerate.')
        value = 0
        num_edges = -1
        self.invert = False

        while True:
            conditions = [{0: 'e'}]
            if self.state == 'DATA':
                conditions.append({'skip': self.halfbit * 6})
            (self.ir,) = self.wait(conditions)

            if len(conditions) == 2:
                if self.matched[1]:
                    self.state = 'IDLE'

            self.edges.append(self.samplenum)
            if len(self.edges) < 2:
                continue

            delta = (self.edges[-1] - self.edges[-2]) / self.halfbit
            delta = int(delta + 0.5)
            self.deltas.append(delta)

            if len(self.deltas) < 2:
                continue

            if self.deltas[-2:] == [6, 2]:
                self.state = 'SYNC'
                num_edges = 0
                self.bits = []

                if self.options['polarity'] == 'auto':
                    value = 1
                else:
                    value = self.ir if self.options['polarity'] == 'active-high' else 1 - self.ir

                self.bits.append((self.edges[-3], self.edges[-1], 8, value))
                self.invert = self.ir == 0
                self.putb(self.bits[-1], [0, ['%d' % value]]) # Add bit.

            if (num_edges % 2) == 0: # Only count every second edge.
                if self.deltas[-2] in [1, 2, 3] and self.deltas[-1] in [1, 2, 3, 6]:
                    self.state = 'DATA'
                    if self.deltas[-2] != self.deltas[-1]:
                        # Insert border between 2 bits.
                        self.edges.insert(-1, self.edges[-2] + self.deltas[-2] * self.halfbit)
                        total = self.deltas[-1]
                        self.deltas[-1] = self.deltas[-2]
                        self.deltas.append(total - self.deltas[-1])

                        self.bits.append((self.edges[-4], self.edges[-2], self.deltas[-2] * 2, value))

                        num_edges += 1
                    else:
                        self.bits.append((self.edges[-3], self.edges[-1], self.deltas[-1] * 2, value))

                    self.putb(self.bits[-1], [0, ['%d' % value]]) # Add bit.

            if len(self.bits) > 0:
                self.handle_bit()
                if self.state == 'IDLE':
                    self.handle_package()

            if self.options['polarity'] == 'auto':
                value = self.ir if self.invert else 1 - self.ir
            else:
                value = self.ir if self.options['polarity'] == 'active-low' else 1 - self.ir

            num_edges += 1
