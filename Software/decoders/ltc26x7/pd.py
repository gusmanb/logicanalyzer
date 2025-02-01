##
## This file is part of the libsigrokdecode project.
##
## Copyright (C) 2020 Analog Devices Inc.
##
## This program is free software; you can redistribute it and/or modify
## it under the terms of the GNU General Public License as published by
## the Free Software Foundation; either version 3 of the License, or
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

slave_address = {
    0x00: ['GND', 'GND', 'GND', 'G'],
    0x01: ['FLOAT', 'FLOAT', 'FLOAT', 'F'],
    0x02: ['VCC', 'VCC', 'VCC', 'V'],
}

commands = {
    0x00: ['Write Input Register', 'Write In Reg', 'Wr In Reg', 'WIR'],
    0x01: ['Update DAC', 'Update', 'U'],
    0x03: ['Write and Power Up DAC', 'Write & Power Up', 'W&PU'],
    0x04: ['Power Down DAC', 'Power Down', 'PD'],
    0x0F: ['No Operation', 'No Op', 'NO'],
}

addresses = {
    0x00: ['DAC A', 'A'],
    0x01: ['DAC B', 'B'],
    0x0F: ['All DACs', 'All'],
}

input_voltage_format = ['%.6fV', '%.2fV']

class Decoder(srd.Decoder):
    api_version = 3
    id = 'ltc26x7'
    name = 'LTC26x7'
    longname = 'Linear Technology LTC26x7'
    desc = 'Linear Technology LTC26x7 16-/14-/12-bit rail-to-rail DACs.'
    license = 'gplv2+'
    inputs = ['i2c']
    outputs = []
    tags = ['IC', 'Analog/digital']
    options = (
        {'id': 'chip', 'desc': 'Chip', 'default': 'ltc2607',
            'values': ('ltc2607', 'ltc2617', 'ltc2627')},
        {'id': 'vref', 'desc': 'Reference voltage (V)', 'default': 1.5},
    )
    annotations = (
        ('slave_addr', 'Slave address'),
        ('command', 'Command'),
        ('address', 'Address'),
        ('dac_a_voltage', 'DAC A voltage'),
        ('dac_b_voltage', 'DAC B voltage'),
    )
    annotation_rows = (
        ('addr_cmd', 'Address/command', (0, 1, 2)),
        ('dac_a_voltages', 'DAC A voltages', (3,)),
        ('dac_b_voltages', 'DAC B voltages', (4,)),
    )

    def __init__(self):
        self.reset()

    def reset(self):
        self.state = 'IDLE'
        self.ss = -1
        self.data = 0x00
        self.dac_val = 0

    def start(self):
        self.out_ann = self.register(srd.OUTPUT_ANN)

    def convert_ternary_str(self, n):
        if n == 0:
            return [0, 0, 0]
        nums = []
        while n:
            n, r = divmod(n, 3)
            nums.append(r)
        while len(nums) < 3:
            nums.append(0)
        return list(reversed(nums))

    def handle_slave_addr(self, data):
        if data == 0x73:
            ann = ['Global address', 'Global addr', 'Glob addr', 'GA']
            self.put(self.ss, self.es, self.out_ann, [0, ann])
            return
        ann = ['CA2=%s CA1=%s CA0=%s', '2=%s 1=%s 0=%s', '%s %s %s', '%s %s %s']
        addr = 0
        for i in range(7):
            if i in [2, 3]:
                continue
            offset = i
            if i > 3:
                offset -= 2
            mask = 1 << i
            if data & mask:
                mask = 1 << offset
                addr |= mask

        addr -= 0x04
        ternary_values = self.convert_ternary_str(addr)
        for i in range(len(ann)):
            ann[i] = ann[i] % (slave_address[ternary_values[0]][i],
                               slave_address[ternary_values[1]][i],
                               slave_address[ternary_values[2]][i])
        self.put(self.ss, self.es, self.out_ann, [0, ann])

    def handle_cmd_addr(self, data):
        cmd_val = (data >> 4) & 0x0F
        self.dac_val = (data & 0x0F)
        sm = (self.ss + self.es) // 2

        self.put(self.ss, sm, self.out_ann, [1, commands[cmd_val]])
        self.put(sm, self.es, self.out_ann, [2, addresses[self.dac_val]])

    def handle_data(self, data):
        self.data = (self.data << 8) & 0xFF00
        self.data += data
        if self.options['chip'] == 'ltc2617':
            self.data = (self.data >> 2)
            self.data = (self.options['vref'] * self.data) / 0x3FFF
        elif self.options['chip'] == 'ltc2627':
            self.data = (self.data >> 4)
            self.data = (self.options['vref'] * self.data) / 0x0FFF
        else:
            self.data = (self.options['vref'] * self.data) / 0xFFFF
        ann = []
        for format in input_voltage_format:
            ann.append(format % self.data)
        self.data = 0

        if self.dac_val == 0x0F: # All DACs (A and B).
            self.put(self.ss, self.es, self.out_ann, [3 + 0, ann])
            self.put(self.ss, self.es, self.out_ann, [3 + 1, ann])
        else:
            self.put(self.ss, self.es, self.out_ann, [3 + self.dac_val, ann])

    def decode(self, ss, es, data):
        cmd, databyte = data
        self.es = es

        # State machine.
        if self.state == 'IDLE':
            # Wait for an I²C START condition.
            if cmd != 'START':
                return
            self.state = 'GET SLAVE ADDR'
        elif self.state == 'GET SLAVE ADDR':
            # Wait for an address write operation.
            if cmd != 'ADDRESS WRITE':
                return
            self.ss = ss
            self.handle_slave_addr(databyte)
            self.ss = -1
            self.state = 'GET CMD ADDR'
        elif self.state == 'GET CMD ADDR':
            if cmd != 'DATA WRITE':
                return
            self.ss = ss
            self.handle_cmd_addr(databyte)
            self.ss = -1
            self.state = 'WRITE DATA'
        elif self.state == 'WRITE DATA':
            if cmd == 'DATA WRITE':
                if self.ss == -1:
                    self.ss = ss
                    self.data = databyte
                    return
                self.handle_data(databyte)
                self.ss = -1
            elif cmd == 'STOP':
                self.state = 'IDLE'
            else:
                return
