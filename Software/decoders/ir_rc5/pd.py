##
## This file is part of the libsigrokdecode project.
##
## Copyright (C) 2014 Uwe Hermann <uwe@hermann-uwe.de>
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
from .lists import *

class SamplerateError(Exception):
    pass

class Decoder(srd.Decoder):
    api_version = 3
    id = 'ir_rc5'
    name = 'IR RC-5'
    longname = 'IR RC-5'
    desc = 'RC-5 infrared remote control protocol.'
    license = 'gplv2+'
    inputs = ['logic']
    outputs = []
    tags = ['IR']
    channels = (
        {'id': 'ir', 'name': 'IR', 'desc': 'IR data line'},
    )
    options = (
        {'id': 'polarity', 'desc': 'Polarity', 'default': 'active-low',
            'values': ('active-low', 'active-high')},
        {'id': 'protocol', 'desc': 'Protocol type', 'default': 'standard',
            'values': ('standard', 'extended')},
    )
    annotations = (
        ('bit', 'Bit'),
        ('startbit1', 'Startbit 1'),
        ('startbit2', 'Startbit 2'),
        ('togglebit-0', 'Toggle bit 0'),
        ('togglebit-1', 'Toggle bit 1'),
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
        self.edges, self.bits, self.ss_es_bits = [], [], []
        self.state = 'IDLE'

    def start(self):
        self.out_ann = self.register(srd.OUTPUT_ANN)
        self.next_edge = 'l' if self.options['polarity'] == 'active-low' else 'h'

    def metadata(self, key, value):
        if key == srd.SRD_CONF_SAMPLERATE:
            self.samplerate = value
            # One bit: 1.78ms (one half low, one half high).
            self.halfbit = int((self.samplerate * 0.00178) / 2.0)

    def putb(self, bit1, bit2, data):
        ss, es = self.ss_es_bits[bit1][0], self.ss_es_bits[bit2][1]
        self.put(ss, es, self.out_ann, data)

    def handle_bits(self):
        a, c, b = 0, 0, self.bits
        # Individual raw bits.
        for i in range(14):
            if i == 0:
                ss = max(0, self.bits[0][0] - self.halfbit)
            else:
                ss = self.ss_es_bits[i - 1][1]
            es = self.bits[i][0] + self.halfbit
            self.ss_es_bits.append([ss, es])
            self.putb(i, i, [0, ['%d' % self.bits[i][1]]])
        # Bits[0:0]: Startbit 1
        s = ['Startbit1: %d' % b[0][1], 'SB1: %d' % b[0][1], 'SB1', 'S1', 'S']
        self.putb(0, 0, [1, s])
        # Bits[1:1]: Startbit 2
        ann_idx = 2
        s = ['Startbit2: %d' % b[1][1], 'SB2: %d' % b[1][1], 'SB2', 'S2', 'S']
        if self.options['protocol'] == 'extended':
            s = ['CMD[6]#: %d' % b[1][1], 'C6#: %d' % b[1][1], 'C6#', 'C#', 'C']
            ann_idx = 6
        self.putb(1, 1, [ann_idx, s])
        # Bits[2:2]: Toggle bit
        s = ['Togglebit: %d' % b[2][1], 'Toggle: %d' % b[2][1],
             'TB: %d' % b[2][1], 'TB', 'T']
        self.putb(2, 2, [3 if b[2][1] == 0 else 4, s])
        # Bits[3:7]: Address (MSB-first)
        for i in range(5):
            a |= (b[3 + i][1] << (4 - i))
        x = system.get(a, ['Unknown', 'Unk'])
        s = ['Address: %d (%s)' % (a, x[0]), 'Addr: %d (%s)' % (a, x[1]),
             'Addr: %d' % a, 'A: %d' % a, 'A']
        self.putb(3, 7, [5, s])
        # Bits[8:13]: Command (MSB-first)
        for i in range(6):
            c |= (b[8 + i][1] << (5 - i))
        if self.options['protocol'] == 'extended':
            inverted_bit6 = 1 if b[1][1] == 0 else 0
            c |= (inverted_bit6 << 6)
        cmd_type = 'VCR' if x[1] in ('VCR1', 'VCR2') else 'TV'
        x = command[cmd_type].get(c, ['Unknown', 'Unk'])
        s = ['Command: %d (%s)' % (c, x[0]), 'Cmd: %d (%s)' % (c, x[1]),
             'Cmd: %d' % c, 'C: %d' % c, 'C']
        self.putb(8, 13, [6, s])

    def edge_type(self):
        # Categorize according to distance from last edge (short/long).
        distance = self.samplenum - self.edges[-1]
        s, l, margin = self.halfbit, self.halfbit * 2, int(self.halfbit / 2)
        if distance in range(l - margin, l + margin + 1):
            return 'l'
        elif distance in range(s - margin, s + margin + 1):
            return 's'
        else:
            return 'e' # Error, invalid edge distance.

    def reset_decoder_state(self):
        self.edges, self.bits, self.ss_es_bits = [], [], []
        self.state = 'IDLE'

    def decode(self):
        if not self.samplerate:
            raise SamplerateError('Cannot decode without samplerate.')
        while True:

            (self.ir,) = self.wait({0: self.next_edge})

            # State machine.
            if self.state == 'IDLE':
                bit = 1
                self.edges.append(self.samplenum)
                self.bits.append([self.samplenum, bit])
                self.state = 'MID1'
                self.next_edge = 'l' if self.ir else 'h'
                continue
            edge = self.edge_type()
            if edge == 'e':
                self.reset_decoder_state() # Reset state machine upon errors.
                continue
            if self.state == 'MID1':
                self.state = 'START1' if edge == 's' else 'MID0'
                bit = None if edge == 's' else 0
            elif self.state == 'MID0':
                self.state = 'START0' if edge == 's' else 'MID1'
                bit = None if edge == 's' else 1
            elif self.state == 'START1':
                if edge == 's':
                    self.state = 'MID1'
                bit = 1 if edge == 's' else None
            elif self.state == 'START0':
                if edge == 's':
                    self.state = 'MID0'
                bit = 0 if edge == 's' else None

            self.edges.append(self.samplenum)
            if bit is not None:
                self.bits.append([self.samplenum, bit])

            if len(self.bits) == 14:
                self.handle_bits()
                self.reset_decoder_state()

            self.next_edge = 'l' if self.ir else 'h'
