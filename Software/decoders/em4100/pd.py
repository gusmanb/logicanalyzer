##
## This file is part of the libsigrokdecode project.
##
## Copyright (C) 2015 Benjamin Larsson <benjamin@southpole.se>
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
    id = 'em4100'
    name = 'EM4100'
    longname = 'RFID EM4100'
    desc = 'EM4100 100-150kHz RFID protocol.'
    license = 'gplv2+'
    inputs = ['logic']
    outputs = []
    tags = ['IC', 'RFID']
    channels = (
        {'id': 'data', 'name': 'Data', 'desc': 'Data line'},
    )
    options = (
        {'id': 'polarity', 'desc': 'Polarity', 'default': 'active-high',
            'values': ('active-low', 'active-high')},
        {'id': 'datarate' , 'desc': 'Data rate', 'default': 64,
            'values': (64, 32, 16)},
#        {'id': 'coding', 'desc': 'Bit coding', 'default': 'biphase',
#            'values': ('biphase', 'manchester', 'psk')},
        {'id': 'coilfreq', 'desc': 'Coil frequency', 'default': 125000},
    )
    annotations = (
        ('bit', 'Bit'),
        ('header', 'Header'),
        ('version-customer', 'Version/customer'),
        ('data', 'Data'),
        ('rowparity-ok', 'Row parity OK'),
        ('rowparity-err', 'Row parity error'),
        ('colparity-ok', 'Column parity OK'),
        ('colparity-err', 'Column parity error'),
        ('stopbit', 'Stop bit'),
        ('tag', 'Tag'),
    )
    annotation_rows = (
        ('bits', 'Bits', (0,)),
        ('fields', 'Fields', (1, 2, 3, 4, 5, 6, 7, 8)),
        ('tags', 'Tags', (9,)),
    )

    def __init__(self):
        self.reset()

    def reset(self):
        self.samplerate = None
        self.oldpin = None
        self.last_samplenum = None
        self.lastlast_samplenum = None
        self.last_edge = 0
        self.bit_width = 0
        self.halfbit_limit = 0
        self.oldpp = 0
        self.oldpl = 0
        self.oldsamplenum = 0
        self.last_bit_pos = 0
        self.ss_first = 0
        self.first_one = 0
        self.state = 'HEADER'
        self.data = 0
        self.data_bits = 0
        self.ss_data = 0
        self.data_parity = 0
        self.payload_cnt = 0
        self.data_col_parity = [0, 0, 0, 0, 0, 0]
        self.col_parity = [0, 0, 0, 0, 0, 0]
        self.tag = 0
        self.all_row_parity_ok = True
        self.col_parity_pos = []

    def metadata(self, key, value):
        if key == srd.SRD_CONF_SAMPLERATE:
            self.samplerate = value
        self.bit_width = (self.samplerate / self.options['coilfreq']) * self.options['datarate']
        self.halfbit_limit = self.bit_width/2 + self.bit_width/4
        self.polarity = 0 if self.options['polarity'] == 'active-low' else 1

    def start(self):
        self.out_ann = self.register(srd.OUTPUT_ANN)

    def putbit(self, bit, ss, es):
        self.put(ss, es, self.out_ann, [0, [str(bit)]])
        if self.state == 'HEADER':
            if bit == 1:
                if self.first_one > 0:
                    self.first_one += 1
                if self.first_one == 9:
                    self.put(self.ss_first, es, self.out_ann,
                             [1, ['Header', 'Head', 'He', 'H']])
                    self.first_one = 0
                    self.state = 'PAYLOAD'
                    return
                if self.first_one == 0:
                    self.first_one = 1
                    self.ss_first = ss

            if bit == 0:
                self.first_one = 0
            return

        if self.state == 'PAYLOAD':
            self.payload_cnt += 1
            if self.data_bits == 0:
                self.ss_data = ss
                self.data = 0
                self.data_parity = 0
            self.data_bits += 1
            if self.data_bits == 5:
                s = 'Version/customer' if self.payload_cnt <= 10 else 'Data'
                c = 2 if self.payload_cnt <= 10 else 3
                self.put(self.ss_data, ss, self.out_ann,
                         [c, [s + ': %X' % self.data, '%X' % self.data]])
                s = 'OK' if self.data_parity == bit else 'ERROR'
                c = 4 if s == 'OK' else 5
                if s == 'ERROR':
                    self.all_row_parity_ok = False
                self.put(ss, es, self.out_ann,
                         [c, ['Row parity: ' + s, 'RP: ' + s, 'RP', 'R']])
                self.tag = (self.tag << 4) | self.data
                self.data_bits = 0
                if self.payload_cnt == 50:
                    self.state = 'TRAILER'
                    self.payload_cnt = 0

            self.data_parity ^= bit
            self.data_col_parity[self.data_bits] ^= bit
            self.data = (self.data << 1) | bit
            return

        if self.state == 'TRAILER':
            self.payload_cnt += 1
            if self.data_bits == 0:
                self.ss_data = ss
                self.data = 0
                self.data_parity = 0
            self.data_bits += 1
            self.col_parity[self.data_bits] = bit
            self.col_parity_pos.append([ss, es])

            if self.data_bits == 5:
                self.put(ss, es, self.out_ann, [8, ['Stop bit', 'SB', 'S']])

                for i in range(1, 5):
                    s = 'OK' if self.data_col_parity[i] == \
                                self.col_parity[i] else 'ERROR'
                    c = 6 if s == 'OK' else 7
                    self.put(self.col_parity_pos[i - 1][0],
                             self.col_parity_pos[i - 1][1], self.out_ann,
                             [c, ['Column parity %d: %s' % (i, s),
                                  'CP%d: %s' % (i, s), 'CP%d' % i, 'C']])

                # Emit an annotation for valid-looking tags.
                all_col_parity_ok = (self.data_col_parity[1:5] == self.col_parity[1:5])
                if all_col_parity_ok and self.all_row_parity_ok:
                    self.put(self.ss_first, es, self.out_ann,
                             [9, ['Tag: %010X' % self.tag, 'Tag', 'T']])

                self.tag = 0
                self.data_bits = 0

                if self.payload_cnt == 5:
                    self.state = 'HEADER'
                    self.payload_cnt = 0
                    self.data_col_parity = [0, 0, 0, 0, 0, 0]
                    self.col_parity = [0, 0, 0, 0, 0, 0]
                    self.col_parity_pos = []
                    self.all_row_parity_ok = True

    def manchester_decode(self, pl, pp, pin):
        bit = self.oldpin ^ self.polarity
        if pl > self.halfbit_limit:
            es = int(self.samplenum - pl/2)
            if self.oldpl > self.halfbit_limit:
                ss = int(self.oldsamplenum - self.oldpl/2)
            else:
                ss = int(self.oldsamplenum - self.oldpl)
            self.putbit(bit, ss, es)
            self.last_bit_pos = int(self.samplenum - pl/2)
        else:
            es = int(self.samplenum)
            if self.oldpl > self.halfbit_limit:
                ss = int(self.oldsamplenum - self.oldpl/2)
                self.putbit(bit, ss, es)
                self.last_bit_pos = int(self.samplenum)
            else:
                if self.last_bit_pos <= self.oldsamplenum - self.oldpl:
                    ss = int(self.oldsamplenum - self.oldpl)
                    self.putbit(bit, ss, es)
                    self.last_bit_pos = int(self.samplenum)

    def decode(self):
        if not self.samplerate:
            raise SamplerateError('Cannot decode without samplerate.')

        # Initialize internal state from the very first sample.
        (pin,) = self.wait()
        self.oldpin = pin
        self.last_samplenum = self.samplenum
        self.lastlast_samplenum = self.samplenum
        self.last_edge = self.samplenum
        self.oldpl = 0
        self.oldpp = 0
        self.oldsamplenum = 0
        self.last_bit_pos = 0

        while True:
            # Ignore identical samples, only process edges.
            (pin,) = self.wait({0: 'e'})
            pl = self.samplenum - self.oldsamplenum
            pp = pin
            self.manchester_decode(pl, pp, pin)
            self.oldpl = pl
            self.oldpp = pp
            self.oldsamplenum = self.samplenum
            self.oldpin = pin
