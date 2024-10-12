##
## This file is part of the libsigrokdecode project.
##
## Copyright (C) 2018 Steve R <steversig@virginmedia.com>
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

bitvals = ('0', '1', 'f', 'U')

def decode_bit(edges, pulses_per_bit):
    if pulses_per_bit == 2:
        # Datasheet says long pulse is 3 times short pulse.
        lmin = 1.5 # long min multiplier
        lmax = 5 # long max multiplier
        if (edges[1] >= edges[0] * lmin and edges[1] <= edges[0] * lmax): # 0 -___
            return '0'
        elif (edges[0] >= edges[1] * lmin and edges[0] <= edges[1] * lmax): # 1 ---_
             return '1'
        # No float type for this line encoding
        else:
            return 'U'

    if pulses_per_bit == 4:
        # Datasheet says long pulse is 3 times short pulse.
        lmin = 2 # long min multiplier
        lmax = 5 # long max multiplier
        eqmin = 0.5 # equal min multiplier
        eqmax = 1.5 # equal max multiplier
        if ( # 0 -___-___
            (edges[1] >= edges[0] * lmin and edges[1] <= edges[0] * lmax) and
            (edges[2] >= edges[0] * eqmin and edges[2] <= edges[0] * eqmax) and
            (edges[3] >= edges[0] * lmin and edges[3] <= edges[0] * lmax)):
            return '0'
        elif ( # 1 ---_---_
            (edges[0] >= edges[1] * lmin and edges[0] <= edges[1] * lmax) and
            (edges[0] >= edges[2] * eqmin and edges[0] <= edges[2] * eqmax) and
            (edges[0] >= edges[3] * lmin and edges[0] <= edges[3] * lmax)):
             return '1'
        elif ( # float ---_-___
             (edges[1] >= edges[0] * lmin and edges[1] <= edges[0] * lmax) and
            (edges[2] >= edges[0] * lmin and edges[2] <= edges[0]* lmax) and
            (edges[3] >= edges[0] * eqmin and edges[3] <= edges[0] * eqmax)):
            return 'f'
        else:
            return 'U'

def pinlabels(bit_count, packet_bit_count):
    if packet_bit_count == 12:
        if bit_count <= 6:
            return 'A%i' % (bit_count - 1)
        else:
            return 'A%i/D%i' % (bit_count - 1, 12 - bit_count)

    if packet_bit_count == 24:
        if bit_count <= 20:
            return 'A%i' % (bit_count - 1)
        else:
            return 'D%i' % (bit_count - 21)

def decode_model(model, bits):
    if model == 'maplin_l95ar':
        address = 'Addr' # Address bits A0 to A5
        for i in range(0, 6):
            address += ' %i:' % (i + 1) + ('on' if bits[i][0] == '0' else 'off')
        button = 'Button'
        # Button bits A6/D5 to A11/D0
        if bits[6][0] == '0' and bits[11][0] == '0':
            button += ' A ON/OFF'
        elif bits[7][0] == '0' and bits[11][0] == '0':
            button += ' B ON/OFF'
        elif bits[9][0] == '0' and bits[11][0] == '0':
            button += ' C ON/OFF'
        elif bits[8][0] == '0' and bits[11][0] == '0':
            button += ' D ON/OFF'
        else:
            button += ' Unknown'
        return [address, bits[0][1], bits[5][2], \
                button, bits[6][1], bits[11][2]]

    if model == 'xx1527':
        addr = 0
        addr_valid = 1
        for i in range(0, 20):
            if bits[i][0] != 'U':
                addr += int(bits[i][0]) * 2 ** i
            else:
                addr_valid = 0

        if addr_valid == 1:
            address = 'Address 0x%X %X %X' % (addr & 0xFF, (addr >> 8) & 0xFF, addr >> 16)
        else:
            address = 'Invalid address as not all bits are 0 or 1'

        output  = ' K0 = ' + bits[20][0] + ','
        output += ' K1 = ' + bits[21][0] + ','
        output += ' K2 = ' + bits[22][0] + ','
        output += ' K3 = ' + bits[23][0]
        return [address, bits[0][1], bits[19][2], \
                output, bits[20][1], bits[23][2]]

class Decoder(srd.Decoder):
    api_version = 3
    id = 'rc_encode'
    name = 'RC encode'
    longname = 'Remote control encoder'
    desc = 'PT22x2/HX22x2/SC52x2 and xx1527 remote control encoder protocol.'
    license = 'gplv2+'
    inputs = ['logic']
    outputs = []
    tags = ['IC', 'IR']
    channels = (
        {'id': 'data', 'name': 'Data', 'desc': 'Data line'},
    )
    annotations = (
        ('bit-0', 'Bit 0'),
        ('bit-1', 'Bit 1'),
        ('bit-f', 'Bit f'),
        ('bit-U', 'Bit U'),
        ('bit-sync', 'Bit sync'),
        ('pin', 'Pin'),
        ('code-word-addr', 'Code word address'),
        ('code-word-data', 'Code word data'),
    )
    annotation_rows = (
        ('bits', 'Bits', (0, 1, 2, 3, 4)),
        ('pins', 'Pins', (5,)),
        ('code-words', 'Code words', (6, 7)),
    )
    options = (
        {'id': 'linecoding', 'desc': 'Encoding', 'default': 'SC52x2/HX22x2', 'values': ('SC52x2/HX22x2', 'xx1527')},
        {'id': 'remote', 'desc': 'Remote', 'default': 'none', 'values': ('none', 'maplin_l95ar')},
    )

    def __init__(self):
        self.reset()

    def reset(self):
        self.samplenumber_last = None
        self.pulses = []
        self.bits = []
        self.labels = []
        self.bit_count = 0
        self.ss = None
        self.es = None
        self.state = 'IDLE'

    def start(self):
        self.out_ann = self.register(srd.OUTPUT_ANN)
        self.model = self.options['remote']
        if self.options['linecoding'] == 'xx1527':
            self.pulses_per_bit = 2
            self.packet_bits = 24
            self.model = 'xx1527'
        else:
            self.pulses_per_bit = 4 # Each bit is repeated
            self.packet_bits = 12

    def putx(self, data):
        self.put(self.ss, self.es, self.out_ann, data)

    def decode(self):
        while True:
            pin = self.wait({0: 'e'})
            self.state = 'DECODING'

            if not self.samplenumber_last: # Set counters to start of signal.
                self.samplenumber_last = self.samplenum
                self.ss = self.samplenum
                continue

            if self.bit_count < self.packet_bits: # Decode A0 to A11 / A23.
                self.bit_count += 1
                for i in range(0, self.pulses_per_bit):
                    if i > 0:
                        pin = self.wait({0: 'e'}) # Get next edges if we need more.
                    samples = self.samplenum - self.samplenumber_last
                    self.pulses.append(samples) # Save the pulse width.
                    self.samplenumber_last = self.samplenum
                self.es = self.samplenum
                self.bits.append([decode_bit(self.pulses, self.pulses_per_bit), self.ss,
                                  self.es]) # Save states and times.
                idx = bitvals.index(decode_bit(self.pulses, self.pulses_per_bit))
                self.putx([idx, [decode_bit(self.pulses, self.pulses_per_bit)]]) # Write decoded bit.
                self.putx([5, [pinlabels(self.bit_count, self.packet_bits)]]) # Write pin labels.
                self.pulses = []
                self.ss = self.samplenum
            else:
                if self.model != 'none':
                    self.labels = decode_model(self.model, self.bits)
                    self.put(self.labels[1], self.labels[2], self.out_ann,
                             [6, [self.labels[0]]]) # Write model decode.
                    self.put(self.labels[4], self.labels[5], self.out_ann,
                             [7, [self.labels[3]]]) # Write model decode.
                samples = self.samplenum - self.samplenumber_last
                pin = self.wait({'skip': 8 * samples}) # Wait for end of sync bit.
                self.es = self.samplenum
                self.putx([4, ['Sync']]) # Write sync label.
                self.reset() # Reset and wait for next set of pulses.
                self.state = 'DECODE_TIMEOUT'
            if not self.state == 'DECODE_TIMEOUT':
                self.samplenumber_last = self.samplenum
