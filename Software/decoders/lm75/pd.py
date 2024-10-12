##
## This file is part of the libsigrokdecode project.
##
## Copyright (C) 2012 Uwe Hermann <uwe@hermann-uwe.de>
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

# TODO: Better support for various LM75 compatible devices.

import sigrokdecode as srd

# LM75 only supports 9 bit resolution, compatible devices usually 9-12 bits.
resolution = {
    # CONFIG[6:5]: <resolution>
    0x00: 9,
    0x01: 10,
    0x02: 11,
    0x03: 12,
}

ft = {
    # CONFIG[4:3]: <fault tolerance setting>
    0x00: 1,
    0x01: 2,
    0x02: 4,
    0x03: 6,
}

class Decoder(srd.Decoder):
    api_version = 3
    id = 'lm75'
    name = 'LM75'
    longname = 'National LM75'
    desc = 'National LM75 (and compatibles) temperature sensor.'
    license = 'gplv2+'
    inputs = ['i2c']
    outputs = []
    tags = ['Sensor']
    options = (
        {'id': 'sensor', 'desc': 'Sensor type', 'default': 'lm75',
            'values': ('lm75',)},
        {'id': 'resolution', 'desc': 'Resolution (bits)', 'default': 9,
            'values': (9, 10, 11, 12)},
    )
    annotations = (
        ('celsius', 'Temperature / °C'),
        ('kelvin', 'Temperature / Kelvin'),
        ('text-verbose', 'Text (verbose)'),
        ('text', 'Text'),
        ('warning', 'Warning'),
    )

    def __init__(self):
        self.reset()

    def reset(self):
        self.state = 'IDLE'
        self.reg = 0x00 # Currently selected register
        self.databytes = []

    def start(self):
        self.out_ann = self.register(srd.OUTPUT_ANN)

    def putx(self, data):
        # Helper for annotations which span exactly one I²C packet.
        self.put(self.ss, self.es, self.out_ann, data)

    def putb(self, data):
        # Helper for annotations which span a block of I²C packets.
        self.put(self.ss_block, self.es_block, self.out_ann, data)

    def warn_upon_invalid_slave(self, addr):
        # LM75 and compatible devices have a 7-bit I²C slave address where
        # the 4 MSBs are fixed to 1001, and the 3 LSBs are configurable.
        # Thus, valid slave addresses (1001xxx) range from 0x48 to 0x4f.
        if addr not in range(0x48, 0x4f + 1):
            s = 'Warning: I²C slave 0x%02x not an LM75 compatible sensor.'
            self.putx([4, [s % addr]])

    def output_temperature(self, s, rw):
        # TODO: Support for resolutions other than 9 bit.
        before, after = self.databytes[0], (self.databytes[1] >> 7) * 5
        celsius = float('%d.%d' % (before, after))
        kelvin = celsius + 273.15
        self.putb([0, ['%s: %.1f °C' % (s, celsius)]])
        self.putb([1, ['%s: %.1f K' % (s, kelvin)]])

        # Warn about the temperature register (0x00) being read-only.
        if s == 'Temperature' and rw == 'WRITE':
            s = 'Warning: The temperature register is read-only!'
            self.putb([4, [s]])

    def handle_temperature_reg(self, b, s, rw):
        # Common helper for the temperature/T_HYST/T_OS registers.
        if len(self.databytes) == 0:
            self.ss_block = self.ss
            self.databytes.append(b)
            return
        self.databytes.append(b)
        self.es_block = self.es
        self.output_temperature(s, rw)
        self.databytes = []

    def handle_reg_0x00(self, b, rw):
        # Temperature register (16bits, read-only).
        self.handle_temperature_reg(b, 'Temperature', rw)

    def handle_reg_0x01(self, b, rw):
        # Configuration register (8 bits, read/write).
        # TODO: Bit-exact annotation ranges.

        sd = b & (1 << 0)
        tmp = 'normal operation' if (sd == 0) else 'shutdown mode'
        s = 'SD = %d: %s\n' % (sd, tmp)
        s2 = 'SD = %s, ' % tmp

        cmp_int = b & (1 << 1)
        tmp = 'comparator' if (cmp_int == 0) else 'interrupt'
        s += 'CMP/INT = %d: %s mode\n' % (cmp_int, tmp)
        s2 += 'CMP/INT = %s, ' % tmp

        pol = b & (1 << 2)
        tmp = 'low' if (pol == 0) else 'high'
        s += 'POL = %d: OS polarity is active-%s\n' % (pol, tmp)
        s2 += 'POL = active-%s, ' % tmp

        bits = (b & ((1 << 4) | (1 << 3))) >> 3
        s += 'Fault tolerance setting: %d bit(s)\n' % ft[bits]
        s2 += 'FT = %d' % ft[bits]

        # Not supported by LM75, but by various compatible devices.
        if self.options['sensor'] != 'lm75': # TODO
            bits = (b & ((1 << 6) | (1 << 5))) >> 5
            s += 'Resolution: %d bits\n' % resolution[bits]
            s2 += ', resolution = %d' % resolution[bits]

        self.putx([2, [s]])
        self.putx([3, [s2]])

    def handle_reg_0x02(self, b, rw):
        # T_HYST register (16 bits, read/write).
        self.handle_temperature_reg(b, 'T_HYST trip temperature', rw)

    def handle_reg_0x03(self, b, rw):
        # T_OS register (16 bits, read/write).
        self.handle_temperature_reg(b, 'T_OS trip temperature', rw)

    def decode(self, ss, es, data):
        cmd, databyte = data

        # Store the start/end samples of this I²C packet.
        self.ss, self.es = ss, es

        # State machine.
        if self.state == 'IDLE':
            # Wait for an I²C START condition.
            if cmd != 'START':
                return
            self.state = 'GET SLAVE ADDR'
        elif self.state == 'GET SLAVE ADDR':
            # Wait for an address read/write operation.
            if cmd in ('ADDRESS READ', 'ADDRESS WRITE'):
                self.warn_upon_invalid_slave(databyte)
                self.state = cmd[8:] + ' REGS' # READ REGS / WRITE REGS
        elif self.state in ('READ REGS', 'WRITE REGS'):
            if cmd in ('DATA READ', 'DATA WRITE'):
                handle_reg = getattr(self, 'handle_reg_0x%02x' % self.reg)
                handle_reg(databyte, cmd[5:]) # READ / WRITE
            elif cmd == 'STOP':
                # TODO: Any output?
                self.state = 'IDLE'
            else:
                # self.putx([0, ['Ignoring: %s (data=%s)' % (cmd, databyte)]])
                pass
