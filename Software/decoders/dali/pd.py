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
from .lists import *

class SamplerateError(Exception):
    pass

class Decoder(srd.Decoder):
    api_version = 3
    id = 'dali'
    name = 'DALI'
    longname = 'Digital Addressable Lighting Interface'
    desc = 'Digital Addressable Lighting Interface (DALI) protocol.'
    license = 'gplv2+'
    inputs = ['logic']
    outputs = []
    tags = ['Embedded/industrial', 'Lighting']
    channels = (
        {'id': 'dali', 'name': 'DALI', 'desc': 'DALI data line'},
    )
    options = (
        {'id': 'polarity', 'desc': 'Polarity', 'default': 'active-low',
            'values': ('active-low', 'active-high')},
    )
    annotations = (
        ('bit', 'Bit'),
        ('startbit', 'Start bit'),
        ('sbit', 'Select bit'),
        ('ybit', 'Individual or group'),
        ('address', 'Address'),
        ('command', 'Command'),
        ('reply', 'Reply data'),
        ('raw', 'Raw data'),
    )
    annotation_rows = (
        ('bits', 'Bits', (0,)),
        ('raw-data', 'Raw data', (7,)),
        ('fields', 'Fields', (1, 2, 3, 4, 5, 6)),
    )

    def __init__(self):
        self.reset()

    def reset(self):
        self.samplerate = None
        self.edges, self.bits, self.ss_es_bits = [], [], []
        self.state = 'IDLE'
        self.dev_type = None

    def start(self):
        self.out_ann = self.register(srd.OUTPUT_ANN)
        self.old_dali = 1 if self.options['polarity'] == 'active-low' else 0

    def metadata(self, key, value):
        if key == srd.SRD_CONF_SAMPLERATE:
            self.samplerate = value
            # One bit: 833.33us (one half low, one half high).
            # This is how may samples are in 1TE.
            self.halfbit = int((self.samplerate * 0.0008333) / 2.0)

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
        self.putb(0, 0, [7, s])
        # Bits[1:8]
        for i in range(8):
            f |= (b[1 + i][1] << (7 - i))
        if length == 9: # BACKWARD Frame
            s = ['Reply: %02X' % f, 'Rply: %02X' % f,
                 'Rep: %02X' % f, 'R: %02X' % f, 'R']
            self.putb(1, 8, [7, s])
            s = ['Reply: %d' % f, 'Rply: %d' % f,
                 'Rep: %d' % f, 'R: %d' % f, 'R']
            self.putb(1, 8, [6, s])
            return

        # FORWARD FRAME
        # Bits[9:16]: Command/data (MSB-first)
        for i in range(8):
            c |= (b[9 + i][1] << (7 - i))
        # Raw output
        s = ['Raw data: %02X' % f, 'Raw: %02X' % f,
             'Raw: %02X' % f, 'R: %02X' % f, 'R']
        self.putb(1, 8, [7, s])
        s = ['Raw data: %02X' % c, 'Raw: %02X' % c,
                'Raw: %02X' % c, 'R: %02X' % c, 'R']
        self.putb(9, 16, [7, s])

        # Bits[8:8]: Select bit
        # s = ['Selectbit: %d' % b[8][1], 'SEL: %d' % b[8][1], 'SEL', 'SE', 'S']
        if b[8][1] == 1:
            s = ['Command', 'Comd', 'COM', 'CO', 'C']
        else:
            s = ['Arc Power Level', 'Arc Pwr', 'ARC', 'AC', 'A']
        self.putb(8, 8, [1, s])

        # f &= 254 # Clear the select bit.
        if f >= 254: # BROADCAST
            s = ['BROADCAST', 'Brdcast', 'BC', 'B', 'B']
            self.putb(1, 7, [5, s])
        elif f >= 160: # Extended command 0b10100000
            if f == 0xC1: # DALI_ENABLE_DEVICE_TYPE_X
                self.dev_type = -1
            x = extended_commands.get(f, ['Unknown', 'Unk'])
            s = ['Extended Command: %02X (%s)' % (f, x[0]),
                 'XC: %02X (%s)' % (f, x[1]),
                 'XC: %02X' % f, 'X: %02X' % f, 'X']
            self.putb(1, 8, [5, s])
        elif f >= 128: # Group
            # Bits[1:1]: Ybit
            s = ['YBit: %d' % b[1][1], 'YB: %d' % b[1][1], 'YB', 'Y', 'Y']
            self.putb(1, 1, [3, s])
            g = (f & 127) >> 1
            s = ['Group address: %d' % g, 'Group: %d' % g,
                'GP: %d' % g, 'G: %d' % g, 'G']
            self.putb(2,7, [4, s])
        else: # Short address
            # Bits[1:1]: Ybit
            s = ['YBit: %d' % b[1][1], 'YB: %d' % b[1][1], 'YB', 'Y', 'Y']
            self.putb(1, 1, [3, s])
            a = f >> 1
            s = ['Short address: %d' % a, 'Addr: %d' % a,
                'Addr: %d' % a, 'A: %d' % a, 'A']
            self.putb(2, 7, [4, s])

        # Bits[9:16]: Command/data (MSB-first)
        if f >= 160 and f < 254:
            if self.dev_type == -1:
                self.dev_type = c
                s = ['Type: %d' % c, 'Typ: %d' % c,
                     'Typ: %d' % c, 'T: %d' % c, 'D']
            else:
                self.dev_type = None
                s = ['Data: %d' % c, 'Dat: %d' % c,
                     'Dat: %d' % c, 'D: %d' % c, 'D']
        elif b[8][1] == 1:
            un = c & 0xF0
            ln = c & 0x0F
            if un == 0x10: # Set scene command
                x = ['Recall Scene %d' % ln, 'SC %d' % ln]
            elif un == 0x40:
                x = ['Store DTR as Scene %d' % ln, 'SC %d = DTR' % ln]
            elif un == 0x50:
                x = ['Delete Scene %d' % ln, 'DEL SC %d' % ln]
            elif un == 0x60:
                x = ['Add to Group %d' % ln, 'Grp %d Add' % ln]
            elif un == 0x70:
                x = ['Remove from Group %d' % ln, 'Grp %d Del' % ln]
            elif un == 0xB0:
                x = ['Query Scene %d Level' % ln, 'Sc %d Level' % ln]
            elif c >= 224: # Application specific commands
                if self.dev_type == 8:
                    x = dali_device_type8.get(c, ['Unknown App', 'Unk'])
                else:
                    x = ['Application Specific Command %d' % c, 'App Cmd %d' % c]
            else:
                x = dali_commands.get(c, ['Unknown', 'Unk'])
            s = ['Command: %d (%s)' % (c, x[0]), 'Com: %d (%s)' % (c, x[1]),
                 'Com: %d' % c, 'C: %d' % c, 'C']
        else:
            s = ['Arc Power Level: %d' % c, 'Level: %d' % c,
                 'Lev: %d' % c, 'L: %d' % c, 'L']
        self.putb(9, 16, [5, s])

    def reset_decoder_state(self):
        self.edges, self.bits, self.ss_es_bits = [], [], []
        self.state = 'IDLE'

    def decode(self):
        if not self.samplerate:
            raise SamplerateError('Cannot decode without samplerate.')
        bit = 0
        while True:
            # TODO: Come up with more appropriate self.wait() conditions.
            (dali,) = self.wait()
            if self.options['polarity'] == 'active-high':
                dali ^= 1 # Invert.

            # State machine.
            if self.state == 'IDLE':
                # Wait for any edge (rising or falling).
                if self.old_dali == dali:
                    continue
                self.edges.append(self.samplenum)
                self.state = 'PHASE0'
                self.old_dali = dali
                continue

            if self.old_dali != dali:
                self.edges.append(self.samplenum)
            elif self.samplenum == (self.edges[-1] + int(self.halfbit * 1.5)):
                self.edges.append(self.samplenum - int(self.halfbit * 0.5))
            else:
                continue

            bit = self.old_dali
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

            self.old_dali = dali
