##
## This file is part of the libsigrokdecode project.
##
## Copyright (C) 2018 Max Weller
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

import re
import sigrokdecode as srd
from common.srdhelper import SrdIntEnum

Pin = SrdIntEnum.from_str('Pin', 'CLK DATA CE')

ann_cmdbit, ann_databit, ann_cmd, ann_data, ann_warning = range(5)

class Decoder(srd.Decoder):
    api_version = 3
    id = 'sda2506'
    name = 'SDA2506'
    longname = 'Siemens SDA 2506-5'
    desc = 'Serial nonvolatile 1-Kbit EEPROM.'
    license = 'gplv2+'
    inputs = ['logic']
    outputs = []
    tags = ['IC', 'Memory']
    channels = (
        {'id': 'clk', 'name': 'CLK', 'desc': 'Clock'},
        {'id': 'd', 'name': 'DATA', 'desc': 'Data'},
        {'id': 'ce', 'name': 'CE#', 'desc': 'Chip-enable'},
    )
    annotations = (
        ('cmdbit', 'Command bit'),
        ('databit', 'Data bit'),
        ('cmd', 'Command'),
        ('databyte', 'Data byte'),
        ('warning', 'Warning'),
    )
    annotation_rows = (
        ('bits', 'Bits', (ann_cmdbit, ann_databit)),
        ('data', 'Data', (ann_data,)),
        ('commands', 'Commands', (ann_cmd,)),
        ('warnings', 'Warnings', (ann_warning,)),
    )

    def __init__(self):
        self.samplerate = None
        self.reset()

    def reset(self):
        self.cmdbits = []
        self.databits = []

    def metadata(self, key, value):
        if key == srd.SRD_CONF_SAMPLERATE:
            self.samplerate = value

    def start(self):
        self.out_ann = self.register(srd.OUTPUT_ANN)

    def putbit(self, ss, es, typ, value):
        self.put(ss, es, self.out_ann, [typ, ['%s' % (value)]])

    def putdata(self, ss, es):
        value = 0
        for i in range(8):
            value = (value << 1) | self.databits[i]
        self.put(ss, es, self.out_ann, [ann_data, ['%02X' % (value)]])

    def decode_bits(self, offset, width):
        out = 0
        for i in range(width):
            out = (out << 1) | self.cmdbits[offset + i][0]
        return (out, self.cmdbits[offset + width - 1][1], self.cmdbits[offset][2])

    def decode_field(self, name, offset, width):
        val, ss, es = self.decode_bits(offset, width)
        self.put(ss, es, self.out_ann, [ann_data, ['%s: %02X' % (name, val)]])
        return val

    def decode(self):
        while True:
            # Wait for CLK edge or CE# edge.
            clk, d, ce = self.wait([{Pin.CLK: 'e'}, {Pin.CE: 'e'}])

            if self.matched[0] and ce == 1 and clk == 1:
                # Rising clk edge and command mode.
                bitstart = self.samplenum
                self.wait({0: 'f'})
                self.cmdbits = [(d, bitstart, self.samplenum)] + self.cmdbits
                if len(self.cmdbits) > 24:
                    self.cmdbits = self.cmdbits[0:24]
                self.putbit(bitstart, self.samplenum, ann_cmdbit, d)
            elif self.matched[0] and ce == 0 and clk == 0:
                # Falling clk edge and data mode.
                bitstart = self.samplenum
                clk, d, ce = self.wait([{'skip': int(2.5 * (1e6 / self.samplerate))}, {0: 'r'}, {2: 'e'}]) # Wait 25 us for data ready.
                if self.matched == (True, False, False):
                    self.wait([{0: 'r'}, {2: 'e'}])
                if len(self.databits) == 0:
                    self.datastart = bitstart
                self.databits = [d] + self.databits
                self.putbit(bitstart, self.samplenum, ann_databit, d)
                if len(self.databits) == 8:
                    self.putdata(self.datastart, self.samplenum)
                    self.databits = []
            elif self.matched[1] and ce == 0:
                # Chip enable edge.
                try:
                    self.decode_field('addr', 1, 7)
                    self.decode_field('CB', 0, 1)
                    if self.cmdbits[0][0] == 0:
                        # Beginning read command.
                        self.decode_field('read', 1, 7)
                        self.put(self.cmdbits[7][1], self.samplenum,
                            self.out_ann, [ann_cmd, ['read' ]])
                    elif d == 0:
                        # Beginning write command.
                        self.decode_field('data', 8, 8)
                        addr, ss, es = self.decode_bits(1, 7)
                        data, ss, es = self.decode_bits(8, 8)
                        cmdstart = self.samplenum
                        self.wait({2: 'r'})
                        self.put(cmdstart, self.samplenum, self.out_ann,
                            [ann_cmd, ['Write to %02X: %02X' % (addr, data)]])
                    else:
                        # Beginning erase command.
                        val, ss, es = self.decode_bits(1, 7)
                        cmdstart = self.samplenum
                        self.wait({2: 'r'})
                        self.put(cmdstart, self.samplenum, self.out_ann,
                            [ann_cmd, ['Erase: %02X' % (val)]])
                    self.databits = []
                except Exception as ex:
                    self.reset()
