##
## This file is part of the libsigrokdecode project.
##
## Copyright (C) 2019-2020 Philip Åkesson <philip.akesson@gmail.com>
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

from common.srdhelper import bitpack
import sigrokdecode as srd

class SamplerateError(Exception):
    pass

class Pin:
    SDQ, = range(1)

class Ann:
    BIT, BYTE, BREAK, = range(3)

class Decoder(srd.Decoder):
    api_version = 3
    id = 'sdq'
    name = 'SDQ'
    longname = 'Texas Instruments SDQ'
    desc = 'Texas Instruments SDQ. The SDQ protocol is also used by Apple.'
    license = 'gplv2+'
    inputs = ['logic']
    outputs = []
    tags = ['Embedded/industrial']
    channels = (
        {'id': 'sdq', 'name': 'SDQ', 'desc': 'Single wire SDQ data line.'},
    )
    options = (
        {'id': 'bitrate', 'desc': 'Bit rate', 'default': 98425},
    )
    annotations = (
        ('bit', 'Bit'),
        ('byte', 'Byte'),
        ('break', 'Break'),
    )
    annotation_rows = (
        ('bits', 'Bits', (Ann.BIT,)),
        ('bytes', 'Bytes', (Ann.BYTE,)),
        ('breaks', 'Breaks', (Ann.BREAK,)),
    )

    def puts(self, data):
        self.put(self.startsample, self.samplenum, self.out_ann, data)

    def putetu(self, data):
        self.put(self.startsample, self.startsample + int(self.bit_width), self.out_ann, data)

    def putbetu(self, data):
        self.put(self.bytepos, self.startsample + int(self.bit_width), self.out_ann, data)

    def __init__(self):
        self.reset()

    def reset(self):
        self.samplerate = None
        self.startsample = 0
        self.bits = []
        self.bytepos = 0

    def start(self):
        self.out_ann = self.register(srd.OUTPUT_ANN)

    def metadata(self, key, value):
        if key == srd.SRD_CONF_SAMPLERATE:
            self.samplerate = value

    def handle_bit(self, bit):
        self.bits.append(bit)
        self.putetu([Ann.BIT, [
            'Bit: {:d}'.format(bit),
            '{:d}'.format(bit),
        ]])

        if len(self.bits) == 8:
            byte = bitpack(self.bits)
            self.putbetu([Ann.BYTE, [
                'Byte: 0x{:02x}'.format(byte),
                '0x{:02x}'.format(byte),
            ]])
            self.bits = []
            self.bytepos = 0

    def handle_break(self):
        self.puts([Ann.BREAK, ['Break', 'BR']])
        self.bits = []
        self.startsample = self.samplenum
        self.bytepos = 0

    def decode(self):
        if not self.samplerate:
            raise SamplerateError('Cannot decode without samplerate.')
        self.bit_width = float(self.samplerate) / float(self.options['bitrate'])
        self.half_bit_width = self.bit_width / 2.0
        # BREAK if the line is low for longer than this.
        break_threshold = self.bit_width * 1.2

        # Wait until the line is high before inspecting input data.
        sdq, = self.wait({Pin.SDQ: 'h'})
        while True:
            # Get the length of a low pulse (falling to rising edge).
            sdq, = self.wait({Pin.SDQ: 'f'})
            self.startsample = self.samplenum
            if self.bytepos == 0:
                self.bytepos = self.samplenum
            sdq, = self.wait({Pin.SDQ: 'r'})

            # Check for 0 or 1 data bits, or the BREAK symbol.
            delta = self.samplenum - self.startsample
            if delta > break_threshold:
                self.handle_break()
            elif delta > self.half_bit_width:
                self.handle_bit(0)
            else:
                self.handle_bit(1)
