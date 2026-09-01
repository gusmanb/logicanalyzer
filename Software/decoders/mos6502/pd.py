##
## This file is part of the libsigrokdecode project.
##
## Copyright (C) 2017 David Banks <dave@hoglet.com>
## Update 2025 by Emile <emile@vandelogt.nl>: most of David's code rewritten. 
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
from .tables import addr_mode_len_map, instr_table, AddrMode
import string

class Ann:
    DATA, FETCH, OP1, OP2, MEMRD, MEMWR, INSTR, ADDR = range(8)

class Pin:
    D0, D7 = 0, 7
    A0, A15 = 8, 23
    RNW, SYNC, PHI2, RDYN, IRQN, NMIN, RSTN = range(24, 31) 
    
class Cycle:
    FETCH, OP1, OP2, MEMRD, MEMWR, DATA = range(6)

cycle_to_ann_map = {
    Cycle.FETCH: Ann.FETCH, # Fetch opcode
    Cycle.OP1:   Ann.OP1,   # Read 1st databyte
    Cycle.OP2:   Ann.OP2,   # Read 2nd databyte (MSB)
    Cycle.MEMRD: Ann.MEMRD, # Read byte
    Cycle.MEMWR: Ann.MEMWR, # Write byte
    Cycle.DATA:  Ann.DATA,  # Dummy cycle 
}

cycle_to_name_map = {
    Cycle.FETCH: 'Fetch',
    Cycle.OP1:   'Op1',
    Cycle.OP2:   'Op2',
    Cycle.MEMRD: 'Read',
    Cycle.MEMWR: 'Write',
    Cycle.DATA:  'Data',
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
    id       = 'mos6502'
    name     = 'MOS6502'
    longname = 'Mostek 6502 CPU'
    desc     = 'Mostek 6502 microprocessor disassembly.'
    license  = 'gplv3+'
    inputs   = ['logic']
    outputs  = []
    tags     = ['Retro computing'] 
    channels = tuple({
            'id': 'd%d' % i,
            'name': 'D%d' % i,
            'desc': 'Data bus line %d' % i
            } for i in range(8)
    ) + tuple({
        'id': 'a%d' % i,
        'name': 'A%d' % i,
        'desc': 'Address bus line %d' % i
        } for i in range(16)
    ) + (
        {'id': 'rnw', 'name': 'RNW', 'desc': 'Memory read or write'},
        {'id': 'sync', 'name': 'SYNC', 'desc': 'Sync - opcode fetch'},
        {'id': 'phi2', 'name': 'PHI2', 'desc': 'Phi2 clock, falling edge active'},
    )
    optional_channels = (
         {'id': 'rdy',  'name': 'RDY',  'desc': 'Ready, allows for wait states'},
         {'id': 'irq',  'name': 'IRQN', 'desc': 'Maskable interrupt'},
         {'id': 'nmi',  'name': 'NMIN', 'desc': 'Non-maskable interrupt'},
         {'id': 'rst',  'name': 'RSTN', 'desc': 'Reset'},
    )
    annotations = (
        ('data',   'Data bus'),
        ('fetch',  'Fetch opcode'),
        ('op1',    'Operand 1'),
        ('op2',    'Operand 2'),
        ('memrd',  'Memory Read'),
        ('memwr',  'Memory Write'),
        ('instr',  'Instruction'),
        ('addr',   'Address'),
    )
    annotation_rows = (
        ('databus', 'Data bus', (Ann.DATA,)),
        ('cycle', 'Cycle', (Ann.FETCH, Ann.OP1, Ann.OP2, Ann.MEMRD, Ann.MEMWR)),
        ('instructions', 'Instructions', (Ann.INSTR,)),
        ('addrbus', 'Address bus', (Ann.ADDR,)),
    )

    def __init__(self):
        self.reset()

    def reset(self):
        self.prev_phi2 = 0  # previous value of PHI2
        self.prev_sync = 0  # previous value of SYNC
        self.samplenum_phi2_f = 0 # samplenr of PHI2 falling edge
        self.samplenum_phi2_r = 0 # samplenr of PHI2 rising edge
        self.samplenum_dasm_start = 0 # samplenr at start of disassembly
        
    def start(self):
        self.out_ann    = self.register(srd.OUTPUT_ANN)
        self.ann_data   = None

    def decode(self):
        opcount = 0
        cycle = Cycle.MEMRD
        cycle_pr = cycle # cycle to Print
        op = '???'
        len = 0
        samplenum_datab = 0 # samplenumber at start of databyte print
        samplenum_datae = 0 # samplenumber at end   of databyte print
        rnw_phi2_r      = 0 # RNW line at rising edge of PHI2
        
        while True:
            pins = self.wait()

            bus_data = reduce_bus(pins[Pin.D0:Pin.D7+1])  # databus as byte
            bus_addr = reduce_bus(pins[Pin.A0:Pin.A15+1]) # addressbus as word

            phi2f = 0  # 1 = PHI2 falling edge detected
            phi2r = 0  # 1 = PHI2 rising edge detected
            if pins[Pin.PHI2] == 1:
                if self.prev_phi2 == 0:
                    phi2r = 1 # PHI2 rising edge detected
                    self.samplenum_phi2_r = self.samplenum
                    rnw_phi2_r = pins[Pin.RNW] # RNW line at rising-edge of PHI2
                    # Print addressbus from PHI2 falling-edge to rising-edge
                    self.put(self.samplenum_phi2_f, self.samplenum, self.out_ann, [Ann.ADDR, [format(bus_addr, '04X')]])
            else: # PHI2 == 0
                if self.prev_phi2 == 1: 
                    phi2f = 1 # PHI2 falling edge detected
                    self.samplenum_phi2_f = self.samplenum
                    # Print databus from PHI2 rising-edge to falling-edge
                    self.put(self.samplenum_phi2_r, self.samplenum, self.out_ann, [Ann.DATA, [format(bus_data, '02X')]])
                    samplenum_datab = self.samplenum_phi2_r # needed for printing cycle-type
                    samplenum_datae = self.samplenum
                    if cycle == Cycle.DATA: # determine if the DATA cycle is READ or WRITE
                        if rnw_phi2_r == 1:
                            cycle_pr = Cycle.MEMRD # READ databyte
                        else:
                            cycle_pr = Cycle.MEMWR # write databyte
                    else: 
                        cycle_pr = cycle  # save cycle for print of addressing mode
            self.prev_phi2 = pins[Pin.PHI2] # save PHI2 clock
            
            if pins[Pin.SYNC] == 0 and self.prev_sync == 1:
                syncf = 1 # 1 = SYNC falling edge detected
            else:
                syncf = 0

            if pins[Pin.SYNC] == 1 and self.prev_sync == 0:
                syncr = 1 # 1 = SYNC rising edge detected
            else:
                syncr = 0
            self.prev_sync = pins[Pin.SYNC] # save SYNC value
 
            # ------------------------------------------------------------------------------------------------------------
            # SYNC = 1 if 6502 is doing an opcode FETCH, PHI rising edge is start of data-read
            # ------------------------------------------------------------------------------------------------------------
            if pins[Pin.SYNC] == 1 and phi2r == 1:
                cycle   = Cycle.FETCH
                op1     = 0                                # value of 1st databyte
                op2     = 0                                # value of 2nd databyte (MSB)
                self.samplenum_dasm_start = self.samplenum # start disassembly text from this samplenumber

            elif phi2f == 1: # from now on, read all data at falling-edge of PHI2
                # ------------------------------------------------------------------------------------------------------------
                # Read databyte op1 following the Fetch opcode byte, PHI2 falling edge is end of data-read
                # ------------------------------------------------------------------------------------------------------------
                if cycle == Cycle.FETCH:
                    instr   = instr_table[bus_data]            # read instruction record
                    op      = instr[0]                         # instruction mnemonic text
                    mode    = instr[1]                         # instruction addressing mode
                    len     = addr_mode_len_map[mode]          # instruction number of bytes [1,2,3]
                    opcount = len - 1                          # counter for number of bytes read, is now 0, 1 or 2
                    if opcount > 0:
                        cycle = Cycle.OP1
                        opcount -= 1 # decrement #databytes to read, is now 0 or 1
                    else:
                        cycle = Cycle.DATA # next cycle is a data-byte cycle

                # ------------------------------------------------------------------------------------------------------------
                # Three situations are possible:
                # opcount == 1: 3-byte instruction, read op2 databyte
                # opcount == 0: a) 2-byte instruction with only 2 clock-cycles (Immediate mode and branches not taken mode).
                #                  print the disassembly here, since the next PHI2 falling edge will be an opcode Fetch.
                #               b) 2-byte instruction with 3 or more clock-cycles. The disassembly is printed anyway, but
                #                  will be overwritten by the disassembly print at the rising edge of SYNC
                # ------------------------------------------------------------------------------------------------------------
                elif cycle == Cycle.OP1:
                    if mode == AddrMode.BRA: 
                        op1 = signed_byte(bus_data)
                    else: 
                        op1 = bus_data
                    if opcount > 0: # 3-byte instruction
                        cycle = Cycle.OP2
                        opcount -= 1
                    else: # 2-byte instruction
                        cycle = Cycle.DATA # next cycle is a data-byte cycle
                        if mode == AddrMode.BRA:
                            self.put(self.samplenum_dasm_start, self.samplenum, self.out_ann, [Ann.INSTR, [op.format(op1+bus_addr)]])
                        else:
                            self.put(self.samplenum_dasm_start, self.samplenum, self.out_ann, [Ann.INSTR, [op.format(op1)]])
            
                # ------------------------------------------------------------------------------------------------------------
                # Last databyte read of a 3-byte instruction. There's only one 3-byte instruction with only 3 clock-cycles, JMP $nnnn.
                # Print the disassembly here, since the next PHI2 falling edge will be an opcode Fetch. Note that for other 3-byte
                # instructions, this disassembly print is overwritten by the disassembly print at the rising edge of SYNC.
                # ------------------------------------------------------------------------------------------------------------
                elif cycle == Cycle.OP2:
                    op2 = bus_data     # read databyte
                    cycle = Cycle.DATA # next cycle is a data-byte cycle
                    self.put(self.samplenum_dasm_start, self.samplenum, self.out_ann, [Ann.INSTR, [op.format(op1 + 256*op2)]])
                
                # ------------------------------------------------------------------------------------------------------------
                # The rising edge of SYNC (which also coincides with the falling edge of PHI2) indicates the start of 
                # the next Fetch operation, so this is a good time to print the disassembly-text of the current instruction.
                # ------------------------------------------------------------------------------------------------------------
                elif syncr == 1:   # rising edge of SYNC
                    if len == 1:   # 1-byte instructions
                        self.put(self.samplenum_dasm_start, self.samplenum, self.out_ann, [Ann.INSTR, [op]])
                    elif len == 2: # 2-byte instructions 
                        if mode == AddrMode.BRA: # branch instructions with relative addressing
                            self.put(self.samplenum_dasm_start, self.samplenum, self.out_ann, [Ann.INSTR, [op.format(op1+bus_addr)]])
                        else:      # all other 2-byte instructions
                            self.put(self.samplenum_dasm_start, self.samplenum, self.out_ann, [Ann.INSTR, [op.format(op1)]])
                    elif len == 3: # 3-byte instructions
                        self.put(self.samplenum_dasm_start, self.samplenum, self.out_ann, [Ann.INSTR, [op.format(op1 + 256*op2)]])

                # ------------------------------------------------------------------------------------------------------------
                # Following a Fetch, OP1 or OP2 cycle, one or more byte read/write cycles may follow. They are identified here,
                # but they don't influence the disassembly-text anymore.
                # ------------------------------------------------------------------------------------------------------------
                else: # not a Fetch, Op1 or Op2 byte, so it is a DATA byte
                    cycle = Cycle.DATA # next cycle is a data-byte cycle
                    
            # elif phi2f == 1:
            
            # ------------------------------------------------------------------------------------------------------------
            # Separate from above decoding, the cycle-type is printed here at the same time-stamp as the databyte
            # ------------------------------------------------------------------------------------------------------------
            if phi2f == 1:
                self.put(samplenum_datab, samplenum_datae, self.out_ann, [cycle_to_ann_map[cycle_pr], [cycle_to_name_map[cycle_pr]]]) 
        # while True:
    # def decode(self):
