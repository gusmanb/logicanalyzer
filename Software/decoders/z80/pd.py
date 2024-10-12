##
## This file is part of the libsigrokdecode project.
##
## Copyright (C) 2014 Daniel Elstner <daniel.kitta@gmail.com>
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
from functools import reduce
from .tables import instr_table_by_prefix
import string

class Ann:
    ADDR, MEMRD, MEMWR, IORD, IOWR, INSTR, ROP, WOP, WARN = range(9)
class Row:
    ADDRBUS, DATABUS, INSTRUCTIONS, OPERANDS, WARNINGS = range(5)
class Pin:
    D0, D7 = 0, 7
    M1, RD, WR, MREQ, IORQ = range(8, 13)
    A0, A15 = 13, 28
class Cycle:
    NONE, MEMRD, MEMWR, IORD, IOWR, FETCH, INTACK = range(7)

# Provide custom format type 'H' for hexadecimal output
# with leading decimal digit (assembler syntax).
class AsmFormatter(string.Formatter):
    def format_field(self, value, format_spec):
        if format_spec.endswith('H'):
            result = format(value, format_spec[:-1] + 'X')
            return result if result[0] in string.digits else '0' + result
        else:
            return format(value, format_spec)

formatter = AsmFormatter()

ann_data_cycle_map = {
    Cycle.MEMRD:  Ann.MEMRD,
    Cycle.MEMWR:  Ann.MEMWR,
    Cycle.IORD:   Ann.IORD,
    Cycle.IOWR:   Ann.IOWR,
    Cycle.FETCH:  Ann.MEMRD,
    Cycle.INTACK: Ann.IORD,
}

def reduce_bus(bus):
    if 0xFF in bus:
        return None # unassigned bus channels
    else:
        return reduce(lambda a, b: (a << 1) | b, reversed(bus))

def signed_byte(byte):
    return byte if byte < 128 else byte - 256

class Decoder(srd.Decoder):
    api_version = 3
    id       = 'z80'
    name     = 'Z80'
    longname = 'Zilog Z80 CPU'
    desc     = 'Zilog Z80 microprocessor disassembly.'
    license  = 'gplv3+'
    inputs   = ['logic']
    outputs  = []
    tags     = ['Retro computing']
    channels = tuple({
            'id': 'd%d' % i,
            'name': 'D%d' % i,
            'desc': 'Data bus line %d' % i
            } for i in range(8)
    ) + (
        {'id': 'm1', 'name': '/M1', 'desc': 'Machine cycle 1'},
        {'id': 'rd', 'name': '/RD', 'desc': 'Memory or I/O read'},
        {'id': 'wr', 'name': '/WR', 'desc': 'Memory or I/O write'},
    )
    optional_channels = (
        {'id': 'mreq', 'name': '/MREQ', 'desc': 'Memory request'},
        {'id': 'iorq', 'name': '/IORQ', 'desc': 'I/O request'},
    ) + tuple({
        'id': 'a%d' % i,
        'name': 'A%d' % i,
        'desc': 'Address bus line %d' % i
        } for i in range(16)
    )
    annotations = (
        ('addr', 'Memory or I/O address'),
        ('memrd', 'Byte read from memory'),
        ('memwr', 'Byte written to memory'),
        ('iord', 'Byte read from I/O port'),
        ('iowr', 'Byte written to I/O port'),
        ('instr', 'Z80 CPU instruction'),
        ('rop', 'Value of input operand'),
        ('wop', 'Value of output operand'),
        ('warning', 'Warning'),
    )
    annotation_rows = (
        ('addrbus', 'Address bus', (Ann.ADDR,)),
        ('databus', 'Data bus', (Ann.MEMRD, Ann.MEMWR, Ann.IORD, Ann.IOWR)),
        ('instructions', 'Instructions', (Ann.INSTR,)),
        ('operands', 'Operands', (Ann.ROP, Ann.WOP)),
        ('warnings', 'Warnings', (Ann.WARN,))
    )

    def __init__(self):
        self.reset()

    def reset(self):
        self.prev_cycle = Cycle.NONE
        self.op_state   = self.state_IDLE

    def start(self):
        self.out_ann    = self.register(srd.OUTPUT_ANN)
        self.bus_data   = None
        self.samplenum  = None
        self.addr_start = None
        self.data_start = None
        self.dasm_start = None
        self.pend_addr  = None
        self.pend_data  = None
        self.ann_data   = None
        self.ann_dasm   = None
        self.prev_cycle = Cycle.NONE
        self.op_state   = self.state_IDLE
        self.instr_len  = 0

    def decode(self):
        while True:
            # TODO: Come up with more appropriate self.wait() conditions.
            pins = self.wait()
            cycle = Cycle.NONE
            if pins[Pin.MREQ] != 1: # default to asserted
                if pins[Pin.RD] == 0:
                    cycle = Cycle.FETCH if pins[Pin.M1] == 0 else Cycle.MEMRD
                elif pins[Pin.WR] == 0:
                    cycle = Cycle.MEMWR
            elif pins[Pin.IORQ] == 0: # default to not asserted
                if pins[Pin.M1] == 0:
                    cycle = Cycle.INTACK
                elif pins[Pin.RD] == 0:
                    cycle = Cycle.IORD
                elif pins[Pin.WR] == 0:
                    cycle = Cycle.IOWR

            if cycle != Cycle.NONE:
                self.bus_data = reduce_bus(pins[Pin.D0:Pin.D7+1])
            if cycle != self.prev_cycle:
                if self.prev_cycle == Cycle.NONE:
                    self.on_cycle_begin(reduce_bus(pins[Pin.A0:Pin.A15+1]))
                elif cycle == Cycle.NONE:
                    self.on_cycle_end()
                else:
                    self.on_cycle_trans()
            self.prev_cycle = cycle

    def on_cycle_begin(self, bus_addr):
        if self.pend_addr is not None:
            self.put_text(self.addr_start, Ann.ADDR,
                          '{:04X}'.format(self.pend_addr))
        self.addr_start = self.samplenum
        self.pend_addr  = bus_addr

    def on_cycle_end(self):
        self.instr_len += 1
        self.op_state = self.op_state()
        if self.ann_dasm is not None:
            self.put_disasm()
        if self.op_state == self.state_RESTART:
            self.op_state = self.state_IDLE()

        if self.ann_data is not None:
            self.put_text(self.data_start, self.ann_data,
                          '{:02X}'.format(self.pend_data))
        self.data_start = self.samplenum
        self.pend_data  = self.bus_data
        self.ann_data   = ann_data_cycle_map[self.prev_cycle]

    def on_cycle_trans(self):
        self.put_text(self.samplenum - 1, Ann.WARN,
                      'Illegal transition between control states')
        self.pend_addr = None
        self.ann_data  = None
        self.ann_dasm  = None

    def put_disasm(self):
        text = formatter.format(self.mnemonic, r=self.arg_reg, d=self.arg_dis,
                                j=self.arg_dis+self.instr_len, i=self.arg_imm,
                                ro=self.arg_read, wo=self.arg_write)
        self.put_text(self.dasm_start, self.ann_dasm, text)
        self.ann_dasm   = None
        self.dasm_start = self.samplenum

    def put_text(self, ss, ann_idx, ann_text):
        self.put(ss, self.samplenum, self.out_ann, [ann_idx, [ann_text]])

    def state_RESTART(self):
        return self.state_IDLE

    def state_IDLE(self):
        if self.prev_cycle != Cycle.FETCH:
            return self.state_IDLE
        self.want_dis   = 0
        self.want_imm   = 0
        self.want_read  = 0
        self.want_write = 0
        self.want_wr_be = False
        self.op_repeat  = False
        self.arg_dis    = 0
        self.arg_imm    = 0
        self.arg_read   = 0
        self.arg_write  = 0
        self.arg_reg    = ''
        self.mnemonic   = ''
        self.instr_pend = False
        self.read_pend  = False
        self.write_pend = False
        self.dasm_start = self.samplenum
        self.op_prefix  = 0
        self.instr_len  = 0
        if self.bus_data in (0xCB, 0xED, 0xDD, 0xFD):
            return self.state_PRE1
        else:
            return self.state_OPCODE

    def state_PRE1(self):
        if self.prev_cycle != Cycle.FETCH:
            self.mnemonic = 'Prefix not followed by fetch'
            self.ann_dasm = Ann.WARN
            return self.state_RESTART
        self.op_prefix = self.pend_data
        if self.op_prefix in (0xDD, 0xFD):
            if self.bus_data == 0xCB:
                return self.state_PRE2
            if self.bus_data in (0xDD, 0xED, 0xFD):
                return self.state_PRE1
        return self.state_OPCODE

    def state_PRE2(self):
        if self.prev_cycle != Cycle.MEMRD:
            self.mnemonic = 'Missing displacement'
            self.ann_dasm = Ann.WARN
            return self.state_RESTART
        self.op_prefix = (self.op_prefix << 8) | self.pend_data
        return self.state_PREDIS

    def state_PREDIS(self):
        if self.prev_cycle != Cycle.MEMRD:
            self.mnemonic = 'Missing opcode'
            self.ann_dasm = Ann.WARN
            return self.state_RESTART
        self.arg_dis = signed_byte(self.pend_data)
        return self.state_OPCODE

    def state_OPCODE(self):
        (table, self.arg_reg) = instr_table_by_prefix[self.op_prefix]
        self.op_prefix = 0
        instruction = table.get(self.pend_data, None)
        if instruction is None:
            self.mnemonic = 'Invalid instruction'
            self.ann_dasm = Ann.WARN
            return self.state_RESTART
        (self.want_dis, self.want_imm, self.want_read, want_write,
                self.op_repeat, self.mnemonic) = instruction
        self.want_write = abs(want_write)
        self.want_wr_be = (want_write < 0)
        if self.want_dis > 0:
            return self.state_POSTDIS
        if self.want_imm > 0:
            return self.state_IMM1
        self.ann_dasm = Ann.INSTR
        if self.want_read > 0 and self.prev_cycle in (Cycle.MEMRD, Cycle.IORD):
            return self.state_ROP1
        if self.want_write > 0 and self.prev_cycle in (Cycle.MEMWR, Cycle.IOWR):
            return self.state_WOP1
        return self.state_RESTART

    def state_POSTDIS(self):
        self.arg_dis = signed_byte(self.pend_data)
        if self.want_imm > 0:
            return self.state_IMM1
        self.ann_dasm = Ann.INSTR
        if self.want_read > 0 and self.prev_cycle in (Cycle.MEMRD, Cycle.IORD):
            return self.state_ROP1
        if self.want_write > 0 and self.prev_cycle in (Cycle.MEMWR, Cycle.IOWR):
            return self.state_WOP1
        return self.state_RESTART

    def state_IMM1(self):
        self.arg_imm = self.pend_data
        if self.want_imm > 1:
            return self.state_IMM2
        self.ann_dasm = Ann.INSTR
        if self.want_read > 0 and self.prev_cycle in (Cycle.MEMRD, Cycle.IORD):
            return self.state_ROP1
        if self.want_write > 0 and self.prev_cycle in (Cycle.MEMWR, Cycle.IOWR):
            return self.state_WOP1
        return self.state_RESTART

    def state_IMM2(self):
        self.arg_imm |= self.pend_data << 8
        self.ann_dasm = Ann.INSTR
        if self.want_read > 0 and self.prev_cycle in (Cycle.MEMRD, Cycle.IORD):
            return self.state_ROP1
        if self.want_write > 0 and self.prev_cycle in (Cycle.MEMWR, Cycle.IOWR):
            return self.state_WOP1
        return self.state_RESTART

    def state_ROP1(self):
        self.arg_read = self.pend_data
        if self.want_read < 2:
            self.mnemonic = '{ro:02X}'
            self.ann_dasm = Ann.ROP
        if self.want_write > 0:
            return self.state_WOP1
        if self.want_read > 1:
            return self.state_ROP2
        if self.op_repeat and self.prev_cycle in (Cycle.MEMRD, Cycle.IORD):
            return self.state_ROP1
        return self.state_RESTART

    def state_ROP2(self):
        self.arg_read |= self.pend_data << 8
        self.mnemonic = '{ro:04X}'
        self.ann_dasm = Ann.ROP
        if self.want_write > 0 and self.prev_cycle in (Cycle.MEMWR, Cycle.IOWR):
            return self.state_WOP1
        return self.state_RESTART

    def state_WOP1(self):
        self.arg_write = self.pend_data
        if self.want_read > 1:
            return self.state_ROP2
        if self.want_write > 1:
            return self.state_WOP2
        self.mnemonic = '{wo:02X}'
        self.ann_dasm = Ann.WOP
        if self.want_read > 0 and self.op_repeat and \
                self.prev_cycle in (Cycle.MEMRD, Cycle.IORD):
            return self.state_ROP1
        return self.state_RESTART

    def state_WOP2(self):
        if self.want_wr_be:
            self.arg_write = (self.arg_write << 8) | self.pend_data
        else:
            self.arg_write |= self.pend_data << 8
        self.mnemonic = '{wo:04X}'
        self.ann_dasm = Ann.WOP
        return self.state_RESTART
