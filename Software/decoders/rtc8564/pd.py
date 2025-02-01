##
## This file is part of the libsigrokdecode project.
##
## Copyright (C) 2012-2014 Uwe Hermann <uwe@hermann-uwe.de>
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
from common.srdhelper import bcd2int

def reg_list():
    l = []
    for i in range(8 + 1):
        l.append(('reg-0x%02x' % i, 'Register 0x%02x' % i))

    return tuple(l)

class Decoder(srd.Decoder):
    api_version = 3
    id = 'rtc8564'
    name = 'RTC-8564'
    longname = 'Epson RTC-8564 JE/NB'
    desc = 'Realtime clock module protocol.'
    license = 'gplv2+'
    inputs = ['i2c']
    outputs = []
    tags = ['Clock/timing']
    annotations = reg_list() + (
        ('read', 'Read date/time'),
        ('write', 'Write date/time'),
        ('bit-reserved', 'Reserved bit'),
        ('bit-vl', 'VL bit'),
        ('bit-century', 'Century bit'),
        ('reg-read', 'Register read'),
        ('reg-write', 'Register write'),
    )
    annotation_rows = (
        ('bits', 'Bits', tuple(range(0, 8 + 1)) + (11, 12, 13)),
        ('regs', 'Register accesses', (14, 15)),
        ('date-time', 'Date/time', (9, 10)),
    )

    def __init__(self):
        self.reset()

    def reset(self):
        self.state = 'IDLE'
        self.hours = -1
        self.minutes = -1
        self.seconds = -1
        self.days = -1
        self.weekdays = -1
        self.months = -1
        self.years = -1
        self.bits = []

    def start(self):
        self.out_ann = self.register(srd.OUTPUT_ANN)

    def putx(self, data):
        self.put(self.ss, self.es, self.out_ann, data)

    def putd(self, bit1, bit2, data):
        self.put(self.bits[bit1][1], self.bits[bit2][2], self.out_ann, data)

    def putr(self, bit):
        self.put(self.bits[bit][1], self.bits[bit][2], self.out_ann,
                 [11, ['Reserved bit', 'Reserved', 'Rsvd', 'R']])

    def handle_reg_0x00(self, b): # Control register 1
        pass

    def handle_reg_0x01(self, b): # Control register 2
        ti_tp = 1 if (b & (1 << 4)) else 0
        af = 1 if (b & (1 << 3)) else 0
        tf = 1 if (b & (1 << 2)) else 0
        aie = 1 if (b & (1 << 1)) else 0
        tie = 1 if (b & (1 << 0)) else 0

        ann = ''

        s = 'repeated' if ti_tp else 'single-shot'
        ann += 'TI/TP = %d: %s operation upon fixed-cycle timer interrupt '\
               'events\n' % (ti_tp, s)
        s = '' if af else 'no '
        ann += 'AF = %d: %salarm interrupt detected\n' % (af, s)
        s = '' if tf else 'no '
        ann += 'TF = %d: %sfixed-cycle timer interrupt detected\n' % (tf, s)
        s = 'enabled' if aie else 'prohibited'
        ann += 'AIE = %d: INT# pin output %s when an alarm interrupt '\
               'occurs\n' % (aie, s)
        s = 'enabled' if tie else 'prohibited'
        ann += 'TIE = %d: INT# pin output %s when a fixed-cycle interrupt '\
               'event occurs\n' % (tie, s)

        self.putx([1, [ann]])

    def handle_reg_0x02(self, b): # Seconds / Voltage-low bit
        vl = 1 if (b & (1 << 7)) else 0
        self.putd(7, 7, [12, ['Voltage low: %d' % vl, 'Volt. low: %d' % vl,
                        'VL: %d' % vl, 'VL']])
        s = self.seconds = bcd2int(b & 0x7f)
        self.putd(6, 0, [2, ['Second: %d' % s, 'Sec: %d' % s, 'S: %d' % s, 'S']])

    def handle_reg_0x03(self, b): # Minutes
        self.putr(7)
        m = self.minutes = bcd2int(b & 0x7f)
        self.putd(6, 0, [3, ['Minute: %d' % m, 'Min: %d' % m, 'M: %d' % m, 'M']])

    def handle_reg_0x04(self, b): # Hours
        self.putr(7)
        self.putr(6)
        h = self.hours = bcd2int(b & 0x3f)
        self.putd(5, 0, [4, ['Hour: %d' % h, 'H: %d' % h, 'H']])

    def handle_reg_0x05(self, b): # Days
        self.putr(7)
        self.putr(6)
        d = self.days = bcd2int(b & 0x3f)
        self.putd(5, 0, [5, ['Day: %d' % d, 'D: %d' % d, 'D']])

    def handle_reg_0x06(self, b): # Weekdays
        for i in (7, 6, 5, 4, 3):
            self.putr(i)
        w = self.weekdays = bcd2int(b & 0x07)
        self.putd(2, 0, [6, ['Weekday: %d' % w, 'WD: %d' % w, 'WD', 'W']])

    def handle_reg_0x07(self, b): # Months / century bit
        c = 1 if (b & (1 << 7)) else 0
        self.putd(7, 7, [13, ['Century bit: %d' % c, 'Century: %d' % c,
                              'Cent: %d' % c, 'C: %d' % c, 'C']])
        self.putr(6)
        self.putr(5)
        m = self.months = bcd2int(b & 0x1f)
        self.putd(4, 0, [7, ['Month: %d' % m, 'Mon: %d' % m, 'M: %d' % m, 'M']])

    def handle_reg_0x08(self, b): # Years
        y = self.years = bcd2int(b & 0xff)
        self.putx([8, ['Year: %d' % y, 'Y: %d' % y, 'Y']])

    def handle_reg_0x09(self, b): # Alarm, minute
        pass

    def handle_reg_0x0a(self, b): # Alarm, hour
        pass

    def handle_reg_0x0b(self, b): # Alarm, day
        pass

    def handle_reg_0x0c(self, b): # Alarm, weekday
        pass

    def handle_reg_0x0d(self, b): # CLKOUT output
        pass

    def handle_reg_0x0e(self, b): # Timer setting
        pass

    def handle_reg_0x0f(self, b): # Down counter for fixed-cycle timer
        pass

    def decode(self, ss, es, data):
        cmd, databyte = data

        # Collect the 'BITS' packet, then return. The next packet is
        # guaranteed to belong to these bits we just stored.
        if cmd == 'BITS':
            self.bits = databyte
            return

        # Store the start/end samples of this I²C packet.
        self.ss, self.es = ss, es

        # State machine.
        if self.state == 'IDLE':
            # Wait for an I²C START condition.
            if cmd != 'START':
                return
            self.state = 'GET SLAVE ADDR'
            self.ss_block = ss
        elif self.state == 'GET SLAVE ADDR':
            # Wait for an address write operation.
            # TODO: We should only handle packets to the RTC slave (0xa2/0xa3).
            if cmd != 'ADDRESS WRITE':
                return
            self.state = 'GET REG ADDR'
        elif self.state == 'GET REG ADDR':
            # Wait for a data write (master selects the slave register).
            if cmd != 'DATA WRITE':
                return
            self.reg = databyte
            self.state = 'WRITE RTC REGS'
        elif self.state == 'WRITE RTC REGS':
            # If we see a Repeated Start here, it's probably an RTC read.
            if cmd == 'START REPEAT':
                self.state = 'READ RTC REGS'
                return
            # Otherwise: Get data bytes until a STOP condition occurs.
            if cmd == 'DATA WRITE':
                r, s = self.reg, '%02X: %02X' % (self.reg, databyte)
                self.putx([15, ['Write register %s' % s, 'Write reg %s' % s,
                                'WR %s' % s, 'WR', 'W']])
                handle_reg = getattr(self, 'handle_reg_0x%02x' % self.reg)
                handle_reg(databyte)
                self.reg += 1
                # TODO: Check for NACK!
            elif cmd == 'STOP':
                # TODO: Handle read/write of only parts of these items.
                d = '%02d.%02d.%02d %02d:%02d:%02d' % (self.days, self.months,
                    self.years, self.hours, self.minutes, self.seconds)
                self.put(self.ss_block, es, self.out_ann,
                         [9, ['Write date/time: %s' % d, 'Write: %s' % d,
                              'W: %s' % d]])
                self.state = 'IDLE'
            else:
                pass # TODO
        elif self.state == 'READ RTC REGS':
            # Wait for an address read operation.
            # TODO: We should only handle packets to the RTC slave (0xa2/0xa3).
            if cmd == 'ADDRESS READ':
                self.state = 'READ RTC REGS2'
                return
            else:
                pass # TODO
        elif self.state == 'READ RTC REGS2':
            if cmd == 'DATA READ':
                r, s = self.reg, '%02X: %02X' % (self.reg, databyte)
                self.putx([15, ['Read register %s' % s, 'Read reg %s' % s,
                                'RR %s' % s, 'RR', 'R']])
                handle_reg = getattr(self, 'handle_reg_0x%02x' % self.reg)
                handle_reg(databyte)
                self.reg += 1
                # TODO: Check for NACK!
            elif cmd == 'STOP':
                d = '%02d.%02d.%02d %02d:%02d:%02d' % (self.days, self.months,
                    self.years, self.hours, self.minutes, self.seconds)
                self.put(self.ss_block, es, self.out_ann,
                         [10, ['Read date/time: %s' % d, 'Read: %s' % d,
                               'R: %s' % d]])
                self.state = 'IDLE'
            else:
                pass # TODO?
