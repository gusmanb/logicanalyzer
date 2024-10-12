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
    id = 't55xx'
    name = 'T55xx'
    longname = 'RFID T55xx'
    desc = 'T55xx 100-150kHz RFID protocol.'
    license = 'gplv2+'
    inputs = ['logic']
    outputs = []
    tags = ['IC', 'RFID']
    channels = (
        {'id': 'data', 'name': 'Data', 'desc': 'Data line'},
    )
    options = (
        {'id': 'coilfreq', 'desc': 'Coil frequency', 'default': 125000},
        {'id': 'start_gap', 'desc': 'Start gap min', 'default': 20},
        {'id': 'w_gap', 'desc': 'Write gap min', 'default': 20},
        {'id': 'w_one_min', 'desc': 'Write one min', 'default': 48},
        {'id': 'w_one_max', 'desc': 'Write one max', 'default': 63},
        {'id': 'w_zero_min', 'desc': 'Write zero min', 'default': 16},
        {'id': 'w_zero_max', 'desc': 'Write zero max', 'default': 31},
        {'id': 'em4100_decode', 'desc': 'EM4100 decode', 'default': 'on',
            'values': ('on', 'off')},
    )
    annotations = (
        ('bit_value', 'Bit value'),
        ('start_gap', 'Start gap'),
        ('write_gap', 'Write gap'),
        ('write_mode_exit', 'Write mode exit'),
        ('bit', 'Bit'),
        ('opcode', 'Opcode'),
        ('lock', 'Lock'),
        ('data', 'Data'),
        ('password', 'Password'),
        ('address', 'Address'),
        ('bitrate', 'Bitrate'),
    )
    annotation_rows = (
        ('bits', 'Bits', (0,)),
        ('structure', 'Structure', (1, 2, 3, 4)),
        ('fields', 'Fields', (5, 6, 7, 8, 9)),
        ('decode', 'Decode', (10,)),
    )

    def __init__(self):
        self.reset()

    def reset(self):
        self.samplerate = None
        self.last_samplenum = None
        self.lastlast_samplenum = None
        self.state = 'START_GAP'
        self.bits_pos = [[0 for col in range(3)] for row in range(70)]
        self.br_string = ['RF/8', 'RF/16', 'RF/32', 'RF/40',
                          'RF/50', 'RF/64', 'RF/100', 'RF/128']
        self.mod_str1 = ['Direct', 'Manchester', 'Biphase', 'Reserved']
        self.mod_str2 = ['Direct', 'PSK1', 'PSK2', 'PSK3', 'FSK1', 'FSK2',
                         'FSK1a', 'FSK2a']
        self.pskcf_str = ['RF/2', 'RF/4', 'RF/8', 'Reserved']
        self.em4100_decode1_partial = 0

    def metadata(self, key, value):
        if key == srd.SRD_CONF_SAMPLERATE:
            self.samplerate = value
        self.field_clock = self.samplerate / self.options['coilfreq']
        self.wzmax = self.options['w_zero_max'] * self.field_clock
        self.wzmin = self.options['w_zero_min'] * self.field_clock
        self.womax = self.options['w_one_max'] * self.field_clock
        self.womin = self.options['w_one_min'] * self.field_clock
        self.startgap = self.options['start_gap'] * self.field_clock
        self.writegap = self.options['w_gap'] * self.field_clock
        self.nogap = 64 * self.field_clock

    def start(self):
        self.out_ann = self.register(srd.OUTPUT_ANN)

    def decode_config(self, idx):
        safer_key = self.bits_pos[idx][0]<<3 | self.bits_pos[idx+1][0]<<2 | \
                    self.bits_pos[idx+2][0]<<1 | self.bits_pos[idx+3][0]
        self.put(self.bits_pos[idx][1], self.bits_pos[idx+3][2], self.out_ann,
                 [10, ['Safer Key' + ': %X' % safer_key,'%X' % safer_key]])
        bitrate = self.bits_pos[idx+11][0]<<2 | self.bits_pos[idx+12][0]<<1 | \
                  self.bits_pos[idx+13][0]
        self.put(self.bits_pos[idx+11][1], self.bits_pos[idx+13][2],
                 self.out_ann, [10, ['Data Bit Rate: ' + \
                 self.br_string[bitrate], self.br_string[bitrate]]])
        modulation1 = self.bits_pos[idx+15][0]<<1 | self.bits_pos[idx+16][0]
        modulation2 = self.bits_pos[idx+17][0]<<2 | \
                      self.bits_pos[idx+18][0]<<1 | self.bits_pos[idx+19][0]
        if modulation1 == 0:
            mod_string = self.mod_str2[modulation2]
        else:
            mod_string = self.mod_str1[modulation1]
        self.put(self.bits_pos[idx+15][1], self.bits_pos[idx+19][2],
                 self.out_ann, [10, ['Modulation: ' + mod_string, mod_string]])
        psk_cf = self.bits_pos[idx+20][0]<<1 | self.bits_pos[idx+21][0]
        self.put(self.bits_pos[idx+20][1], self.bits_pos[idx+21][2],
                 self.out_ann, [10, ['PSK-CF: ' + self.pskcf_str[psk_cf],
                 self.pskcf_str[psk_cf]]])
        self.put(self.bits_pos[idx+22][1], self.bits_pos[idx+22][2],
                 self.out_ann, [10, ['AOR' + ': %d' % \
                 (self.bits_pos[idx+22][0]),'%d' % (self.bits_pos[idx+22][0])]])
        maxblock = self.bits_pos[idx+24][0]<<2 | self.bits_pos[idx+25][0]<<1 | \
                   self.bits_pos[idx+26][0]
        self.put(self.bits_pos[idx+24][1], self.bits_pos[idx+26][2],
                 self.out_ann, [10, ['Max-Block' + ': %d' % maxblock,
                 '%d' % maxblock]])
        self.put(self.bits_pos[idx+27][1], self.bits_pos[idx+27][2],
                 self.out_ann, [10, ['PWD' + ': %d' % \
                 (self.bits_pos[idx+27][0]),'%d' % (self.bits_pos[idx+27][0])]])
        self.put(self.bits_pos[idx+28][1], self.bits_pos[idx+28][2],
                 self.out_ann, [10, ['ST-sequence terminator' + ': %d' % \
                 (self.bits_pos[idx+28][0]),'%d' % (self.bits_pos[idx+28][0])]])
        self.put(self.bits_pos[idx+31][1], self.bits_pos[idx+31][2],
                 self.out_ann, [10, ['POR delay' + ': %d' % \
                 (self.bits_pos[idx+31][0]),'%d' % (self.bits_pos[idx+31][0])]])

    def put4bits(self, idx):
        bits = self.bits_pos[idx][0]<<3 | self.bits_pos[idx+1][0]<<2 | \
               self.bits_pos[idx+2][0]<<1 | self.bits_pos[idx+3][0]
        self.put(self.bits_pos[idx][1], self.bits_pos[idx+3][2], self.out_ann,
                 [10, ['%X' % bits]])

    def em4100_decode1(self, idx):
        self.put(self.bits_pos[idx][1], self.bits_pos[idx+8][2], self.out_ann,
                 [10, ['EM4100 header', 'EM header', 'Header', 'H']])
        self.put4bits(idx+9)
        self.put4bits(idx+14)
        self.put4bits(idx+19)
        self.put4bits(idx+24)
        self.em4100_decode1_partial = self.bits_pos[idx+29][0]<<3 | \
            self.bits_pos[idx+30][0]<<2 | self.bits_pos[idx+31][0]<<1
        self.put(self.bits_pos[idx+29][1], self.bits_pos[idx+31][2],
                 self.out_ann, [10, ['Partial nibble']])

    def em4100_decode2(self, idx):
        if self.em4100_decode1_partial != 0:
            bits = self.em4100_decode1_partial + self.bits_pos[idx][0]
            self.put(self.bits_pos[idx][1], self.bits_pos[idx][2],
                     self.out_ann, [10, ['%X' % bits]])
            self.em4100_decode1_partial = 0
        else:
            self.put(self.bits_pos[idx][1], self.bits_pos[idx][2],
                     self.out_ann, [10, ['Partial nibble']])

        self.put4bits(idx+2)
        self.put4bits(idx+7)
        self.put4bits(idx+12)
        self.put4bits(idx+17)
        self.put4bits(idx+22)
        self.put(self.bits_pos[idx+27][1], self.bits_pos[idx+31][2],
                 self.out_ann, [10, ['EM4100 trailer']])

    def get_32_bits(self, idx):
        retval = 0
        for i in range(0, 32):
            retval <<= 1
            retval |= self.bits_pos[i+idx][0]
        return retval

    def get_3_bits(self, idx):
        retval = self.bits_pos[idx][0]<<2 | self.bits_pos[idx+1][0]<<1 | \
                 self.bits_pos[idx+2][0]
        return retval

    def put_fields(self):
        if (self.bit_nr == 70):
            self.put(self.bits_pos[0][1], self.bits_pos[1][2], self.out_ann,
                     [5, ['Opcode' + ': %d%d' % (self.bits_pos[0][0],
                     self.bits_pos[1][0]), '%d%d' % (self.bits_pos[0][0],
                     self.bits_pos[1][0])]])
            password = self.get_32_bits(2)
            self.put(self.bits_pos[2][1], self.bits_pos[33][2], self.out_ann,
                     [8, ['Password' + ': %X' % password, '%X' % password]])
            self.put(self.bits_pos[34][1], self.bits_pos[34][2], self.out_ann,
                     [6, ['Lock' + ': %X' % self.bits_pos[34][0],
                     '%X' % self.bits_pos[34][0]]])
            data = self.get_32_bits(35)
            self.put(self.bits_pos[35][1], self.bits_pos[66][2], self.out_ann,
                     [7, ['Data' + ': %X' % data, '%X' % data]])
            addr = self.get_3_bits(67)
            self.put(self.bits_pos[67][1], self.bits_pos[69][2], self.out_ann,
                     [9, ['Addr' + ': %X' % addr, '%X' % addr]])
            if addr == 0:
                self.decode_config(35)
            if addr == 7:
                self.put(self.bits_pos[35][1], self.bits_pos[66][2],
                         self.out_ann, [10, ['Password' + ': %X' % data,
                         '%X' % data]])
            # If we are programming EM4100 data we can decode it halfway.
            if addr == 1 and self.options['em4100_decode'] == 'on':
                self.em4100_decode1(35)
            if addr == 2 and self.options['em4100_decode'] == 'on':
                self.em4100_decode2(35)

        if (self.bit_nr == 38):
            self.put(self.bits_pos[0][1], self.bits_pos[1][2], self.out_ann,
                     [5, ['Opcode' + ': %d%d' % (self.bits_pos[0][0],
                     self.bits_pos[1][0]), '%d%d' % (self.bits_pos[0][0],
                     self.bits_pos[1][0])]])
            self.put(self.bits_pos[2][1], self.bits_pos[2][2], self.out_ann,
                     [6, ['Lock' + ': %X' % self.bits_pos[2][0],
                     '%X' % self.bits_pos[2][0]]])
            data = self.get_32_bits(3)
            self.put(self.bits_pos[3][1], self.bits_pos[34][2], self.out_ann,
                     [7, ['Data' + ': %X' % data, '%X' % data]])
            addr = self.get_3_bits(35)
            self.put(self.bits_pos[35][1], self.bits_pos[37][2], self.out_ann,
                     [9, ['Addr' + ': %X' % addr, '%X' % addr]])
            if addr == 0:
                self.decode_config(3)
            if addr == 7:
                self.put(self.bits_pos[3][1], self.bits_pos[34][2],
                         self.out_ann, [10, ['Password' + ': %X' % data,
                         '%X' % data]])
            # If we are programming EM4100 data we can decode it halfway.
            if addr == 1 and self.options['em4100_decode'] == 'on':
                self.em4100_decode1(3)
            if addr == 2 and self.options['em4100_decode'] == 'on':
                self.em4100_decode2(3)

        if (self.bit_nr == 2):
            self.put(self.bits_pos[0][1], self.bits_pos[1][2], self.out_ann,
                     [5, ['Opcode' + ': %d%d' % (self.bits_pos[0][0],
                     self.bits_pos[1][0]), '%d%d' % (self.bits_pos[0][0],
                     self.bits_pos[1][0])]])
        self.bit_nr = 0

    def add_bits_pos(self, bit, bit_start, bit_end):
        if self.bit_nr < 70:
            self.bits_pos[self.bit_nr][0] = bit
            self.bits_pos[self.bit_nr][1] = bit_start
            self.bits_pos[self.bit_nr][2] = bit_end
            self.bit_nr += 1

    def decode(self):
        if not self.samplerate:
            raise SamplerateError('Cannot decode without samplerate.')

        self.last_samplenum = 0
        self.lastlast_samplenum = 0
        self.last_edge = 0
        self.oldpl = 0
        self.oldpp = 0
        self.oldsamplenum = 0
        self.last_bit_pos = 0
        self.old_gap_start = 0
        self.old_gap_end = 0
        self.gap_detected = 0
        self.bit_nr = 0

        while True:
            (pin,) = self.wait({0: 'e'})

            pl = self.samplenum - self.oldsamplenum
            pp = pin
            samples = self.samplenum - self.last_samplenum

            if self.state == 'WRITE_GAP':
                if pl > self.writegap:
                    self.gap_detected = 1
                    self.put(self.last_samplenum, self.samplenum,
                             self.out_ann, [2, ['Write gap']])
                if (self.last_samplenum-self.old_gap_end) > self.nogap:
                    self.gap_detected = 0
                    self.state = 'START_GAP'
                    self.put(self.old_gap_end, self.last_samplenum,
                             self.out_ann, [3, ['Write mode exit']])
                    self.put_fields()

            if self.state == 'START_GAP':
                if pl > self.startgap:
                    self.gap_detected = 1
                    self.put(self.last_samplenum, self.samplenum,
                             self.out_ann, [1, ['Start gap']])
                    self.state = 'WRITE_GAP'

            if self.gap_detected == 1:
                self.gap_detected = 0
                if (self.last_samplenum - self.old_gap_end) > self.wzmin \
                        and (self.last_samplenum - self.old_gap_end) < self.wzmax:
                    self.put(self.old_gap_end, self.last_samplenum,
                             self.out_ann, [0, ['0']])
                    self.put(self.old_gap_end, self.last_samplenum,
                             self.out_ann, [4, ['Bit']])
                    self.add_bits_pos(0, self.old_gap_end,
                                      self.last_samplenum)
                if (self.last_samplenum - self.old_gap_end) > self.womin \
                        and (self.last_samplenum - self.old_gap_end) < self.womax:
                    self.put(self.old_gap_end, self.last_samplenum,
                             self.out_ann, [0, ['1']])
                    self.put(self.old_gap_end, self.last_samplenum,
                             self.out_ann, [4, ['Bit']])
                    self.add_bits_pos(1, self.old_gap_end, self.last_samplenum)

                self.old_gap_start = self.last_samplenum
                self.old_gap_end = self.samplenum

            self.oldpl = pl
            self.oldpp = pp
            self.oldsamplenum = self.samplenum
            self.last_samplenum = self.samplenum
