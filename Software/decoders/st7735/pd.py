##
## This file is part of the libsigrokdecode project.
##
## Copyright (C) 2018 Aleksander Alekseev <afiskon@gmail.com>
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

import sigrokdecode as srd

MAX_DATA_LEN = 128

# Command ID -> name, short description
META = {
    0x00: {'name': 'NOP    ', 'desc': 'No operation'},
    0x01: {'name': 'SWRESET', 'desc': 'Software reset'},
    0x04: {'name': 'RDDID  ', 'desc': 'Read display ID'},
    0x09: {'name': 'RDDST  ', 'desc': 'Read display status'},
    0x10: {'name': 'SLPIN  ', 'desc': 'Sleep in & booster off'},
    0x11: {'name': 'SLPOUT ', 'desc': 'Sleep out & booster on'},
    0x12: {'name': 'PTLON  ', 'desc': 'Partial mode on'},
    0x13: {'name': 'NORON  ', 'desc': 'Partial off (normal)'},
    0x20: {'name': 'INVOFF ', 'desc': 'Display inversion off'},
    0x21: {'name': 'INVON  ', 'desc': 'Display inversion on'},
    0x28: {'name': 'DISPOFF', 'desc': 'Display off'},
    0x29: {'name': 'DISPON ', 'desc': 'Display on'},
    0x2A: {'name': 'CASET  ', 'desc': 'Column address set'},
    0x2B: {'name': 'RASET  ', 'desc': 'Row address set'},
    0x2C: {'name': 'RAMWR  ', 'desc': 'Memory write'},
    0x2E: {'name': 'RAMRD  ', 'desc': 'Memory read'},
    0x30: {'name': 'PTLAR  ', 'desc': 'Partial start/end address set'},
    0x36: {'name': 'MADCTL ', 'desc': 'Memory data address control'},
    0x3A: {'name': 'COLMOD ', 'desc': 'Interface pixel format'},
    0xB1: {'name': 'FRMCTR1', 'desc': 'Frame rate control (in normal mode / full colors)'},
    0xB2: {'name': 'FRMCTR2', 'desc': 'Frame rate control (in idle mode / 8-colors)'},
    0xB3: {'name': 'FRMCTR3', 'desc': 'Frame rate control (in partial mode / full colors) '},
    0xB4: {'name': 'INVCTR ', 'desc': 'Display inversion control'},
    0xB6: {'name': 'DISSET5', 'desc': 'Display function set 5'},
    0xC0: {'name': 'PWCTR1 ', 'desc': 'Power control 1'},
    0xC1: {'name': 'PWCTR2 ', 'desc': 'Power control 2'},
    0xC2: {'name': 'PWCTR3 ', 'desc': 'Power control 3'},
    0xC3: {'name': 'PWCTR4 ', 'desc': 'Power control 4'},
    0xC4: {'name': 'PWCTR5 ', 'desc': 'Power control 5'},
    0xC5: {'name': 'VMCTR1 ', 'desc': 'VCOM control 1'},
    0xDA: {'name': 'RDID1  ', 'desc': 'Read ID1'},
    0xDB: {'name': 'RDID2  ', 'desc': 'Read ID2'},
    0xDC: {'name': 'RDID3  ', 'desc': 'Read ID3'},
    0xDD: {'name': 'RDID4  ', 'desc': 'Read ID4'},
    0xFC: {'name': 'PWCTR6 ', 'desc': 'Power control 6'},
    0xE0: {'name': 'GMCTRP1', 'desc': 'Gamma \'+\'polarity correction characteristics setting'},
    0xE1: {'name': 'GMCTRN1', 'desc': 'Gamma \'-\'polarity correction characteristics setting'},
}

class Ann:
    BITS, CMD, DATA, DESC = range(4)

class Decoder(srd.Decoder):
    api_version = 3
    id = 'st7735'
    name = 'ST7735'
    longname = 'Sitronix ST7735'
    desc = 'Sitronix ST7735 TFT controller protocol.'
    license = 'gplv2+'
    inputs = ['logic']
    outputs = []
    tags = ['Display', 'IC']
    channels = (
        {'id': 'cs', 'name': 'CS#', 'desc': 'Chip-select'},
        {'id': 'clk', 'name': 'CLK', 'desc': 'Clock'},
        {'id': 'mosi', 'name': 'MOSI', 'desc': 'Master out, slave in'},
        {'id': 'dc', 'name': 'DC', 'desc': 'Data or command'}
    )
    annotations = (
        ('bit', 'Bit'),
        ('command', 'Command'),
        ('data', 'Data'),
        ('description', 'Description'),
    )
    annotation_rows = (
        ('bits', 'Bits', (Ann.BITS,)),
        ('fields', 'Fields', (Ann.CMD, Ann.DATA)),
        ('descriptions', 'Descriptions', (Ann.DESC,)),
    )

    def __init__(self):
        self.reset()

    def reset(self):
        self.accum_byte = 0
        self.accum_bits_num = 0
        self.bit_ss = -1
        self.byte_ss = -1
        self.current_bit = -1

    def start(self):
        self.out_ann = self.register(srd.OUTPUT_ANN)

    def put_desc(self, ss, es, cmd, data):
        if cmd == -1:
            return
        if cmd in META:
            self.put(ss, es, self.out_ann, [Ann.DESC,
                ['%s: %s' % (META[cmd]['name'].strip(), META[cmd]['desc'])]])
        else:
            # Default description:
            dots = ''
            if len(data) == MAX_DATA_LEN:
                data = data[:-1]
                dots = '...'
            data_str = '(none)'
            if len(data) > 0:
                data_str = ' '.join(['%02X' % b for b in data])
            self.put(ss, es, self.out_ann, [Ann.DESC,
                ['Unknown command: %02X. Data: %s%s' % (cmd, data_str, dots)]])

    def decode(self):
        current_cmd = -1
        current_data = []
        desc_ss = -1
        desc_es = -1
        self.reset()
        while True:
            # Check data on both CLK edges.
            (cs, clk, mosi, dc) = self.wait({1: 'e'})

            if cs == 1: # Wait for CS = low, ignore the rest.
                self.reset()
                continue

            if clk == 1:
                # Read one bit.
                self.bit_ss = self.samplenum
                if self.accum_bits_num == 0:
                    self.byte_ss = self.samplenum
                self.current_bit = mosi

            if (clk == 0) and (self.current_bit >= 0):
                # Process one bit.
                self.put(self.bit_ss, self.samplenum, self.out_ann,
                         [Ann.BITS, [str(self.current_bit)]])
                self.accum_byte = (self.accum_byte << 1) | self.current_bit # MSB-first.
                self.accum_bits_num += 1
                if self.accum_bits_num == 8:
                    # Process one byte.
                    ann = Ann.DATA if dc else Ann.CMD # DC = low for commands.
                    self.put(self.byte_ss, self.samplenum, self.out_ann,
                             [ann, ['%02X' % self.accum_byte]])
                    if ann == Ann.CMD:
                        self.put_desc(desc_ss, desc_es, current_cmd, current_data)
                        desc_ss = self.byte_ss
                        desc_es = self.samplenum # For cmds without data.
                        current_cmd = self.accum_byte
                        current_data = []
                    else:
                        if len(current_data) < MAX_DATA_LEN:
                            current_data += [self.accum_byte]
                        desc_es = self.samplenum

                    self.accum_bits_num = 0
                    self.accum_byte = 0
                    self.byte_ss = -1
                self.current_bit = -1
                self.bit_ss = -1
