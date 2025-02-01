##
## This file is part of the libsigrokdecode project.
##
## Copyright (C) 2017 Karl Palsson <karlp@etactica.com>
##
## Permission is hereby granted, free of charge, to any person obtaining a copy
## of this software and associated documentation files (the "Software"), to deal
## in the Software without restriction, including without limitation the rights
## to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
## copies of the Software, and to permit persons to whom the Software is
## furnished to do so, subject to the following conditions:
##
## The above copyright notice and this permission notice shall be included in all
## copies or substantial portions of the Software.
##
## THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
## IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
## FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
## AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
## LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
## OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
## SOFTWARE.

import math
import sigrokdecode as srd
from .lists import *

class Decoder(srd.Decoder):
    api_version = 3
    id = 'ade77xx'
    name = 'ADE77xx'
    longname = 'Analog Devices ADE77xx'
    desc = 'Poly phase multifunction energy metering IC protocol.'
    license = 'mit'
    inputs = ['spi']
    outputs = []
    tags = ['Analog/digital', 'IC', 'Sensor']
    annotations = (
        ('read', 'Register read'),
        ('write', 'Register write'),
        ('warning', 'Warning'),
    )
    annotation_rows = (
        ('reads', 'Reads', (0,)),
        ('writes', 'Writes', (1,)),
        ('warnings', 'Warnings', (2,)),
    )

    def reset_data(self):
        self.expected = 0
        self.mosi_bytes, self.miso_bytes = [], []

    def __init__(self):
        self.reset()

    def reset(self):
        self.ss_cmd, self.es_cmd = 0, 0
        self.reset_data()

    def start(self):
        self.out_ann = self.register(srd.OUTPUT_ANN)

    def putx(self, data):
        self.put(self.ss_cmd, self.es_cmd, self.out_ann, data)

    def put_warn(self, pos, msg):
        self.put(pos[0], pos[1], self.out_ann, [2, [msg]])

    def decode(self, ss, es, data):
        ptype = data[0]
        if ptype == 'CS-CHANGE':
            # Bear in mind, that CS is optional according to the datasheet.
            # If we transition high mid-stream, toss out our data and restart.
            cs_old, cs_new = data[1:]
            if cs_old is not None and cs_old == 0 and cs_new == 1:
                if len(self.mosi_bytes) > 0 and len(self.mosi_bytes[1:]) < self.expected:
                    # Mark short read/write for reg at least!
                    self.es_cmd = es
                    write, reg = self.cmd & 0x80, self.cmd & 0x7f
                    rblob = regs.get(reg)
                    idx = 1 if write else 0
                    self.putx([idx, ['%s: %s' % (rblob[0], "SHORT")]])
                    self.put_warn([self.ss_cmd, es], "Short transfer!")
                self.reset_data()
            return

        # Don't care about anything else.
        if ptype != 'DATA':
            return
        mosi, miso = data[1:]

        if len(self.mosi_bytes) == 0:
            self.ss_cmd = ss
        self.mosi_bytes.append(mosi)
        self.miso_bytes.append(miso)

        # A transfer is 2-4 bytes, (command + 1..3 byte reg).
        if len(self.mosi_bytes) < 2:
            return

        self.cmd = self.mosi_bytes[0]
        write, reg = self.cmd & 0x80, self.cmd & 0x7f
        rblob = regs.get(reg)
        if not rblob:
            # If you don't have CS, this will _destroy_ comms!
            self.put_warn([self.ss_cmd, es], 'Unknown register!')
            return

        self.expected = math.ceil(rblob[3] / 8)
        if len(self.mosi_bytes[1:]) != self.expected:
            return
        valo, vali = None, None
        self.es_cmd = es
        if self.expected == 3:
            valo = self.mosi_bytes[1] << 16 | self.mosi_bytes[2] << 8 | \
                   self.mosi_bytes[3]
            vali = self.miso_bytes[1] << 16 | self.miso_bytes[2] << 8 | \
                   self.miso_bytes[3]
        elif self.expected == 2:
            valo = self.mosi_bytes[1] << 8 | self.mosi_bytes[2]
            vali = self.miso_bytes[1] << 8 | self.miso_bytes[2]
        elif self.expected == 1:
            valo = self.mosi_bytes[1]
            vali = self.miso_bytes[1]

        if write:
            self.putx([1, ['%s: %#x' % (rblob[0], valo)]])
        else:
            self.putx([0, ['%s: %#x' % (rblob[0], vali)]])

        self.reset_data()
