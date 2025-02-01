##
## This file is part of the libsigrokdecode project.
##
## Copyright (C) 2010-2014 Uwe Hermann <uwe@hermann-uwe.de>
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

class Decoder(srd.Decoder):
    api_version = 3
    id = 'nunchuk'
    name = 'Nunchuk'
    longname = 'Nintendo Wii Nunchuk'
    desc = 'Nintendo Wii Nunchuk controller protocol.'
    license = 'gplv2+'
    inputs = ['i2c']
    outputs = []
    tags = ['Sensor']
    annotations = \
        tuple(('reg-0x%02X' % i, 'Register 0x%02X' % i) for i in range(6)) + (
        ('bit-bz', 'BZ bit'),
        ('bit-bc', 'BC bit'),
        ('bit-ax', 'AX bits'),
        ('bit-ay', 'AY bits'),
        ('bit-az', 'AZ bits'),
        ('nunchuk-write', 'Nunchuk write'),
        ('cmd-init', 'Init command'),
        ('summary', 'Summary'),
        ('warning', 'Warning'),
    )
    annotation_rows = (
        ('regs', 'Registers', tuple(range(13))),
        ('summaries', 'Summaries', (13,)),
        ('warnings', 'Warnings', (14,)),
    )

    def __init__(self):
        self.reset()

    def reset(self):
        self.state = 'IDLE'
        self.sx = self.sy = self.ax = self.ay = self.az = self.bz = self.bc = -1
        self.databytecount = 0
        self.reg = 0x00
        self.ss = self.es = self.ss_block = self.es_block = 0
        self.init_seq = []

    def start(self):
        self.out_ann = self.register(srd.OUTPUT_ANN)

    def putx(self, data):
        self.put(self.ss, self.es, self.out_ann, data)

    def putb(self, data):
        self.put(self.ss_block, self.es_block, self.out_ann, data)

    def putd(self, bit1, bit2, data):
        self.put(self.bits[bit1][1], self.bits[bit2][2], self.out_ann, data)

    def handle_reg_0x00(self, databyte):
        self.ss_block = self.ss
        self.sx = databyte
        self.putx([0, ['Analog stick X position: 0x%02X' % self.sx,
                       'SX: 0x%02X' % self.sx]])

    def handle_reg_0x01(self, databyte):
        self.sy = databyte
        self.putx([1, ['Analog stick Y position: 0x%02X' % self.sy,
                       'SY: 0x%02X' % self.sy]])

    def handle_reg_0x02(self, databyte):
        self.ax = databyte << 2
        self.putx([2, ['Accelerometer X value bits[9:2]: 0x%03X' % self.ax,
                       'AX[9:2]: 0x%03X' % self.ax]])

    def handle_reg_0x03(self, databyte):
        self.ay = databyte << 2
        self.putx([3, ['Accelerometer Y value bits[9:2]: 0x%03X' % self.ay,
                       'AY[9:2]: 0x%03X' % self.ay]])

    def handle_reg_0x04(self, databyte):
        self.az = databyte << 2
        self.putx([4, ['Accelerometer Z value bits[9:2]: 0x%03X' % self.az,
                       'AZ[9:2]: 0x%03X' % self.az]])

    def handle_reg_0x05(self, databyte):
        self.es_block = self.es
        self.bz = (databyte & (1 << 0)) >> 0 # Bits[0:0]
        self.bc = (databyte & (1 << 1)) >> 1 # Bits[1:1]
        ax_rest = (databyte & (3 << 2)) >> 2 # Bits[3:2]
        ay_rest = (databyte & (3 << 4)) >> 4 # Bits[5:4]
        az_rest = (databyte & (3 << 6)) >> 6 # Bits[7:6]
        self.ax |= ax_rest
        self.ay |= ay_rest
        self.az |= az_rest

        # self.putx([5, ['Register 5', 'Reg 5', 'R5']])

        s = '' if (self.bz == 0) else 'not '
        self.putd(0, 0, [6, ['Z: %spressed' % s, 'BZ: %d' % self.bz]])

        s = '' if (self.bc == 0) else 'not '
        self.putd(1, 1, [7, ['C: %spressed' % s, 'BC: %d' % self.bc]])

        self.putd(3, 2, [8, ['Accelerometer X value bits[1:0]: 0x%X' % ax_rest,
                             'AX[1:0]: 0x%X' % ax_rest]])

        self.putd(5, 4, [9, ['Accelerometer Y value bits[1:0]: 0x%X' % ay_rest,
                             'AY[1:0]: 0x%X' % ay_rest]])

        self.putd(7, 6, [10, ['Accelerometer Z value bits[1:0]: 0x%X' % az_rest,
                              'AZ[1:0]: 0x%X' % az_rest]])

        self.reg = 0x00

    def output_full_block_if_possible(self):
        # For now, only output summary annotations if all values are available.
        t = (self.sx, self.sy, self.ax, self.ay, self.az, self.bz, self.bc)
        if -1 in t:
            return
        bz = 'pressed' if self.bz == 0 else 'not pressed'
        bc = 'pressed' if self.bc == 0 else 'not pressed'
        s = 'Analog stick: %d/%d, accelerometer: %d/%d/%d, Z: %s, C: %s' % \
            (self.sx, self.sy, self.ax, self.ay, self.az, bz, bc)
        self.putb([13, [s]])

    def handle_reg_write(self, databyte):
        self.putx([11, ['Nunchuk write: 0x%02X' % databyte]])
        if len(self.init_seq) < 2:
            self.init_seq.append(databyte)

    def output_init_seq(self):
        if len(self.init_seq) != 2:
            self.putb([14, ['Init sequence was %d bytes long (2 expected)' % \
                      len(self.init_seq)]])
            return

        if self.init_seq != [0x40, 0x00]:
            self.putb([14, ['Unknown init sequence (expected: 0x40 0x00)']])
            return

        # TODO: Detect Nunchuk clones (they have different init sequences).

        self.putb([12, ['Initialize Nunchuk', 'Init Nunchuk', 'Init', 'I']])

    def decode(self, ss, es, data):
        cmd, databyte = data

        # Collect the 'BITS' packet, then return. The next packet is
        # guaranteed to belong to these bits we just stored.
        if cmd == 'BITS':
            self.bits = databyte
            return

        self.ss, self.es = ss, es

        # State machine.
        if self.state == 'IDLE':
            # Wait for an I²C START condition.
            if cmd != 'START':
                return
            self.state = 'GET SLAVE ADDR'
            self.ss_block = ss
        elif self.state == 'GET SLAVE ADDR':
            # Wait for an address read/write operation.
            if cmd == 'ADDRESS READ':
                self.state = 'READ REGS'
            elif cmd == 'ADDRESS WRITE':
                self.state = 'WRITE REGS'
        elif self.state == 'READ REGS':
            if cmd == 'DATA READ':
                handle_reg = getattr(self, 'handle_reg_0x%02x' % self.reg)
                handle_reg(databyte)
                self.reg += 1
            elif cmd == 'STOP':
                self.es_block = es
                self.output_full_block_if_possible()
                self.sx = self.sy = self.ax = self.ay = self.az = -1
                self.bz = self.bc = -1
                self.state = 'IDLE'
            else:
                # self.putx([14, ['Ignoring: %s (data=%s)' % (cmd, databyte)]])
                pass
        elif self.state == 'WRITE REGS':
            if cmd == 'DATA WRITE':
                self.handle_reg_write(databyte)
            elif cmd == 'STOP':
                self.es_block = es
                self.output_init_seq()
                self.init_seq = []
                self.state = 'IDLE'
            else:
                # self.putx([14, ['Ignoring: %s (data=%s)' % (cmd, databyte)]])
                pass
