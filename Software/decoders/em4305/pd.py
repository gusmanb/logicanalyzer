##
## This file is part of the libsigrokdecode project.
##
## Copyright (C) 2016 Benjamin Larsson <benjamin@southpole.se>
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
    id = 'em4305'
    name = 'EM4305'
    longname = 'RFID EM4205/EM4305'
    desc = 'EM4205/EM4305 100-150kHz RFID protocol.'
    license = 'gplv2+'
    inputs = ['logic']
    outputs = []
    tags = ['IC', 'RFID']
    channels = (
        {'id': 'data', 'name': 'Data', 'desc': 'Data line'},
    )
    options = (
        {'id': 'coilfreq', 'desc': 'Coil frequency', 'default': 125000},
        {'id': 'first_field_stop', 'desc': 'First field stop min', 'default': 40},
        {'id': 'w_gap', 'desc': 'Write gap min', 'default': 12},
        {'id': 'w_one_max', 'desc': 'Write one max', 'default': 32},
        {'id': 'w_zero_on_min', 'desc': 'Write zero on min', 'default': 15},
        {'id': 'w_zero_off_max', 'desc': 'Write zero off max', 'default': 27},
        {'id': 'em4100_decode', 'desc': 'EM4100 decode', 'default': 'on',
            'values': ('on', 'off')},
    )
    annotations = (
        ('bit_value', 'Bit value'),
        ('first_field_stop', 'First field stop'),
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
        self.state = 'FFS_SEARCH'
        self.bits_pos = [[0 for col in range(3)] for row in range(70)]
        self.br_string = ['RF/8', 'RF/16', 'Unused', 'RF/32', 'RF/40',
                          'Unused', 'Unused', 'RF/64',]
        self.encoder = ['not used', 'Manchester', 'Bi-phase', 'not used']
        self.delayed_on = ['No delay', 'Delayed on - BP/8', 'Delayed on - BP/4', 'No delay']
        self.em4100_decode1_partial = 0
        self.cmds = ['Invalid', 'Login', 'Write word', 'Invalid', 'Read word', 'Disable', 'Protect', 'Invalid']

    def metadata(self, key, value):
        if key == srd.SRD_CONF_SAMPLERATE:
            self.samplerate = value
        self.field_clock = self.samplerate / self.options['coilfreq']
        self.wzmax = self.options['w_zero_off_max'] * self.field_clock
        self.wzmin = self.options['w_zero_on_min'] * self.field_clock
        self.womax = self.options['w_one_max'] * self.field_clock
        self.ffs = self.options['first_field_stop'] * self.field_clock
        self.writegap = self.options['w_gap'] * self.field_clock
        self.nogap = 300 * self.field_clock

    def start(self):
        self.out_ann = self.register(srd.OUTPUT_ANN)

    def decode_config(self, idx):
        bitrate = self.get_3_bits(idx+2)
        self.put(self.bits_pos[idx][1], self.bits_pos[idx+5][2],
                 self.out_ann, [10, ['Data rate: ' + \
                 self.br_string[bitrate], self.br_string[bitrate]]])
        encoding = self.bits_pos[idx+6][0]<<0 | self.bits_pos[idx+7][0]<<1
        self.put(self.bits_pos[idx+6][1], self.bits_pos[idx+10][2],
                 self.out_ann, [10, ['Encoder: ' + \
                 self.encoder[encoding], self.encoder[encoding]]])
        self.put(self.bits_pos[idx+11][1], self.bits_pos[idx+12][2], self.out_ann,
                 [10, ['Zero bits', 'ZB']])
        delay_on = self.bits_pos[idx+13][0]<<0 | self.bits_pos[idx+14][0]<<1
        self.put(self.bits_pos[idx+13][1], self.bits_pos[idx+14][2],
                 self.out_ann, [10, ['Delayed on: ' + \
                 self.delayed_on[delay_on], self.delayed_on[delay_on]]])
        lwr = self.bits_pos[idx+15][0]<<3 | self.bits_pos[idx+16][0]<<2 | \
                 self.bits_pos[idx+18][0]<<1 | self.bits_pos[idx+19][0]<<0
        self.put(self.bits_pos[idx+15][1], self.bits_pos[idx+19][2],
                 self.out_ann, [10, ['Last default read word: %d' % lwr, 'LWR: %d' % lwr, '%d' % lwr]])
        self.put(self.bits_pos[idx+20][1], self.bits_pos[idx+20][2],
                 self.out_ann, [10, ['Read login: %d' % self.bits_pos[idx+20][0], '%d' % self.bits_pos[idx+20][0]]])
        self.put(self.bits_pos[idx+21][1], self.bits_pos[idx+21][2], self.out_ann,
                 [10, ['Zero bits', 'ZB']])
        self.put(self.bits_pos[idx+22][1], self.bits_pos[idx+22][2],
                 self.out_ann, [10, ['Write login: %d' % self.bits_pos[idx+22][0], '%d' % self.bits_pos[idx+22][0]]])
        self.put(self.bits_pos[idx+23][1], self.bits_pos[idx+24][2], self.out_ann,
                 [10, ['Zero bits', 'ZB']])
        self.put(self.bits_pos[idx+25][1], self.bits_pos[idx+25][2],
                 self.out_ann, [10, ['Disable: %d' % self.bits_pos[idx+25][0], '%d' % self.bits_pos[idx+25][0]]])
        self.put(self.bits_pos[idx+27][1], self.bits_pos[idx+27][2],
                 self.out_ann, [10, ['Reader talk first: %d' % self.bits_pos[idx+27][0], 'RTF: %d' % self.bits_pos[idx+27][0]]])
        self.put(self.bits_pos[idx+28][1], self.bits_pos[idx+28][2], self.out_ann,
                 [10, ['Zero bits', 'ZB']])
        self.put(self.bits_pos[idx+29][1], self.bits_pos[idx+29][2],
                 self.out_ann, [10, ['Pigeon mode: %d' % self.bits_pos[idx+29][0], '%d' % self.bits_pos[idx+29][0]]])
        self.put(self.bits_pos[idx+30][1], self.bits_pos[idx+34][2],
                 self.out_ann, [10, ['Reserved', 'Res', 'R']])

    def put4bits(self, idx):
        bits = self.bits_pos[idx][0]<<3 | self.bits_pos[idx+1][0]<<2 | \
               self.bits_pos[idx+2][0]<<1 | self.bits_pos[idx+3][0]
        self.put(self.bits_pos[idx][1], self.bits_pos[idx+3][2], self.out_ann,
                 [10, ['%X' % bits]])

    def em4100_decode1(self, idx):
        self.put(self.bits_pos[idx][1], self.bits_pos[idx+9][2], self.out_ann,
                 [10, ['EM4100 header', 'EM header', 'Header', 'H']])
        self.put4bits(idx+10)
        bits = self.bits_pos[idx+15][0]<<3 | self.bits_pos[idx+16][0]<<2 | \
               self.bits_pos[idx+18][0]<<1 | self.bits_pos[idx+19][0]<<0
        self.put(self.bits_pos[idx+15][1], self.bits_pos[idx+19][2], self.out_ann,
               [10, ['%X' % bits]])
        self.put4bits(idx+21)
        self.put4bits(idx+27)
        self.em4100_decode1_partial = self.bits_pos[idx+32][0]<<3 | \
            self.bits_pos[idx+33][0]<<2 | self.bits_pos[idx+34][0]<<1
        self.put(self.bits_pos[idx+32][1], self.bits_pos[idx+34][2],
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
        bits = self.bits_pos[idx+7][0]<<3 | self.bits_pos[idx+9][0]<<2 | \
               self.bits_pos[idx+10][0]<<1 | self.bits_pos[idx+11][0]<<0
        self.put(self.bits_pos[idx+7][1], self.bits_pos[idx+11][2], self.out_ann,
               [10, ['%X' % bits]])
        self.put4bits(idx+13)
        self.put4bits(idx+19)
        bits = self.bits_pos[idx+24][0]<<3 | self.bits_pos[idx+25][0]<<2 | \
               self.bits_pos[idx+27][0]<<1 | self.bits_pos[idx+28][0]<<0
        self.put(self.bits_pos[idx+24][1], self.bits_pos[idx+28][2], self.out_ann,
               [10, ['%X' % bits]])
        self.put(self.bits_pos[idx+30][1], self.bits_pos[idx+34][2],
                 self.out_ann, [10, ['EM4100 trailer']])

    def get_32_bits(self, idx):
        return self.get_8_bits(idx+27)<<24 | self.get_8_bits(idx+18)<<16 | \
               self.get_8_bits(idx+9)<<8 | self.get_8_bits(idx)

    def get_8_bits(self, idx):
        retval = 0
        for i in range(0, 8):
            retval <<= 1
            retval |= self.bits_pos[i+idx][0]
        return retval

    def get_3_bits(self, idx):
        return self.bits_pos[idx][0]<<2 | self.bits_pos[idx+1][0]<<1 | \
               self.bits_pos[idx+2][0]

    def get_4_bits(self, idx):
        return self.bits_pos[idx][0]<<0 | self.bits_pos[idx+1][0]<<1 | \
               self.bits_pos[idx+2][0]<<2 | self.bits_pos[idx+3][0]<<3

    def print_row_parity(self, idx, length):
        parity = 0
        for i in range(0, length):
            parity += self.bits_pos[i+idx][0]
        parity = parity & 0x1
        if parity == self.bits_pos[idx+length][0]:
            self.put(self.bits_pos[idx+length][1], self.bits_pos[idx+length][2], self.out_ann,
                [5, ['Row parity OK', 'Parity OK', 'OK']])
        else:
            self.put(self.bits_pos[idx+length][1], self.bits_pos[idx+length][2], self.out_ann,
                [5, ['Row parity failed', 'Parity failed', 'Fail']])

    def print_col_parity(self, idx):
        data_1 = self.get_8_bits(idx)
        data_2 = self.get_8_bits(idx+9)
        data_3 = self.get_8_bits(idx+9+9)
        data_4 = self.get_8_bits(idx+9+9+9)
        col_par = self.get_8_bits(idx+9+9+9+9)
        col_par_calc = data_1^data_2^data_3^data_4

        if col_par == col_par_calc:
            self.put(self.bits_pos[idx+9+9+9+9][1], self.bits_pos[idx+9+9+9+9+7][2], self.out_ann,
                [5, ['Column parity OK', 'Parity OK', 'OK']])
        else:
            self.put(self.bits_pos[idx+9+9+9+9][1], self.bits_pos[idx+9+9+9+9+7][2], self.out_ann,
                [5, ['Column parity failed', 'Parity failed', 'Fail']])

    def print_8bit_data(self, idx):
        data = self.get_8_bits(idx)
        self.put(self.bits_pos[idx][1], self.bits_pos[idx+7][2], self.out_ann,
                     [9, ['Data' + ': %X' % data, '%X' % data]])

    def put_fields(self):
        if self.bit_nr == 50:
            self.put(self.bits_pos[0][1], self.bits_pos[0][2], self.out_ann,
                     [4, ['Logic zero']])
            self.put(self.bits_pos[1][1], self.bits_pos[4][2], self.out_ann,
                     [4, ['Command', 'Cmd', 'C']])
            self.put(self.bits_pos[5][1], self.bits_pos[49][2], self.out_ann,
                     [4, ['Password', 'Passwd', 'Pass', 'P']])
            # Get command.
            cmd = self.get_3_bits(1)
            self.put(self.bits_pos[1][1], self.bits_pos[3][2], self.out_ann,
                     [5, [self.cmds[cmd]]])
            self.print_row_parity(1, 3)

            # Print data.
            self.print_8bit_data(5)
            self.print_row_parity(5, 8)
            self.print_8bit_data(14)
            self.print_row_parity(14, 8)
            self.print_8bit_data(23)
            self.print_row_parity(23, 8)
            self.print_8bit_data(32)
            self.print_row_parity(32, 8)
            self.print_col_parity(5)
            if self.bits_pos[49][0] == 0:
                self.put(self.bits_pos[49][1], self.bits_pos[49][2], self.out_ann,
                         [5, ['Stop bit', 'Stop', 'SB']])
            else:
                self.put(self.bits_pos[49][1], self.bits_pos[49][2], self.out_ann,
                         [5, ['Stop bit error', 'Error']])

            if cmd == 1:
                password = self.get_32_bits(5)
                self.put(self.bits_pos[12][1], self.bits_pos[46][2], self.out_ann,
                     [10, ['Login password: %X' % password]])

        if self.bit_nr == 57:
            self.put(self.bits_pos[0][1], self.bits_pos[0][2], self.out_ann,
                     [4, ['Logic zero', 'LZ']])
            self.put(self.bits_pos[1][1], self.bits_pos[4][2], self.out_ann,
                     [4, ['Command', 'Cmd', 'C']])
            self.put(self.bits_pos[5][1], self.bits_pos[11][2], self.out_ann,
                     [4, ['Address', 'Addr', 'A']])
            self.put(self.bits_pos[12][1], self.bits_pos[56][2], self.out_ann,
                     [4, ['Data', 'Da', 'D']])

            # Get command.
            cmd = self.get_3_bits(1)
            self.put(self.bits_pos[1][1], self.bits_pos[3][2], self.out_ann,
                     [5, [self.cmds[cmd]]])
            self.print_row_parity(1, 3)

            # Get address.
            addr = self.get_4_bits(5)
            self.put(self.bits_pos[5][1], self.bits_pos[8][2], self.out_ann,
                     [9, ['Addr' + ': %d' % addr, '%d' % addr]])
            self.put(self.bits_pos[9][1], self.bits_pos[10][2], self.out_ann,
                     [5, ['Zero bits', 'ZB']])
            self.print_row_parity(5, 6)
            # Print data.
            self.print_8bit_data(12)
            self.print_row_parity(12, 8)
            self.print_8bit_data(21)
            self.print_row_parity(21, 8)
            self.print_8bit_data(30)
            self.print_row_parity(30, 8)
            self.print_8bit_data(39)
            self.print_row_parity(39, 8)
            self.print_col_parity(12)
            if self.bits_pos[56][0] == 0:
                self.put(self.bits_pos[56][1], self.bits_pos[56][2], self.out_ann,
                         [5, ['Stop bit', 'Stop', 'SB']])
            else:
                self.put(self.bits_pos[56][1], self.bits_pos[56][2], self.out_ann,
                         [5, ['Stop bit error', 'Error']])

            if addr == 4:
                self.decode_config(12)

            if addr == 2:
                password = self.get_32_bits(12)
                self.put(self.bits_pos[12][1], self.bits_pos[46][2], self.out_ann,
                     [10, ['Write password: %X' % password]])

            # If we are programming EM4100 data we can decode it halfway.
            if addr == 5 and self.options['em4100_decode'] == 'on':
                self.em4100_decode1(12)
            if addr == 6 and self.options['em4100_decode'] == 'on':
                self.em4100_decode2(12)

        self.bit_nr = 0

    def add_bits_pos(self, bit, ss_bit, es_bit):
        if self.bit_nr < 70:
            self.bits_pos[self.bit_nr][0] = bit
            self.bits_pos[self.bit_nr][1] = ss_bit
            self.bits_pos[self.bit_nr][2] = es_bit
            self.bit_nr += 1

    def decode(self):
        if not self.samplerate:
            raise SamplerateError('Cannot decode without samplerate.')

        # Initialize internal state.
        self.last_samplenum = self.samplenum
        self.oldsamplenum = 0
        self.old_gap_end = 0
        self.gap_detected = 0
        self.bit_nr = 0

        while True:
            # Ignore identical samples, only process edges.
            (pin,) = self.wait({0: 'e'})

            pl = self.samplenum - self.oldsamplenum
            pp = pin
            samples = self.samplenum - self.last_samplenum

            if self.state == 'FFS_DETECTED':
                if pl > self.writegap:
                    self.gap_detected = 1
                if (self.last_samplenum - self.old_gap_end) > self.nogap:
                    self.gap_detected = 0
                    self.state = 'FFS_SEARCH'
                    self.put(self.old_gap_end, self.last_samplenum,
                             self.out_ann, [3, ['Write mode exit']])
                    self.put_fields()

            if self.state == 'FFS_SEARCH':
                if pl > self.ffs:
                    self.gap_detected = 1
                    self.put(self.last_samplenum, self.samplenum,
                             self.out_ann, [1, ['First field stop', 'Field stop', 'FFS']])
                    self.state = 'FFS_DETECTED'

            if self.gap_detected == 1:
                self.gap_detected = 0
                if (self.last_samplenum - self.old_gap_end) > self.wzmin \
                        and (self.last_samplenum - self.old_gap_end) < self.wzmax:
                    self.put(self.old_gap_end, self.samplenum,
                             self.out_ann, [0, ['0']])
                    self.add_bits_pos(0, self.old_gap_end, self.samplenum)
                if (self.last_samplenum - self.old_gap_end) > self.womax \
                        and (self.last_samplenum-self.old_gap_end) < self.nogap:
                    # One or more 1 bits
                    one_bits = (int)((self.last_samplenum - self.old_gap_end) / self.womax)
                    for ox in range(0, one_bits):
                        bs = (int)(self.old_gap_end+ox*self.womax)
                        be = (int)(self.old_gap_end+ox*self.womax + self.womax)
                        self.put(bs, be, self.out_ann, [0, ['1']])
                        self.add_bits_pos(1, bs, be)
                    if (self.samplenum - self.last_samplenum) > self.wzmin \
                            and (self.samplenum - self.last_samplenum) < self.wzmax:
                        bs = (int)(self.old_gap_end+one_bits*self.womax)
                        self.put(bs, self.samplenum, self.out_ann, [0, ['0']])
                        self.add_bits_pos(0, bs, self.samplenum)

                self.old_gap_end = self.samplenum

            if self.state == 'SKIP':
                self.state = 'FFS_SEARCH'

            self.oldsamplenum = self.samplenum
            self.last_samplenum = self.samplenum
