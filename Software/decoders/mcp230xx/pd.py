##
## This file is part of the libsigrokdecode project.
##
## Copyright (C) 2019 Benedikt Otto <benedikt_o@web.de>
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

STATE_IDLE, STATE_ADDR, STATE_DATA, STATE_READ_ADDR, STATE_READ_DATA, STATE_STOP = range(6)
UNKNOWN, READ, WRITE = range(3)

registers = ["IODIR", "IPOL", "GPINTEN", "DEFVAL", "INTCON", "IOCON", "GPPU", "INTF", "INTCAP", "GPIO", "OLAT"]
registers_mcp23017_bank0 = {i: (registers[i // 2] + "AB"[i % 2] if registers[i // 2] != "IOCON" else "IOCON") for i in range(22)}

registers_mcp23017_bank1 = {(i + 5 if i > 11 else i): (registers[i % 11] + "AB"[i // 11] if registers[i % 11] != "IOCON" else "IOCON") for i in range(22)}

registers_mcp23008 = {i: registers[i] for i in range(11)}

class Decoder(srd.Decoder):
    api_version = 3
    id = 'mcp230xx'
    name = 'MCP230XX'
    longname = 'Microchip MCP230XX'
    desc = 'MCP230XX 8/16-bit I²C output expanders.'
    license = 'gplv2+'
    inputs = ['i2c']
    outputs = []
    tags = ['IC']

    options = (
        {'id': 'type', 'desc': 'Type', 'default': 'MCP23017',
            'values': ('MCP23008', 'MCP23017')},
    )

    annotations = (
        ('register_read', 'Register read'),
        ('register_write', 'Register write'),
        ('warning', 'Warning'),
    )
    annotation_rows = (
        ('regs', 'Registers', (0, 1)),
        ('warnings', 'Warnings', (2,)),
    )

    def __init__(self):
        self.reset()

    def reset(self):
        self.state = STATE_IDLE
        self.iocon = 0
        self.iocon_set = False

    def start(self):
        self.out_ann = self.register(srd.OUTPUT_ANN)

    def get_registers(self):
        if self.options["type"] == "MCP23008":
            return registers_mcp23008
        else:
            return registers_mcp23017_bank1 if self.iocon & (1 << 7) else registers_mcp23017_bank0

    def putx(self, ss, es, data):
        self.put(ss, es, self.out_ann, data)

    def checkAddress(self, ss, es, address):
        if not address in range(0x20, 0x27 + 1):
            self.putx(ss, es, [2, ['Address %02X not MCP230XX compatible' % address]])

    def handleRead(self, register, data):
        if len(data) >= 1:
            register = register[0]
            for d in data:
                registers = self.get_registers()
                if not register in registers:
                    self.putx(d[1], d[2], [2, ['Error: Register %d not accessible' %register]])
                    if not self.iocon_set:
                        self.iocon = d[0]
                else:
                    register_name = registers[register]
                    if register_name == "IOCON":
                        self.iocon = d[0]
                        self.iocon_set = True
                    self.putx(d[1], d[2], [0, ["Read %s: %02X" % (register_name, d[0]), "R%02X" % d[0]]])
                register += 1

    def handleWrite(self, data):
        if len(data) >= 2:
            register = data[0][0]
            for d in data[1:]:
                registers = self.get_registers()
                if not register in registers:
                    self.putx(d[1], d[2], [2, ['Error: Register %d not accessible' %register]])
                    if not self.iocon_set:
                        self.iocon = d[0]
                else:
                    register_name = registers[register]
                    if register_name == "IOCON":
                        self.iocon = d[0]
                        self.iocon_set = True
                    self.putx(d[1], d[2], [1, ["Write %s: %02X" % (register_name, d[0]), "W%02X" % d[0]]])
                register += 1

    def decode(self, ss, es, data):
        cmd, databyte = data
        if cmd in ('ACK', 'NACK', 'BITS'): # Discard 'ACK' and 'BITS'.
            return
        if self.state == STATE_IDLE and cmd == 'START':
            self.state = STATE_ADDR
            self.dataWrite = []
            self.dataRead = []
        elif self.state == STATE_ADDR and cmd == 'ADDRESS WRITE':
            self.state = STATE_DATA
            self.checkAddress(ss, es, databyte)
        elif self.state in [STATE_DATA, STATE_STOP] and cmd == 'DATA WRITE':
            self.state = STATE_STOP
            self.dataWrite.append((databyte, ss, es))
        elif self.state == STATE_STOP and cmd == "START REPEAT":
            self.state = STATE_READ_ADDR
        elif self.state == STATE_READ_ADDR and cmd == "ADDRESS READ":
            self.state = STATE_READ_DATA
            self.checkAddress(ss, es, databyte)
        elif self.state in [STATE_READ_DATA, STATE_STOP] and cmd == 'DATA READ':
            self.state = STATE_STOP
            self.dataRead.append((databyte, ss, es))
        elif self.state == STATE_STOP and cmd == 'STOP':
            self.state = STATE_IDLE
            if len(self.dataRead) > 0 and len(self.dataWrite) == 1:
                self.handleRead(self.dataWrite[0], self.dataRead)
            elif len(self.dataWrite) > 0 and self.dataRead == []:
                self.handleWrite(self.dataWrite)
