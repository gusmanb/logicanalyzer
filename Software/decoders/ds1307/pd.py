##
## This file is part of the libsigrokdecode project.
##
## Copyright (C) 2012-2020 Uwe Hermann <uwe@hermann-uwe.de>
## Copyright (C) 2013 Matt Ranostay <mranostay@gmail.com>
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
from common.srdhelper import bcd2int, SrdIntEnum

days_of_week = (
    'Sunday', 'Monday', 'Tuesday', 'Wednesday',
    'Thursday', 'Friday', 'Saturday',
)

regs = (
    'Seconds', 'Minutes', 'Hours', 'Day', 'Date', 'Month', 'Year',
    'Control', 'RAM',
)

bits = (
    'Clock halt', 'Seconds', 'Reserved', 'Minutes', '12/24 hours', 'AM/PM',
    'Hours', 'Day', 'Date', 'Month', 'Year', 'OUT', 'SQWE', 'RS', 'RAM',
)

rates = {
    0b00: '1Hz',
    0b01: '4096Hz',
    0b10: '8192Hz',
    0b11: '32768Hz',
}

DS1307_I2C_ADDRESS = 0x68

def regs_and_bits():
    l = [('reg_' + r.lower(), r + ' register') for r in regs]
    l += [('bit_' + re.sub(r'\/| ', '_', b).lower(), b + ' bit') for b in bits]
    return tuple(l)

a = ['REG_' + r.upper() for r in regs] + \
    ['BIT_' + re.sub(r'\/| ', '_', b).upper() for b in bits] + \
    ['READ_DATE_TIME', 'WRITE_DATE_TIME', 'READ_REG', 'WRITE_REG', 'WARNING']
Ann = SrdIntEnum.from_list('Ann', a)

class Decoder(srd.Decoder):
    api_version = 3
    id = 'ds1307'
    name = 'DS1307'
    longname = 'Dallas DS1307'
    desc = 'Dallas DS1307 realtime clock module protocol.'
    license = 'gplv2+'
    inputs = ['i2c']
    outputs = []
    tags = ['Clock/timing', 'IC']
    annotations =  regs_and_bits() + (
        ('read_date_time', 'Read date/time'),
        ('write_date_time', 'Write date/time'),
        ('read_reg', 'Register read'),
        ('write_reg', 'Register write'),
        ('warning', 'Warning'),
    )
    annotation_rows = (
        ('bits', 'Bits', Ann.prefixes('BIT_')),
        ('regs', 'Registers', Ann.prefixes('REG_')),
        ('date_time', 'Date/time', Ann.prefixes('READ_ WRITE_')),
        ('warnings', 'Warnings', (Ann.WARNING,)),
    )

    def __init__(self):
        self.reset()

    def reset(self):
        self.state = 'IDLE'
        self.hours = -1
        self.minutes = -1
        self.seconds = -1
        self.days = -1
        self.date = -1
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
                 [Ann.BIT_RESERVED, ['Reserved bit', 'Reserved', 'Rsvd', 'R']])

    def handle_reg_0x00(self, b): # Seconds (0-59) / Clock halt bit
        self.putd(7, 0, [Ann.REG_SECONDS, ['Seconds', 'Sec', 'S']])
        ch = 1 if (b & (1 << 7)) else 0
        self.putd(7, 7, [Ann.BIT_CLOCK_HALT, ['Clock halt: %d' % ch,
            'Clk hlt: %d' % ch, 'CH: %d' % ch, 'CH']])
        s = self.seconds = bcd2int(b & 0x7f)
        self.putd(6, 0, [Ann.BIT_SECONDS, ['Second: %d' % s, 'Sec: %d' % s,
            'S: %d' % s, 'S']])

    def handle_reg_0x01(self, b): # Minutes (0-59)
        self.putd(7, 0, [Ann.REG_MINUTES, ['Minutes', 'Min', 'M']])
        self.putr(7)
        m = self.minutes = bcd2int(b & 0x7f)
        self.putd(6, 0, [Ann.BIT_MINUTES, ['Minute: %d' % m, 'Min: %d' % m, 'M: %d' % m, 'M']])

    def handle_reg_0x02(self, b): # Hours (1-12+AM/PM or 0-23)
        self.putd(7, 0, [Ann.REG_HOURS, ['Hours', 'H']])
        self.putr(7)
        ampm_mode = True if (b & (1 << 6)) else False
        if ampm_mode:
            self.putd(6, 6, [Ann.BIT_12_24_HOURS, ['12-hour mode', '12h mode', '12h']])
            a = 'PM' if (b & (1 << 5)) else 'AM'
            self.putd(5, 5, [Ann.BIT_AM_PM, [a, a[0]]])
            h = self.hours = bcd2int(b & 0x1f)
            self.putd(4, 0, [Ann.BIT_HOURS, ['Hour: %d' % h, 'H: %d' % h, 'H']])
        else:
            self.putd(6, 6, [Ann.BIT_12_24_HOURS, ['24-hour mode', '24h mode', '24h']])
            h = self.hours = bcd2int(b & 0x3f)
            self.putd(5, 0, [Ann.BIT_HOURS, ['Hour: %d' % h, 'H: %d' % h, 'H']])

    def handle_reg_0x03(self, b): # Day / day of week (1-7)
        self.putd(7, 0, [Ann.REG_DAY, ['Day of week', 'Day', 'D']])
        for i in (7, 6, 5, 4, 3):
            self.putr(i)
        w = self.days = bcd2int(b & 0x07)
        ws = days_of_week[self.days - 1]
        self.putd(2, 0, [Ann.BIT_DAY, ['Weekday: %s' % ws, 'WD: %s' % ws, 'WD', 'W']])

    def handle_reg_0x04(self, b): # Date (1-31)
        self.putd(7, 0, [Ann.REG_DATE, ['Date', 'D']])
        for i in (7, 6):
            self.putr(i)
        d = self.date = bcd2int(b & 0x3f)
        self.putd(5, 0, [Ann.BIT_DATE, ['Date: %d' % d, 'D: %d' % d, 'D']])

    def handle_reg_0x05(self, b): # Month (1-12)
        self.putd(7, 0, [Ann.REG_MONTH, ['Month', 'Mon', 'M']])
        for i in (7, 6, 5):
            self.putr(i)
        m = self.months = bcd2int(b & 0x1f)
        self.putd(4, 0, [Ann.BIT_MONTH, ['Month: %d' % m, 'Mon: %d' % m, 'M: %d' % m, 'M']])

    def handle_reg_0x06(self, b): # Year (0-99)
        self.putd(7, 0, [Ann.REG_YEAR, ['Year', 'Y']])
        y = self.years = bcd2int(b & 0xff)
        self.years += 2000
        self.putd(7, 0, [Ann.BIT_YEAR, ['Year: %d' % y, 'Y: %d' % y, 'Y']])

    def handle_reg_0x07(self, b): # Control Register
        self.putd(7, 0, [Ann.REG_CONTROL, ['Control', 'Ctrl', 'C']])
        for i in (6, 5, 3, 2):
            self.putr(i)
        o = 1 if (b & (1 << 7)) else 0
        s = 1 if (b & (1 << 4)) else 0
        s2 = 'en' if (b & (1 << 4)) else 'dis'
        r = rates[b & 0x03]
        self.putd(7, 7, [Ann.BIT_OUT, ['Output control: %d' % o,
            'OUT: %d' % o, 'O: %d' % o, 'O']])
        self.putd(4, 4, [Ann.BIT_SQWE, ['Square wave output: %sabled' % s2,
            'SQWE: %sabled' % s2, 'SQWE: %d' % s, 'S: %d' % s, 'S']])
        self.putd(1, 0, [Ann.BIT_RS, ['Square wave output rate: %s' % r,
            'Square wave rate: %s' % r, 'SQW rate: %s' % r, 'Rate: %s' % r,
            'RS: %s' % s, 'RS', 'R']])

    def handle_reg_0x3f(self, b): # RAM (bytes 0x08-0x3f)
        self.putd(7, 0, [Ann.REG_RAM, ['RAM', 'R']])
        self.putd(7, 0, [Ann.BIT_RAM, ['SRAM: 0x%02X' % b, '0x%02X' % b]])

    def output_datetime(self, cls, rw):
        # TODO: Handle read/write of only parts of these items.
        d = '%s, %02d.%02d.%4d %02d:%02d:%02d' % (
            days_of_week[self.days - 1], self.date, self.months,
            self.years, self.hours, self.minutes, self.seconds)
        self.put(self.ss_block, self.es, self.out_ann,
                 [cls, ['%s date/time: %s' % (rw, d)]])

    def handle_reg(self, b):
        r = self.reg if self.reg < 8 else 0x3f
        fn = getattr(self, 'handle_reg_0x%02x' % r)
        fn(b)
        # Honor address auto-increment feature of the DS1307. When the
        # address reaches 0x3f, it will wrap around to address 0.
        self.reg += 1
        if self.reg > 0x3f:
            self.reg = 0

    def is_correct_chip(self, addr):
        if addr == DS1307_I2C_ADDRESS:
            return True
        self.put(self.ss_block, self.es, self.out_ann,
                 [Ann.WARNING, ['Ignoring non-DS1307 data (slave 0x%02X)' % addr]])
        return False

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
            if cmd != 'ADDRESS WRITE':
                return
            if not self.is_correct_chip(databyte):
                self.state = 'IDLE'
                return
            self.state = 'GET REG ADDR'
        elif self.state == 'GET REG ADDR':
            # Wait for a data write (master selects the slave register).
            if cmd != 'DATA WRITE':
                return
            self.reg = databyte
            self.state = 'WRITE RTC REGS'
        elif self.state == 'WRITE RTC REGS':
            # If we see a Repeated Start here, it's an RTC read.
            if cmd == 'START REPEAT':
                self.state = 'READ RTC REGS'
                return
            # Otherwise: Get data bytes until a STOP condition occurs.
            if cmd == 'DATA WRITE':
                self.handle_reg(databyte)
            elif cmd == 'STOP':
                self.output_datetime(Ann.WRITE_DATE_TIME, 'Written')
                self.state = 'IDLE'
        elif self.state == 'READ RTC REGS':
            # Wait for an address read operation.
            if cmd != 'ADDRESS READ':
                return
            if not self.is_correct_chip(databyte):
                self.state = 'IDLE'
                return
            self.state = 'READ RTC REGS2'
        elif self.state == 'READ RTC REGS2':
            if cmd == 'DATA READ':
                self.handle_reg(databyte)
            elif cmd == 'STOP':
                self.output_datetime(Ann.READ_DATE_TIME, 'Read')
                self.state = 'IDLE'
