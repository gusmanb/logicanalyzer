##
## This file is part of the libsigrokdecode project.
##
## Copyright (C) 2012-2020 Uwe Hermann <uwe@hermann-uwe.de>
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
from common.srdhelper import SrdStrEnum

'''
OUTPUT_PYTHON format:

Packet:
[<ptype>, <pdata>]

<ptype>:
 - 'NEW STATE': <pdata> is the new state of the JTAG state machine.
   Valid values: 'TEST-LOGIC-RESET', 'RUN-TEST/IDLE', 'SELECT-DR-SCAN',
   'CAPTURE-DR', 'SHIFT-DR', 'EXIT1-DR', 'PAUSE-DR', 'EXIT2-DR', 'UPDATE-DR',
   'SELECT-IR-SCAN', 'CAPTURE-IR', 'SHIFT-IR', 'EXIT1-IR', 'PAUSE-IR',
   'EXIT2-IR', 'UPDATE-IR'.
 - 'IR TDI': Bitstring that was clocked into the IR register.
 - 'IR TDO': Bitstring that was clocked out of the IR register.
 - 'DR TDI': Bitstring that was clocked into the DR register.
 - 'DR TDO': Bitstring that was clocked out of the DR register.

All bitstrings are a list consisting of two items. The first is a sequence
of '1' and '0' characters (the right-most character is the LSB. Example:
'01110001', where 1 is the LSB). The second item is a list of ss/es values
for each bit that is in the bitstring.
'''

s = 'TEST-LOGIC-RESET RUN-TEST/IDLE \
     SELECT-DR-SCAN CAPTURE-DR UPDATE-DR PAUSE-DR SHIFT-DR EXIT1-DR EXIT2-DR \
     SELECT-IR-SCAN CAPTURE-IR UPDATE-IR PAUSE-IR SHIFT-IR EXIT1-IR EXIT2-IR'
St = SrdStrEnum.from_str('St', s)

jtag_states = [s.value for s in St]

class Decoder(srd.Decoder):
    api_version = 3
    id = 'jtag'
    name = 'JTAG'
    longname = 'Joint Test Action Group (IEEE 1149.1)'
    desc = 'Protocol for testing, debugging, and flashing ICs.'
    license = 'gplv2+'
    inputs = ['logic']
    outputs = ['jtag']
    tags = ['Debug/trace']
    channels = (
        {'id': 'tdi',  'name': 'TDI',  'desc': 'Test data input'},
        {'id': 'tdo',  'name': 'TDO',  'desc': 'Test data output'},
        {'id': 'tck',  'name': 'TCK',  'desc': 'Test clock'},
        {'id': 'tms',  'name': 'TMS',  'desc': 'Test mode select'},
    )
    optional_channels = (
        {'id': 'trst', 'name': 'TRST#', 'desc': 'Test reset'},
        {'id': 'srst', 'name': 'SRST#', 'desc': 'System reset'},
        {'id': 'rtck', 'name': 'RTCK',  'desc': 'Return clock signal'},
    )
    annotations = tuple([tuple([s.lower(), s]) for s in jtag_states]) + ( \
        ('bit-tdi', 'Bit (TDI)'),
        ('bit-tdo', 'Bit (TDO)'),
        ('bitstring-tdi', 'Bitstring (TDI)'),
        ('bitstring-tdo', 'Bitstring (TDO)'),
    )
    annotation_rows = (
        ('bits-tdi', 'Bits (TDI)', (16,)),
        ('bits-tdo', 'Bits (TDO)', (17,)),
        ('bitstrings-tdi', 'Bitstrings (TDI)', (18,)),
        ('bitstrings-tdo', 'Bitstrings (TDO)', (19,)),
        ('states', 'States', tuple(range(15 + 1))),
    )

    def __init__(self):
        self.reset()

    def reset(self):
        # self.state = St.TEST_LOGIC_RESET
        self.state = St.RUN_TEST_IDLE
        self.oldstate = None
        self.bits_tdi = []
        self.bits_tdo = []
        self.bits_samplenums_tdi = []
        self.bits_samplenums_tdo = []
        self.ss_item = self.es_item = None
        self.ss_bitstring = self.es_bitstring = None
        self.saved_item = None
        self.first = True
        self.first_bit = True

    def start(self):
        self.out_python = self.register(srd.OUTPUT_PYTHON)
        self.out_ann = self.register(srd.OUTPUT_ANN)

    def putx(self, data):
        self.put(self.ss_item, self.es_item, self.out_ann, data)

    def putp(self, data):
        self.put(self.ss_item, self.es_item, self.out_python, data)

    def putx_bs(self, data):
        self.put(self.ss_bitstring, self.es_bitstring, self.out_ann, data)

    def putp_bs(self, data):
        self.put(self.ss_bitstring, self.es_bitstring, self.out_python, data)

    def advance_state_machine(self, tms):
        self.oldstate = self.state

        # Intro "tree"
        if self.state == St.TEST_LOGIC_RESET:
            self.state = St.TEST_LOGIC_RESET if (tms) else St.RUN_TEST_IDLE
        elif self.state == St.RUN_TEST_IDLE:
            self.state = St.SELECT_DR_SCAN if (tms) else St.RUN_TEST_IDLE

        # DR "tree"
        elif self.state == St.SELECT_DR_SCAN:
            self.state = St.SELECT_IR_SCAN if (tms) else St.CAPTURE_DR
        elif self.state == St.CAPTURE_DR:
            self.state = St.EXIT1_DR if (tms) else St.SHIFT_DR
        elif self.state == St.SHIFT_DR:
            self.state = St.EXIT1_DR if (tms) else St.SHIFT_DR
        elif self.state == St.EXIT1_DR:
            self.state = St.UPDATE_DR if (tms) else St.PAUSE_DR
        elif self.state == St.PAUSE_DR:
            self.state = St.EXIT2_DR if (tms) else St.PAUSE_DR
        elif self.state == St.EXIT2_DR:
            self.state = St.UPDATE_DR if (tms) else St.SHIFT_DR
        elif self.state == St.UPDATE_DR:
            self.state = St.SELECT_DR_SCAN if (tms) else St.RUN_TEST_IDLE

        # IR "tree"
        elif self.state == St.SELECT_IR_SCAN:
            self.state = St.TEST_LOGIC_RESET if (tms) else St.CAPTURE_IR
        elif self.state == St.CAPTURE_IR:
            self.state = St.EXIT1_IR if (tms) else St.SHIFT_IR
        elif self.state == St.SHIFT_IR:
            self.state = St.EXIT1_IR if (tms) else St.SHIFT_IR
        elif self.state == St.EXIT1_IR:
            self.state = St.UPDATE_IR if (tms) else St.PAUSE_IR
        elif self.state == St.PAUSE_IR:
            self.state = St.EXIT2_IR if (tms) else St.PAUSE_IR
        elif self.state == St.EXIT2_IR:
            self.state = St.UPDATE_IR if (tms) else St.SHIFT_IR
        elif self.state == St.UPDATE_IR:
            self.state = St.SELECT_DR_SCAN if (tms) else St.RUN_TEST_IDLE

    def handle_rising_tck_edge(self, pins):
        (tdi, tdo, tck, tms, trst, srst, rtck) = pins

        # Rising TCK edges always advance the state machine.
        self.advance_state_machine(tms)

        if self.first:
            # Save the start sample and item for later (no output yet).
            self.ss_item = self.samplenum
            self.first = False
        else:
            # Output the saved item (from the last CLK edge to the current).
            self.es_item = self.samplenum
            # Output the old state (from last rising TCK edge to current one).
            self.putx([jtag_states.index(self.oldstate.value), [self.oldstate.value]])
            self.putp(['NEW STATE', self.state.value])

        # Upon SHIFT-*/EXIT1-* collect the current TDI/TDO values.
        if self.oldstate.value.startswith('SHIFT-') or \
           self.oldstate.value.startswith('EXIT1-'):
            if self.first_bit:
                self.ss_bitstring = self.samplenum
                self.first_bit = False
            else:
                self.putx([16, [str(self.bits_tdi[-1])]])
                self.putx([17, [str(self.bits_tdo[-1])]])
                # Use self.samplenum as ES of the previous bit.
                self.bits_samplenums_tdi[-1][1] = self.samplenum
                self.bits_samplenums_tdo[-1][1] = self.samplenum

            self.bits_tdi.append(tdi)
            self.bits_tdo.append(tdo)

            # Use self.samplenum as SS of the current bit.
            self.bits_samplenums_tdi.append([self.samplenum, -1])
            self.bits_samplenums_tdo.append([self.samplenum, -1])

        # Output all TDI/TDO bits if we just switched to UPDATE-*.
        if self.state.value.startswith('UPDATE-'):

            self.es_bitstring = self.samplenum

            t = self.state.value[-2:] + ' TDI'
            self.bits_tdi.reverse()
            self.bits_samplenums_tdi.reverse()
            b = ''.join(map(str, self.bits_tdi[1:]))
            h = ' (0x%x' % int('0b0' + b, 2) + ')'
            s = t + ': ' + b + h + ', ' + str(len(self.bits_tdi[1:])) + ' bits'
            self.putx_bs([18, [s]])
            self.putp_bs([t, [b, self.bits_samplenums_tdi[1:]]])
            self.bits_tdi = []
            self.bits_samplenums_tdi = []

            t = self.state.value[-2:] + ' TDO'
            self.bits_tdo.reverse()
            self.bits_samplenums_tdo.reverse()
            b = ''.join(map(str, self.bits_tdo[1:]))
            h = ' (0x%x' % int('0b0' + b, 2) + ')'
            s = t + ': ' + b + h + ', ' + str(len(self.bits_tdo[1:])) + ' bits'
            self.putx_bs([19, [s]])
            self.putp_bs([t, [b, self.bits_samplenums_tdo[1:]]])
            self.bits_tdo = []
            self.bits_samplenums_tdo = []

            self.first_bit = True

            self.ss_bitstring = self.samplenum

        self.ss_item = self.samplenum

    def decode(self):
        while True:
            # Wait for a rising edge on TCK.
            self.handle_rising_tck_edge(self.wait({2: 'r'}))
