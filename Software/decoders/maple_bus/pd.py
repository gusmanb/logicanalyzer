##
## This file is part of the libsigrokdecode project.
##
## Copyright (C) 2017 Marcus Comstedt <marcus@mc.pp.se>
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
from common.srdhelper import SrdIntEnum

Pin = SrdIntEnum.from_str('Pin', 'SDCKA SDCKB')

ann = [
    ['Size', 'L'],
    ['SrcAP', 'S'],
    ['DstAP', 'D'],
    ['Cmd', 'C'],
    ['Data'],
    ['Cksum', 'K'],
]

class Decoder(srd.Decoder):
    api_version = 3
    id = 'maple_bus'
    name = 'Maple bus'
    longname = 'SEGA Maple bus'
    desc = 'Maple bus peripheral protocol for SEGA Dreamcast.'
    license = 'gplv2+'
    inputs = ['logic']
    outputs = []
    tags = ['Retro computing']
    channels = (
        {'id': 'sdcka', 'name': 'SDCKA', 'desc': 'Data/clock line A'},
        {'id': 'sdckb', 'name': 'SDCKB', 'desc': 'Data/clock line B'},
    )
    annotations = (
        ('start', 'Start pattern'),
        ('end', 'End pattern'),
        ('start-with-crc', 'Start pattern with CRC'),
        ('occupancy', 'SDCKB occupancy pattern'),
        ('reset', 'RESET pattern'),
        ('bit', 'Bit'),
        ('size', 'Data size'),
        ('source', 'Source AP'),
        ('dest', 'Destination AP'),
        ('command', 'Command'),
        ('data', 'Data'),
        ('checksum', 'Checksum'),
        ('frame-error', 'Frame error'),
        ('checksum-error', 'Checksum error'),
        ('size-error', 'Size error'),
    )
    annotation_rows = (
        ('bits', 'Bits', (0, 1, 2, 3, 4, 5)),
        ('fields', 'Fields', (6, 7, 8, 9, 10, 11)),
        ('warnings', 'Warnings', (12, 13, 14)),
    )
    binary = (
        ('size', 'Data size'),
        ('source', 'Source AP'),
        ('dest', 'Destination AP'),
        ('command', 'Command code'),
        ('data', 'Data'),
        ('checksum', 'Checksum'),
    )

    def __init__(self):
        self.reset()

    def reset(self):
        pass

    def start(self):
        self.out_ann = self.register(srd.OUTPUT_ANN)
        self.out_binary = self.register(srd.OUTPUT_BINARY)
        self.pending_bit_pos = None

    def putx(self, data):
        self.put(self.ss, self.es, self.out_ann, data)

    def putb(self, data):
        self.put(self.ss, self.es, self.out_binary, data)

    def byte_annotation(self, bintype, d):
        return [bintype + 6,
            ['%s: %02X' % (name, d) for name in ann[bintype]] + ['%02X' % d]]

    def got_start(self):
        self.putx([0, ['Start pattern', 'Start', 'S']])

    def got_end(self):
        self.putx([1, ['End pattern', 'End', 'E']])
        if self.length != self.expected_length + 1:
            self.putx([14, ['Size error', 'L error', 'LE']])

    def got_start_with_crc(self):
        self.putx([2, ['Start pattern with CRC', 'Start CRC', 'SC']])

    def got_occupancy(self):
        self.putx([3, ['SDCKB occupancy pattern', 'Occupancy', 'O']])

    def got_reset(self):
        self.putx([4, ['RESET pattern', 'RESET', 'R']])

    def output_pending_bit(self):
        if self.pending_bit_pos:
            self.put(self.pending_bit_pos, self.pending_bit_pos, self.out_ann, [5, ['Bit: %d' % self.pending_bit, '%d' % self.pending_bit]])

    def got_bit(self, n):
        self.output_pending_bit()
        self.data = self.data * 2 + n
        self.pending_bit = n
        self.pending_bit_pos = self.samplenum

    def got_byte(self):
        self.output_pending_bit()
        bintype = 4
        if self.length < 4:
            if self.length == 0:
                self.expected_length = 4 * (self.data + 1)
            bintype = self.length
        elif self.length == self.expected_length:
            bintype = 5
            if self.data != self.checksum:
                self.putx([13, ['Cksum error', 'K error', 'KE']])
        self.length = self.length + 1
        self.checksum = self.checksum ^ self.data
        self.putx(self.byte_annotation(bintype, self.data))
        self.putb([bintype, bytes([self.data])])
        self.pending_bit_pos = None

    def frame_error(self):
        self.putx([7, ['Frame error', 'F error', 'FE']])

    def handle_start(self):
        self.wait({Pin.SDCKA: 'l', Pin.SDCKB: 'h'})
        self.ss = self.samplenum
        count = 0
        while True:
            sdcka, sdckb = self.wait([{Pin.SDCKB: 'f'}, {Pin.SDCKA: 'r'}])
            if self.matched[0]:
                count = count + 1
            if self.matched[1]:
                self.es = self.samplenum
                if sdckb == 1:
                    if count == 4:
                        self.got_start()
                        return True
                    elif count == 6:
                        self.got_start_with_crc()
                        return True
                    elif count == 8:
                        self.got_occupancy()
                        return False
                    elif count >= 14:
                        self.got_reset()
                        return False
                self.frame_error()
                return False

    def handle_byte_or_stop(self):
        self.ss = self.samplenum
        self.pending_bit_pos = None
        initial = True
        counta = 0
        countb = 0
        self.data = 0
        while countb < 4:
            sdcka, sdckb = self.wait([{Pin.SDCKA: 'f'}, {Pin.SDCKB: 'f'}])
            self.es = self.samplenum
            if self.matched[0]:
                if counta == countb:
                    self.got_bit(sdckb)
                    counta = counta + 1
                elif counta == 1 and countb == 0 and self.data == 0 and sdckb == 0:
                    self.wait([{Pin.SDCKA: 'h', Pin.SDCKB: 'h'},
                               {Pin.SDCKA: 'f'}, {Pin.SDCKB: 'f'}])
                    self.es = self.samplenum
                    if self.matched[0]:
                        self.got_end()
                    else:
                        self.frame_error()
                    return False
                else:
                    self.frame_error()
                    return False
            elif self.matched[1]:
                if counta == countb + 1:
                    self.got_bit(sdcka)
                    countb = countb + 1
                elif counta == 0 and countb == 0 and sdcka == 1 and initial:
                    self.ss = self.samplenum
                    initial = False
                else:
                    self.frame_error()
                    return False
        self.wait({Pin.SDCKA: 'h'})
        self.es = self.samplenum
        self.got_byte()
        return True

    def decode(self):
        while True:
            while not self.handle_start():
                pass
            self.length = 0
            self.expected_length = 4
            self.checksum = 0
            while self.handle_byte_or_stop():
                pass
