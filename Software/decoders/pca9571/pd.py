##
## This file is part of the libsigrokdecode project.
##
## Copyright (C) 2019 Mickael Bosch <mickael.bosch@linux.com>
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

NUM_OUTPUT_CHANNELS = 8

# TODO: Other I²C functions: general call / reset address, device ID address.

def logic_channels(num_channels):
    l = []
    for i in range(num_channels):
        l.append(tuple(['p%d' % i, 'P%d' % i]))
    return tuple(l)

class Decoder(srd.Decoder):
    api_version = 3
    id = 'pca9571'
    name = 'PCA9571'
    longname = 'NXP PCA9571'
    desc = 'NXP PCA9571 8-bit I²C output expander.'
    license = 'gplv2+'
    inputs = ['i2c']
    outputs = []
    tags = ['Embedded/industrial', 'IC']
    annotations = (
        ('register', 'Register type'),
        ('value', 'Register value'),
        ('warning', 'Warning'),
    )
    logic_output_channels = logic_channels(NUM_OUTPUT_CHANNELS)
    annotation_rows = (
        ('regs', 'Registers', (0, 1)),
        ('warnings', 'Warnings', (2,)),
    )

    def __init__(self):
        self.reset()

    def reset(self):
        self.state = 'IDLE'
        self.last_write = 0xFF # Chip port default state is high.
        self.last_write_es = 0

    def start(self):
        self.out_ann = self.register(srd.OUTPUT_ANN)
        self.out_logic = self.register(srd.OUTPUT_LOGIC)

    def flush(self):
        self.put_logic_states()

    def putx(self, data):
        self.put(self.ss, self.es, self.out_ann, data)

    def put_logic_states(self):
        if (self.es > self.last_write_es):
            data = bytes([self.last_write])
            self.put(self.last_write_es, self.es, self.out_logic, [0, data])
            self.last_write_es = self.es

    def handle_io(self, b):
        if self.state == 'READ DATA':
            operation = ['Outputs read', 'R']
            if b != self.last_write:
                self.putx([2, ['Warning: read value and last write value '
                               '(%02X) are different' % self.last_write]])
        else:
            operation = ['Outputs set', 'W']
            self.put_logic_states()
            self.last_write = b

        self.putx([1, [operation[0] + ': %02X' % b,
                       operation[1] + ': %02X' % b]])

    def check_correct_chip(self, addr):
        if addr != 0x25:
            self.putx([2, ['Warning: I²C slave 0x%02X not a PCA9571 '
                           'compatible chip.' % addr]])
            return False
        return True

    def decode(self, ss, es, data):
        cmd, databyte = data
        self.ss, self.es = ss, es

        # State machine.
        if cmd in ('ACK', 'BITS'): # Discard 'ACK' and 'BITS'.
            pass
        elif cmd in ('START', 'START REPEAT'): # Start a communication.
            self.state = 'GET SLAVE ADDR'
        elif cmd in ('NACK', 'STOP'): # Reset the state machine.
            self.state = 'IDLE'
        elif cmd in ('ADDRESS READ', 'ADDRESS WRITE'):
            if ((self.state == 'GET SLAVE ADDR') and
                    self.check_correct_chip(databyte)):
                if cmd == 'ADDRESS READ':
                    self.state = 'READ DATA'
                else:
                    self.state = 'WRITE DATA'
            else:
                self.state = 'IDLE'
        elif cmd in ('DATA READ', 'DATA WRITE'):
            if self.state in ('READ DATA', 'WRITE DATA'):
                self.handle_io(databyte)
            else:
                self.state = 'IDLE'
