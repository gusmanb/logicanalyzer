##
## This file is part of the libsigrokdecode project.
##
## Copyright (C) 2015 Jeremy Swanson <jeremy@rakocontrols.com>
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
## along with this program.  If not, see <http://www.gnu.org/licenses/>.
##

import sigrokdecode as srd

class SamplerateError(Exception):
    pass

class Decoder(srd.Decoder):
    api_version = 3
    id = 'dsi'
    name = 'DSI'
    longname = 'Digital Serial Interface'
    desc = 'Digital Serial Interface (DSI) lighting protocol.'
    license = 'gplv2+'
    inputs = ['logic']
    outputs = []
    tags = ['Embedded/industrial', 'Lighting']
    channels = (
        {'id': 'dsi', 'name': 'DSI', 'desc': 'DSI data line'},
    )
    options = (
        {'id': 'polarity', 'desc': 'Polarity', 'default': 'active-high',
            'values': ('active-low', 'active-high')},
    )
    annotations = (
        ('bit', 'Bit'),
        ('startbit', 'Start bit'),
        ('level', 'Dimmer level'),
        ('raw', 'Raw data'),
    )
    annotation_rows = (
        ('bits', 'Bits', (0,)),
        ('raw-vals', 'Raw data', (3,)),
        ('fields', 'Fields', (1, 2)),
    )

    def __init__(self):
        self.reset()

    def reset(self):
        self.samplerate = None
        self.edges, self.bits, self.ss_es_bits = [], [], []
        self.state = 'IDLE'

    def start(self):
        self.out_ann = self.register(srd.OUTPUT_ANN)
        self.old_dsi = 1 if self.options['polarity'] == 'active-low' else 0

    def metadata(self, key, value):
        if key == srd.SRD_CONF_SAMPLERATE:
            self.samplerate = value
            # One bit: 1666.7us (one half low, one half high).
            # This is how many samples are in 1TE.
            self.halfbit = int((self.samplerate * 0.0016667) / 2.0)

    def putb(self, bit1, bit2, data):
        ss, es = self.ss_es_bits[bit1][0], self.ss_es_bits[bit2][1]
        self.put(ss, es, self.out_ann, data)

    def handle_bits(self, length):
        a, c, f, g, b = 0, 0, 0, 0, self.bits
        # Individual raw bits.
        for i in range(length):
            if i == 0:
                ss = max(0, self.bits[0][0])
            else:
                ss = self.ss_es_bits[i - 1][1]
            es = self.bits[i][0] + (self.halfbit * 2)
            self.ss_es_bits.append([ss, es])
            self.putb(i, i, [0, ['%d' % self.bits[i][1]]])
        # Bits[0:0]: Startbit
        s = ['Startbit: %d' % b[0][1], 'ST: %d' % b[0][1], 'ST', 'S', 'S']
        self.putb(0, 0, [1, s])
        self.putb(0, 0, [3, s])
        # Bits[1:8]
        for i in range(8):
            f |= (b[1 + i][1] << (7 - i))
            g = f / 2.55
        if length == 9: # BACKWARD Frame
            s = ['Data: %02X' % f, 'Dat: %02X' % f,
                 'Dat: %02X' % f, 'D: %02X' % f, 'D']
            self.putb(1, 8, [3, s])
            s = ['Level: %d%%' % g, 'Lev: %d%%' % g,
                 'Lev: %d%%' % g, 'L: %d' % g, 'D']
            self.putb(1, 8, [2, s])
            return

    def reset_decoder_state(self):
        self.edges, self.bits, self.ss_es_bits = [], [], []
        self.state = 'IDLE'

    def decode(self):
        if not self.samplerate:
            raise SamplerateError('Cannot decode without samplerate.')
        bit = 0
        while True:
            # TODO: Come up with more appropriate self.wait() conditions.
            (self.dsi,) = self.wait()
            if self.options['polarity'] == 'active-high':
                self.dsi ^= 1 # Invert.

            # State machine.
            if self.state == 'IDLE':
                # Wait for any edge (rising or falling).
                if self.old_dsi == self.dsi:
                    continue
                # Add in the first half of the start bit.
                self.edges.append(self.samplenum - int(self.halfbit))
                self.edges.append(self.samplenum)
                # Start bit is 0->1.
                self.phase0 = self.dsi ^ 1
                self.state = 'PHASE1'
                self.old_dsi = self.dsi
                # Get the next sample point.
                self.old_dsi = self.dsi
                continue

            if self.old_dsi != self.dsi:
                self.edges.append(self.samplenum)
            elif self.samplenum == (self.edges[-1] + int(self.halfbit * 1.5)):
                self.edges.append(self.samplenum - int(self.halfbit * 0.5))
            else:
                continue

            bit = self.old_dsi
            if self.state == 'PHASE0':
                self.phase0 = bit
                self.state = 'PHASE1'
            elif self.state == 'PHASE1':
                if (bit == 1) and (self.phase0 == 1): # Stop bit.
                    if len(self.bits) == 17 or len(self.bits) == 9:
                        # Forward or Backward.
                        self.handle_bits(len(self.bits))
                    self.reset_decoder_state() # Reset upon errors.
                    continue
                else:
                    self.bits.append([self.edges[-3], bit])
                    self.state = 'PHASE0'

            self.old_dsi = self.dsi
