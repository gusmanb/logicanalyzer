##
## This file is part of the libsigrokdecode project.
##
## Copyright (C) 2019 Uli Huber
## Copyright (C) 2020 Soeren Apel
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

ann_bit, ann_stat_bit, ann_type, ann_command, ann_parameter, ann_parity, ann_pos, ann_status, ann_warning = range(9)
frame_type_none, frame_type_command, frame_type_16bit_pos, frame_type_18bit_pos = range(4)

class Decoder(srd.Decoder):
    api_version = 3
    id = 'xy2-100'
    name = 'XY2-100'
    longname = 'XY2-100(E) and XY-200(E) galvanometer protocol'
    desc = 'Serial protocol for galvanometer positioning in laser systems'
    license = 'gplv2+'
    inputs = ['logic']
    outputs = []

    tags = ['Embedded/industrial']

    channels = (
        {'id': 'clk', 'name': 'CLK', 'desc': 'Clock'},
        {'id': 'sync', 'name': 'SYNC', 'desc': 'Sync'},
        {'id': 'data', 'name': 'DATA', 'desc': 'X, Y or Z axis data'},
    )
    optional_channels = (
        {'id': 'status', 'name': 'STAT', 'desc': 'X, Y or Z axis status'},
    )

    annotations = (
        ('bit', 'Data Bit'),
        ('stat_bit', 'Status Bit'),
        ('type', 'Frame Type'),
        ('command', 'Command'),
        ('parameter', 'Parameter'),
        ('parity', 'Parity'),
        ('position', 'Position'),
        ('status', 'Status'),
        ('warning', 'Human-readable warnings'),
    )
    annotation_rows = (
        ('bits', 'Data Bits', (ann_bit,)),
        ('stat_bits', 'Status Bits', (ann_stat_bit,)),
        ('data', 'Data', (ann_type, ann_command, ann_parameter, ann_parity)),
        ('positions', 'Positions', (ann_pos,)),
        ('statuses', 'Statuses', (ann_status,)),
        ('warnings', 'Warnings', (ann_warning,)),
    )

    def __init__(self):
        self.samplerate = None
        self.reset()

    def reset(self):
        self.bits = []
        self.stat_bits = []
        self.stat_skip_bit = True

    def metadata(self, key, value):
        if key == srd.SRD_CONF_SAMPLERATE:
            self.samplerate = value

    def start(self):
        self.out_ann = self.register(srd.OUTPUT_ANN)

    def put_ann(self, ss, es, ann_class, value):
        self.put(ss, es, self.out_ann, [ann_class, value])

    def process_bit(self, sync, bit_ss, bit_es, bit_value):
        self.put_ann(bit_ss, bit_es, ann_bit, ['%d' % bit_value])
        self.bits.append((bit_ss, bit_es, bit_value))

        if sync == 0:
            if len(self.bits) < 20:
                self.put_ann(self.bits[0][0], bit_es, ann_warning, ['Not enough data bits'])
                self.reset()
                return

            # Bit structure:
            # 0 1 2 3 4 5 6 7 8 9 10 11 12 13 14 15 16 17 18 19
            # T --------------- 18-bit pos ----------------- PARITY    or
            # -TYPE-- ------------ 16-bit pos -------------- PARITY    or
            # -TYPE-- -8-bit command -8-bit parameter value- PARITY

            # Calculate parity, excluding the parity bit itself
            parity = 0
            for ss, es, value in self.bits[:-1]:
                parity ^= value

            par_ss, par_es, par_value = self.bits[19]
            parity_even = 0
            parity_odd = 0
            if (par_value == parity):
                parity_even = 1
            else:
                parity_odd = 1

            type_1_value = self.bits[0][2]
            type_3_value = (self.bits[0][2] << 2) | (self.bits[1][2] << 1) | self.bits[2][2]

            # Determine frame type
            type = frame_type_none
            parity_status = ['X', 'Unknown']
            type_ss = self.bits[0][0]
            type_es = self.bits[2][1]

            ### 18-bit position
            if (type_1_value == 1) and (parity_odd == 1):
                type = frame_type_18bit_pos
                type_es = self.bits[0][1]
                self.put_ann(self.bits[0][0], bit_es, ann_warning, ['Careful: 18-bit position frames with wrong parity and command frames with wrong parity cannot be identified'])
            ### 16-bit position
            elif (type_3_value == 1):
                type = frame_type_16bit_pos
                if (parity_even == 1):
                    parity_status = ['OK']
                else:
                    parity_status = ['NOK']
                    self.put_ann(self.bits[0][0], bit_es, ann_warning, ['Parity error', 'PE'])
            ### Command
            elif (type_3_value == 7) and (parity_even == 1):
                type = frame_type_command
                self.put_ann(self.bits[0][0], bit_es, ann_warning, ['Careful: 18-bit position frames with wrong parity and command frames with wrong parity cannot be identified'])
            ### Other
            else:
                self.put_ann(self.bits[0][0], bit_es, ann_warning, ['Error', 'Unknown command or parity error'])
                self.reset()
                return

            # Output command and parity annotations
            if (type == frame_type_16bit_pos):
                self.put_ann(type_ss, type_es, ann_type, ['16 bit Position Frame', '16 bit Pos', 'Pos', 'P'])
            if (type == frame_type_18bit_pos):
                self.put_ann(type_ss, type_es, ann_type, ['18 bit Position Frame', '18 bit Pos', 'Pos', 'P'])
            if (type == frame_type_command):
                self.put_ann(type_ss, type_es, ann_type, ['Command Frame', 'Command', 'C'])

            self.put_ann(par_ss, par_es, ann_parity, parity_status)

            # Output value
            if (type == frame_type_16bit_pos) or (type == frame_type_18bit_pos):
               pos = 0

               if (type == frame_type_16bit_pos):
                   count = 15
                   for ss, es, value in self.bits[3:19]:
                       pos |= value << count
                       count -= 1
                   pos = pos if pos < 32768 else pos - 65536
               else:
                   count = 17
                   for ss, es, value in self.bits[3:19]:
                       pos |= value << count
                       count -= 1
                   pos = pos if pos < 131072 else pos - 262144

               self.put_ann(type_es, par_ss, ann_pos, ['%d' % pos])

            if (type == frame_type_command):
               count = 7
               cmd = 0
               cmd_es = 0
               for ss, es, value in self.bits[3:11]:
                   cmd |= value << count
                   count -= 1
                   cmd_es = es
               self.put_ann(type_es, cmd_es, ann_command, ['Command 0x%X' % cmd, 'Cmd 0x%X' % cmd, '0x%X' % cmd])

               count = 7
               param = 0
               for ss, es, value in self.bits[11:19]:
                   param |= value << count
                   count -= 1
               self.put_ann(cmd_es, par_ss, ann_parameter, ['Parameter 0x%X / %d' % (param, param), '0x%X / %d' % (param, param),'0x%X' % param])

            self.reset()

    def process_stat_bit(self, sync, bit_ss, bit_es, bit_value):
        if self.stat_skip_bit:
            self.stat_skip_bit = False
            return

        self.put_ann(bit_ss, bit_es, ann_stat_bit, ['%d' % bit_value])
        self.stat_bits.append((bit_ss, bit_es, bit_value))

        if (sync == 0) and (len(self.stat_bits) == 19):
            stat_ss = self.stat_bits[0][0]
            stat_es = self.stat_bits[18][1]

            status = 0
            count = 18
            for ss, es, value in self.stat_bits:
                status |= value << count
                count -= 1
            self.put_ann(stat_ss, stat_es, ann_status, ['Status 0x%X' % status, '0x%X' % status])

    def decode(self):
        bit_ss = None
        bit_es = None
        bit_value = 0
        stat_ss = None
        stat_es = None
        stat_value = 0
        sync_value = 0
        has_stat = self.has_channel(3)

        while True:
            # Wait for any edge on clk
            clk, sync, data, stat = self.wait({0: 'e'})

            if clk == 1:
                stat_value = stat

                bit_es = self.samplenum
                if bit_ss:
                    self.process_bit(sync_value, bit_ss, bit_es, bit_value)
                bit_ss = self.samplenum
            else:
                bit_value = data
                sync_value = sync

                stat_es = self.samplenum
                if stat_ss and has_stat:
                    self.process_stat_bit(sync_value, stat_ss, stat_es, stat_value)
                stat_ss = self.samplenum
