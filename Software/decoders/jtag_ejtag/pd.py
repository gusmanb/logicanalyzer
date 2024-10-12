##
## This file is part of the libsigrokdecode project.
##
## Copyright (C) 2018 Vladislav Ivanov <vlad.ivanov@lab-systems.ru>
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
from common.srdhelper import bin2int, SrdIntEnum

class Instruction(object):
    IDCODE            = 0x01
    IMPCODE           = 0x03
    ADDRESS           = 0x08
    DATA              = 0x09
    CONTROL           = 0x0A
    ALL               = 0x0B
    EJTAGBOOT         = 0x0C
    NORMALBOOT        = 0x0D
    FASTDATA          = 0x0E
    TCBCONTROLA       = 0x10
    TCBCONTROLB       = 0x11
    TCBDATA           = 0x12
    TCBCONTROLC       = 0x13
    PCSAMPLE          = 0x14
    TCBCONTROLD       = 0x15
    TCBCONTROLE       = 0x16

class State(object):
    RESET             = 0
    DEVICE_ID         = 1
    IMPLEMENTATION    = 2
    DATA              = 3
    ADDRESS           = 4
    CONTROL           = 5
    FASTDATA          = 6
    PC_SAMPLE         = 7
    BYPASS            = 8

class ControlReg(object):
    PRACC             = (1 << 18)
    PRNW              = (1 << 19)

class Ann(SrdIntEnum):
    INSTRUCTION       = 0
    REGISTER          = 1
    CONTROL_FIELD_IN  = 10
    CONTROL_FIELD_OUT = 11
    PRACC             = 12

ejtag_insn = {
    0x00: ['Free',        'Boundary scan'],
    0x01: ['IDCODE',      'Select Device Identification (ID) register'],
    0x02: ['Free',        'Boundary scan'],
    0x03: ['IMPCODE',     'Select Implementation register'],
    0x08: ['ADDRESS',     'Select Address register'],
    0x09: ['DATA',        'Select Data register'],
    0x0A: ['CONTROL',     'Select EJTAG Control register'],
    0x0B: ['ALL',         'Select the Address, Data and EJTAG Control registers'],
    0x0C: ['EJTAGBOOT',   'Fetch code from the debug exception vector after reset'],
    0x0D: ['NORMALBOOT',  'Execute the reset handler after reset'],
    0x0E: ['FASTDATA',    'Select the Data and Fastdata registers'],
    0x0F: ['Reserved',    'Reserved'],
    0x10: ['TCBCONTROLA', 'Select the control register TCBTraceControl'],
    0x11: ['TCBCONTROLB', 'Selects trace control block register B'],
    0x12: ['TCBDATA',     'Access the registers specified by TCBCONTROLB'],
    0x13: ['TCBCONTROLC', 'Select trace control block register C'],
    0x14: ['PCSAMPLE',    'Select the PCsample register'],
    0x15: ['TCBCONTROLD', 'Select trace control block register D'],
    0x16: ['TCBCONTROLE', 'Select trace control block register E'],
    0x17: ['FDC',         'Select Fast Debug Channel'],
    0x1C: ['Free',        'Boundary scan'],
}

ejtag_reg = {
    0x00: 'RESET',
    0x01: 'DEVICE_ID',
    0x02: 'IMPLEMENTATION',
    0x03: 'DATA',
    0x04: 'ADDRESS',
    0x05: 'CONTROL',
    0x06: 'FASTDATA',
    0x07: 'PC_SAMPLE',
    0x08: 'BYPASS',
}

ejtag_control_reg = [
    [31, 31, 'Rocc', [
        # Read
        ['No reset ocurred', 'Reset ocurred'],
        # Write
        ['Acknowledge reset', 'No effect'],
    ]],
    [30, 29, 'Psz', [
        ['Access: byte', 'Access: halfword', 'Access: word', 'Access: triple'],
    ]],
    [23, 23, 'VPED', [
        ['VPE disabled', 'VPE enabled'],
    ]],
    [22, 22, 'Doze', [
        ['Processor is not in low-power mode', 'Processor is in low-power mode'],
    ]],
    [21, 21, 'Halt', [
        ['Internal system bus clock is running', 'Internal system bus clock is stopped'],
    ]],
    [20, 20, 'Per Rst', [
        ['No peripheral reset applied', 'Peripheral reset applied'],
        ['Deassert peripheral reset', 'Assert peripheral reset'],
    ]],
    [19, 19, 'PRn W', [
        ['Read processor access', 'Write processor access'],
    ]],
    [18, 18, 'Pr Acc', [
        ['No pending processor access', 'Pending processor access'],
        ['Finish processor access', 'Don\'t finish processor access'],
    ]],
    [16, 16, 'Pr Rst', [
        ['No processor reset applied', 'Processor reset applied'],
        ['Deassert processor reset', 'Assert system reset'],
    ]],
    [15, 15, 'Prob En', [
        ['Probe will not serve processor accesses', 'Probe will service processor accesses'],
    ]],
    [14, 14, 'Prob Trap', [
        ['Default location', 'DMSEG fetch'],
        ['Set to default location', 'Set to DMSEG fetch'],
    ]],
    [13, 13, 'ISA On Debug', [
        ['MIPS32/MIPS64 ISA', 'microMIPS ISA'],
        ['Set to MIPS32/MIPS64 ISA', 'Set to microMIPS ISA'],
    ]],
    [12, 12, 'EJTAG Brk', [
        ['No pending debug interrupt', 'Pending debug interrupt'],
        ['No effect', 'Request debug interrupt'],
    ]],
    [3, 3, 'DM', [
        ['Not in debug mode', 'In debug mode'],
    ]],
]

ejtag_state_map = {
    Instruction.IDCODE: State.DEVICE_ID,
    Instruction.IMPCODE: State.IMPLEMENTATION,
    Instruction.DATA: State.DATA,
    Instruction.ADDRESS: State.ADDRESS,
    Instruction.CONTROL: State.CONTROL,
    Instruction.FASTDATA: State.FASTDATA,
}

class RegData(object):
    def __init__(self):
        self.ss = None
        self.es = None
        self.data = None

class LastData(object):
    def __init__(self):
        self.data_in = RegData()
        self.data_out = RegData()

class PraccState(object):
    def reset(self):
        self.address_in = None
        self.address_out = None
        self.data_in = None
        self.data_out = None
        self.write = False
        self.ss = 0
        self.es = 0

    def __init__(self):
        self.reset()

regs_items = {
    'ann': tuple([tuple([s.lower(), s]) for s in list(ejtag_reg.values())]),
    'rows_range': tuple(range(1, 1 + 9)),
}

class Decoder(srd.Decoder):
    api_version = 3
    id = 'jtag_ejtag'
    name = 'JTAG / EJTAG'
    longname = 'Joint Test Action Group / EJTAG (MIPS)'
    desc = 'MIPS EJTAG protocol.'
    license = 'gplv2+'
    inputs = ['jtag']
    outputs = []
    tags = ['Debug/trace']
    annotations = (
        ('instruction', 'Instruction'),
    ) + regs_items['ann'] + (
        ('control_field_in', 'Control field in'),
        ('control_field_out', 'Control field out'),
        ('pracc', 'PrAcc'),
    )
    annotation_rows = (
        ('instructions', 'Instructions', (0,)),
        ('control_fields_in', 'Control fields in', (10,)),
        ('control_fields_out', 'Control fields out', (11,)),
        ('regs', 'Registers', regs_items['rows_range']),
        ('pracc-vals', 'PrAcc', (12,)),
    )

    def __init__(self):
        self.reset()

    def reset(self):
        self.state = State.RESET
        self.pracc_state = PraccState()

    def put_current(self, data):
        self.put(self.ss, self.es, self.out_ann, data)

    def put_at(self, ss: int, es: int, data):
        self.put(ss, es, self.out_ann, data)

    def start(self):
        self.out_ann = self.register(srd.OUTPUT_ANN)

    def select_reg(self, ir_value: int):
        self.state = ejtag_state_map.get(ir_value, State.RESET)

    def parse_pracc(self):
        control_in = bin2int(self.last_data['in']['data'][0])
        control_out = bin2int(self.last_data['out']['data'][0])

        # Check if JTAG master acknowledges a pending PrAcc.
        if not ((not (control_in & ControlReg.PRACC)) and \
                (control_out & ControlReg.PRACC)):
            return

        ss, es = self.pracc_state.ss, self.pracc_state.es
        pracc_write = (control_out & ControlReg.PRNW) != 0

        s = 'PrAcc: '
        s += 'Store' if pracc_write else 'Load/Fetch'

        if pracc_write:
            if self.pracc_state.address_out is not None:
                s += ', A:' + ' 0x{:08X}'.format(self.pracc_state.address_out)
            if self.pracc_state.data_out is not None:
                s += ', D:' + ' 0x{:08X}'.format(self.pracc_state.data_out)
        else:
            if self.pracc_state.address_out is not None:
                s += ', A:' + ' 0x{:08X}'.format(self.pracc_state.address_out)
            if self.pracc_state.data_in is not None:
                s += ', D:' + ' 0x{:08X}'.format(self.pracc_state.data_in)

        self.pracc_state.reset()

        self.put_at(ss, es, [Ann.PRACC, [s]])

    def parse_control_reg(self, ann):
        reg_write = ann == Ann.CONTROL_FIELD_IN
        control_bit_positions = []
        data_select = 'in' if (reg_write) else 'out'

        control_bit_positions = self.last_data[data_select]['data'][1]
        control_data = self.last_data[data_select]['data'][0]

        # Annotate control register fields.
        for field in ejtag_control_reg:
            start_bit = 31 - field[1]
            end_bit = 31 - field[0]
            comment = field[2]
            value_descriptions = []

            if reg_write:
                if len(field[3]) < 2:
                    continue
                value_descriptions = field[3][1]
            else:
                value_descriptions = field[3][0]

            ss = control_bit_positions[start_bit][0]
            es = control_bit_positions[end_bit][1]

            value_str = control_data[end_bit : start_bit + 1]
            value_index = bin2int(value_str)

            short_desc = comment + ': ' + value_str
            long_desc = value_descriptions[value_index] if len(value_descriptions) > value_index else '?'

            self.put_at(ss, es, [ann, [long_desc, short_desc]])

    def check_last_data(self):
        if not hasattr(self, 'last_data'):
            self.last_data = {'in': {}, 'out': {}}

    def handle_fastdata(self, val, ann):
        spracc_write_desc = {
            0: ['0', 'SPrAcc: 0', 'Request completion of Fastdata access'],
            1: ['1', 'SPrAcc: 1', 'No effect'],
        }
        spracc_read_desc = {
            0: ['0', 'SPrAcc: 0', 'Fastdata access failure'],
            1: ['1', 'SPrAcc: 1', 'Successful completion of Fastdata access'],
        }

        bitstring = val[0]
        bit_sample_pos = val[1]
        fastdata_state = bitstring[32]
        data = bin2int(bitstring[0:32])

        fastdata_bit_pos = bit_sample_pos[32]
        data_pos = [bit_sample_pos[31][0], bit_sample_pos[0][1]]

        ss_fastdata, es_fastdata = fastdata_bit_pos
        ss_data, es_data = data_pos

        display_data = [ann, ['0x{:08X}'.format(data)]]
        spracc_display_data = []

        if ann == Ann.CONTROL_FIELD_IN:
            spracc_display_data = [ann, spracc_write_desc[int(fastdata_state)]]
        elif ann == Ann.CONTROL_FIELD_OUT:
            spracc_display_data = [ann, spracc_read_desc[int(fastdata_state)]]

        self.put_at(ss_fastdata, es_fastdata, spracc_display_data)
        self.put_at(ss_data, es_data, display_data)

    def handle_dr_tdi(self, val):
        value = bin2int(val[0])
        self.check_last_data()
        self.last_data['in'] = {'ss': self.ss, 'es': self.es, 'data': val}

        self.pracc_state.ss, self.pracc_state.es = self.ss, self.es

        if self.state == State.ADDRESS:
            self.pracc_state.address_in = value
        elif self.state == State.DATA:
            self.pracc_state.data_in = value
        elif self.state == State.FASTDATA:
            self.handle_fastdata(val, Ann.CONTROL_FIELD_IN)

    def handle_dr_tdo(self, val):
        value = bin2int(val[0])
        self.check_last_data()
        self.last_data['out'] = {'ss': self.ss, 'es': self.es, 'data': val}
        if self.state == State.ADDRESS:
            self.pracc_state.address_out = value
        elif self.state == State.DATA:
            self.pracc_state.data_out = value
        elif self.state == State.FASTDATA:
            self.handle_fastdata(val, Ann.CONTROL_FIELD_OUT)

    def handle_ir_tdi(self, val):
        code = bin2int(val[0])
        hexval = '0x{:02X}'.format(code)
        if code in ejtag_insn:
            # Format instruction name.
            insn = ejtag_insn[code]
            s_short = insn[0]
            s_long = insn[0] + ': ' + insn[1] + ' (' + hexval + ')'
            # Display it and select data register.
            self.put_current([Ann.INSTRUCTION, [s_long, s_short]])
        else:
            self.put_current([Ann.INSTRUCTION, [hexval, 'IR TDI ({})'.format(hexval)]])
        self.select_reg(code)

    def handle_new_state(self, new_state):
        if new_state != 'UPDATE-DR' or not hasattr(self, 'last_data'):
            return

        if self.state == State.RESET:
            return

        reg_name = ejtag_reg[self.state]
        ann_index = Ann.REGISTER + self.state
        display_data = [ann_index, [reg_name]]
        self.put_at(self.last_data['in']['ss'], self.last_data['in']['es'], display_data)

        if self.state == State.CONTROL:
            control_bit_positions = self.last_data['in']['data'][1]
            bit_count = len(control_bit_positions)
            # Check if control register data length is correct.
            if bit_count != 32:
                error_display = [Ann.REGISTER, ['Error: length != 32']]
                self.put_at(self.last_data['in']['ss'], self.last_data['in']['es'], error_display)
                return
            self.parse_control_reg(Ann.CONTROL_FIELD_IN)
            self.parse_control_reg(Ann.CONTROL_FIELD_OUT)
            self.parse_pracc()

    def decode(self, ss: int, es: int, data):
        cmd, val = data
        self.ss, self.es = ss, es

        if cmd == 'IR TDI':
            self.handle_ir_tdi(val)
        elif cmd == 'DR TDI':
            self.handle_dr_tdi(val)
        elif cmd == 'DR TDO':
            self.handle_dr_tdo(val)
        elif cmd == 'NEW STATE':
            self.handle_new_state(val)
