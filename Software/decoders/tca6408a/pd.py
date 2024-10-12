##
## This file is part of the libsigrokdecode project.
##
## Copyright (C) 2012 Uwe Hermann <uwe@hermann-uwe.de>
## Copyright (C) 2013 Matt Ranostay <mranostay@gmail.com>
## Copyright (C) 2014 alberink <alberink@stampfini.org>
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

def logic_channels(num_channels):
    l = []
    for i in range(num_channels):
        l.append(tuple(['p%d' % i, 'P-port input/output %d' % i]))
    return tuple(l)

class Decoder(srd.Decoder):
    api_version = 3
    id = 'tca6408a'
    name = 'TI TCA6408A'
    longname = 'Texas Instruments TCA6408A'
    desc = 'Texas Instruments TCA6408A 8-bit I²C I/O expander.'
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
        self.chip = -1

        self.logic_output_es = 0
        self.logic_value = 0

    def start(self):
        self.out_ann = self.register(srd.OUTPUT_ANN)
        self.out_logic = self.register(srd.OUTPUT_LOGIC)

    def flush(self):
        self.put_logic_states()

    def putx(self, data):
        self.put(self.ss, self.es, self.out_ann, data)

    def put_logic_states(self):
        if (self.es > self.logic_output_es):
            data = bytes([self.logic_value])
            self.put(self.logic_output_es, self.es, self.out_logic, [0, data])
            self.logic_output_es = self.es

    def handle_reg_0x00(self, b):
        self.putx([1, ['State of inputs: %02X' % b]])
        # TODO

    def handle_reg_0x01(self, b):
        self.put_logic_states()
        self.putx([1, ['Outputs set: %02X' % b]])
        self.logic_value = b

    def handle_reg_0x02(self, b):
        self.putx([1, ['Polarity inverted: %02X' % b]])

    def handle_reg_0x03(self, b):
        self.putx([1, ['Configuration: %02X' % b]])

    def handle_write_reg(self, b):
        if b == 0:
            self.putx([0, ['Input port', 'In', 'I']])
        elif b == 1:
            self.putx([0, ['Output port', 'Out', 'O']])
        elif b == 2:
            self.putx([0, ['Polarity inversion register', 'Pol', 'P']])
        elif b == 3:
            self.putx([0, ['Configuration register', 'Conf', 'C']])

    def check_correct_chip(self, addr):
        if addr not in (0x20, 0x21):
            self.putx([2, ['Warning: I²C slave 0x%02X not a TCA6408A '
                           'compatible chip.' % addr]])
            self.state = 'IDLE'

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
            self.chip = databyte
            self.state = 'GET REG ADDR'
        elif self.state == 'GET REG ADDR':
            # Wait for a data write (master selects the slave register).
            if cmd in ('ADDRESS READ', 'ADDRESS WRITE'):
                self.check_correct_chip(databyte)
            if cmd != 'DATA WRITE':
                return
            self.reg = databyte
            self.handle_write_reg(self.reg)
            self.state = 'WRITE IO REGS'
        elif self.state == 'WRITE IO REGS':
            # If we see a Repeated Start here, the master wants to read.
            if cmd == 'START REPEAT':
                self.state = 'READ IO REGS'
                return
            # Otherwise: Get data bytes until a STOP condition occurs.
            if cmd == 'DATA WRITE':
                handle_reg = getattr(self, 'handle_reg_0x%02x' % self.reg)
                handle_reg(databyte)
            elif cmd == 'STOP':
                self.state = 'IDLE'
                self.chip = -1
        elif self.state == 'READ IO REGS':
            # Wait for an address read operation.
            if cmd == 'ADDRESS READ':
                self.state = 'READ IO REGS2'
                self.chip = databyte
                return
        elif self.state == 'READ IO REGS2':
            if cmd == 'DATA READ':
                handle_reg = getattr(self, 'handle_reg_0x%02x' % self.reg)
                handle_reg(databyte)
            elif cmd == 'STOP':
                self.state = 'IDLE'
