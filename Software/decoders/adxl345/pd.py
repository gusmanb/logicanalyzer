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
from common.srdhelper import SrdIntEnum
from .lists import *

WORD_SIZE = 8

class Channel():
    MISO, MOSI = range(2)

class Operation():
    READ, WRITE = range(2)

class BitType():
    ENABLE = {1: ['Enable %s', 'En %s', '%s '], 0: ['Disable %s', 'Dis %s', '!%s '],}
    SOURCE = {1: ['Involve %s', 'Inv %s', '%s'], 0: ['Not involve %s', 'Not inv %s', '!%s'],}
    INTERRUPT = {1: ['INT2 %s', 'I2: %s '], 0: ['INT1 %s', 'I1:%s '],}
    AC_DC = {1: ['%s ac', 'ac'], 0: ['%s dc', 'dc'],}
    UNUSED = {1: ['N/A'], 0: ['N/A'],}
    OTHER = 0

class Bit():
    def __init__(self, name, type, values=None):
        self.value = 0
        self.name = name
        self.type = type
        self.values = values

    def set_value(self, value):
        self.value = value

    def get_bit_annotation(self):
        if self.type == BitType.OTHER:
            annotation = self.values[self.value].copy()
        else:
            annotation = self.type[self.value].copy()

        for index in range(len(annotation)):
            if '%s' in annotation[index]:
                annotation[index] = str(annotation[index] % self.name)
        return annotation

Ann = SrdIntEnum.from_str('Ann', 'READ WRITE MB REG_ADDRESS REG_DATA WARNING')

St = SrdIntEnum.from_str('St', 'IDLE ADDRESS_BYTE DATA')

class Decoder(srd.Decoder):
    api_version = 3
    id = 'adxl345'
    name = 'ADXL345'
    longname = 'Analog Devices ADXL345'
    desc = 'Analog Devices ADXL345 3-axis accelerometer.'
    license = 'gplv2+'
    inputs = ['spi']
    outputs = []
    tags = ['IC', 'Sensor']
    annotations = (
        ('read', 'Read'),
        ('write', 'Write'),
        ('mb', 'Multiple bytes'),
        ('reg-address', 'Register address'),
        ('reg-data', 'Register data'),
        ('warning', 'Warning'),
    )
    annotation_rows = (
        ('reg', 'Registers', (Ann.READ, Ann.WRITE, Ann.MB, Ann.REG_ADDRESS)),
        ('data', 'Data', (Ann.REG_DATA, Ann.WARNING)),
    )

    def __init__(self):
        self.reset()

    def reset(self):
        self.mosi, self.miso = [], []
        self.reg = []
        self.operation = None
        self.address = 0
        self.data = -1
        self.state = St.IDLE
        self.ss, self.es = -1, -1
        self.samples_per_bit = 0

    def start(self):
        self.out_ann = self.register(srd.OUTPUT_ANN)

    def putx(self, data):
        self.put(self.ss, self.es, self.out_ann, data)

    def putb(self, data, index):
        start = self.ss + (self.samples_per_bit * index)
        self.put(start, start + self.samples_per_bit, self.out_ann, data)

    def putbs(self, data, start_index, stop_index):
        start_index = self.reverse_bit_index(start_index, WORD_SIZE)
        stop_index = self.reverse_bit_index(stop_index, WORD_SIZE)
        start = self.ss + (self.samples_per_bit * start_index)
        stop = start + (self.samples_per_bit * (stop_index - start_index + 1))
        self.put(start, stop, self.out_ann, data)

    def handle_reg_with_scaling_factor(self, data, factor, name, unit, error_msg):
        if data == 0 and error_msg is not None:
            self.putx([Ann.WARNING, error_msg])
        else:
            result = (data * factor) / 1000
            self.putx([Ann.REG_DATA, ['%s: %f %s' % (name, result, unit), '%f %s' % (result, unit)]])

    def handle_reg_bit_msg(self, bit, index, en_msg, dis_msg):
        self.putb([Ann.REG_DATA, [en_msg if bit else dis_msg]], index)

    def interpret_bits(self, data, bits):
        bits_values = []
        for offset in range(8):
            bits_values.insert(0, (data & (1 << offset)) >> offset)

        for index in range(len(bits)):
            if bits[index] is None:
                continue
            bit = bits[index]
            bit.set_value(bits_values[index])
            self.putb([Ann.REG_DATA, bit.get_bit_annotation()], index)

        return list(reversed(bits_values))

    def reverse_bit_index(self, index, word_size):
        return word_size - index - 1

    def get_decimal_number(self, bits, start_index, stop_index):
        number = 0
        interval = range(start_index, stop_index + 1, 1)
        for index, offset in zip(interval, range(len(interval))):
            bit = bits[index]
            number = number | (bit << offset)
        return number

    def get_axis_value(self, data, axis):
        if self.data != - 1:
            data <<= 8
            self.data |= data
            self.put(self.start_index, self.es, self.out_ann,
                [Ann.REG_DATA, ['%s: 0x%04X' % (axis, self.data), str(data)]])
            self.data = -1
        else:
            self.putx([Ann.REG_DATA, [str(data)]])

    def handle_reg_0x1d(self, data):
        self.handle_reg_with_scaling_factor(data, 62.5, 'Threshold', 'g',
            error_messages['undesirable'])

    def handle_reg_0x1e(self, data):
        self.handle_reg_with_scaling_factor(data, 15.6, 'OFSX', 'g', None)

    def handle_reg_0x1f(self, data):
        self.handle_reg_with_scaling_factor(data, 15.6, 'OFSY', 'g', None)

    def handle_reg_0x20(self, data):
        self.handle_reg_with_scaling_factor(data, 15.6, 'OFSZ', 'g', None)

    def handle_reg_0x21(self, data):
        self.handle_reg_with_scaling_factor(data, 0.625, 'Duration', 's',
            error_messages['dis_single_double'])

    def handle_reg_0x22(self, data):
        self.handle_reg_with_scaling_factor(data, 1.25, 'Latency', 's',
            error_messages['dis_double'])

    def handle_reg_0x23(self, data):
        self.handle_reg_with_scaling_factor(data, 1.25, 'Window', 's',
            error_messages['dis_double'])

    def handle_reg_0x24(self, data):
        self.handle_reg_0x1d(data)

    def handle_reg_0x25(self, data):
        self.handle_reg_0x1d(data)

    def handle_reg_0x26(self, data):
        self.handle_reg_with_scaling_factor(data, 1000, 'Time', 's',
            error_messages['interrupt'])

    def handle_reg_0x27(self, data):
        bits = [Bit('ACT', BitType.AC_DC),
                Bit('ACT_X', BitType.ENABLE),
                Bit('ACT_Y', BitType.ENABLE),
                Bit('ACT_Z', BitType.ENABLE),
                Bit('INACT', BitType.AC_DC),
                Bit('INACT_X', BitType.ENABLE),
                Bit('INACT_Y', BitType.ENABLE),
                Bit('INACT_Z', BitType.ENABLE)]
        self.interpret_bits(data, bits)

    def handle_reg_0x28(self, data):
        self.handle_reg_0x1d(data)

    def handle_reg_0x29(self, data):
        self.handle_reg_with_scaling_factor(data, 5, 'Time', 's',
            error_messages['undesirable'])

    def handle_reg_0x2a(self, data):
        bits = [Bit('', BitType.UNUSED),
                Bit('', BitType.UNUSED),
                Bit('', BitType.UNUSED),
                Bit('', BitType.UNUSED),
                Bit('', BitType.OTHER, {1: ['Suppressed', 'Suppr', 'S'],
                    0: ['Unsuppressed', 'Unsuppr', 'Uns'],}),
                Bit('TAP_X', BitType.ENABLE),
                Bit('TAP_Y', BitType.ENABLE),
                Bit('TAP_Z', BitType.ENABLE)]
        self.interpret_bits(data, bits)

    def handle_reg_0x2b(self, data):
        bits = [Bit('', BitType.UNUSED),
                Bit('ACT_X', BitType.SOURCE),
                Bit('ACT_Y', BitType.SOURCE),
                Bit('ACT_Z', BitType.SOURCE),
                Bit('', BitType.OTHER, {1: ['Asleep', 'Asl'],
                    0: ['Not asleep', 'Not asl', '!Asl'],}),
                Bit('TAP_X', BitType.SOURCE),
                Bit('TAP_Y', BitType.SOURCE),
                Bit('TAP_Z', BitType.SOURCE)]
        self.interpret_bits(data, bits)

    def handle_reg_0x2c(self, data):
        bits = [Bit('', BitType.UNUSED),
                Bit('', BitType.UNUSED),
                Bit('', BitType.UNUSED),
                Bit('', BitType.OTHER, {1: ['Reduce power', 'Reduce pw', 'Red pw'], 0: ['Normal operation', 'Normal op', 'Norm op'],})]
        bits_values = self.interpret_bits(data, bits)

        start_index, stop_index = 0, 3
        rate = self.get_decimal_number(bits_values, start_index, stop_index)
        self.putbs([Ann.REG_DATA, ['%f' % rate_code[rate]]], stop_index, start_index)

    def handle_reg_0x2d(self, data):
        bits = [Bit('', BitType.UNUSED),
                Bit('', BitType.UNUSED),
                Bit('', BitType.OTHER, {1: ['Link'], 0: ['Unlink'], }),
                Bit('AUTO_SLEEP', BitType.ENABLE),
                Bit('', BitType.OTHER, {1: ['Measurement mode', 'Measurement', 'Meas'], 0: ['Standby mode', 'Standby'], }),
                Bit('', BitType.OTHER, {1: ['Sleep mode', 'Sleep', 'Slp'], 0: ['Normal mode', 'Normal', 'Nrm'],})]
        bits_values = self.interpret_bits(data, bits)

        start_index, stop_index = 0, 1
        wakeup = self.get_decimal_number(bits_values, start_index, stop_index)
        frequency = 2 ** (~wakeup & 0x03)
        self.putbs([Ann.REG_DATA, ['%d Hz' % frequency]], stop_index, start_index)

    def handle_reg_0x2e(self, data):
        bits = [Bit('DATA_READY', BitType.ENABLE),
                Bit('SINGLE_TAP', BitType.ENABLE),
                Bit('DOUBLE_TAP', BitType.ENABLE),
                Bit('Activity', BitType.ENABLE),
                Bit('Inactivity', BitType.ENABLE),
                Bit('FREE_FALL', BitType.ENABLE),
                Bit('Watermark', BitType.ENABLE),
                Bit('Overrun', BitType.ENABLE)]
        self.interpret_bits(data, bits)

    def handle_reg_0x2f(self, data):
        bits = [Bit('DATA_READY', BitType.INTERRUPT),
                Bit('SINGLE_TAP', BitType.INTERRUPT),
                Bit('DOUBLE_TAP', BitType.INTERRUPT),
                Bit('Activity', BitType.INTERRUPT),
                Bit('Inactivity', BitType.INTERRUPT),
                Bit('FREE_FALL', BitType.INTERRUPT),
                Bit('Watermark', BitType.INTERRUPT),
                Bit('Overrun', BitType.INTERRUPT)]
        self.interpret_bits(data, bits)

    def handle_reg_0x30(self, data):
        bits = [Bit('DATA_READY', BitType.SOURCE),
                Bit('SINGLE_TAP', BitType.SOURCE),
                Bit('DOUBLE_TAP', BitType.SOURCE),
                Bit('Activity', BitType.SOURCE),
                Bit('Inactivity', BitType.SOURCE),
                Bit('FREE_FALL', BitType.SOURCE),
                Bit('Watermark', BitType.SOURCE),
                Bit('Overrun', BitType.SOURCE)]
        self.interpret_bits(data, bits)

    def handle_reg_0x31(self, data):
        bits = [Bit('SELF_TEST', BitType.ENABLE),
                Bit('', BitType.OTHER, {1: ['3-wire SPI', '3-SPI'], 0: ['4-wire SPI', '4-SPI'],}),
                Bit('', BitType.OTHER, {1: ['INT ACT LOW', 'INT LOW'], 0: ['INT ACT HIGH', 'INT HIGH'],}),
                Bit('', BitType.UNUSED),
                Bit('', BitType.OTHER, {1: ['Full resolution', 'Full res'], 0: ['10-bit mode', '10-bit'],}),
                Bit('', BitType.OTHER, {1: ['MSB mode', 'MSB'], 0: ['LSB mode', 'LSB'],})]
        bits_values = self.interpret_bits(data, bits)

        start_index, stop_index = 0, 1
        range_g = self.get_decimal_number(bits_values, start_index, stop_index)
        result = 2 ** (range_g + 1)
        self.putbs([Ann.REG_DATA, ['+/-%d g' % result]], stop_index, start_index)

    def handle_reg_0x32(self, data):
        self.data = data
        self.putx([Ann.REG_DATA, [str(data)]])

    def handle_reg_0x33(self, data):
        self.get_axis_value(data, 'X')

    def handle_reg_0x34(self, data):
        self.handle_reg_0x32(data)

    def handle_reg_0x35(self, data):
        self.get_axis_value(data, 'Y')

    def handle_reg_0x36(self, data):
        self.handle_reg_0x32(data)

    def handle_reg_0x37(self, data):
        self.get_axis_value(data, 'Z')

    def handle_reg_0x38(self, data):
        bits = [None,
                None,
                Bit('', BitType.OTHER, {1: ['Trig-INT2', 'INT2'], 0: ['Trig-INT1', 'INT1'], })]
        bits_values = self.interpret_bits(data, bits)

        start_index, stop_index = 6, 7
        fifo = self.get_decimal_number(bits_values, start_index, stop_index)
        self.putbs([Ann.REG_DATA, [fifo_modes[fifo]]], stop_index, start_index)

        start_index, stop_index = 0, 4
        samples = self.get_decimal_number(bits_values, start_index, stop_index)
        self.putbs([Ann.REG_DATA, ['Samples: %d' % samples, '%d' % samples]], stop_index, start_index)

    def handle_reg_0x39(self, data):
        bits = [Bit('', BitType.OTHER, {1: ['Triggered', 'Trigg'], 0: ['Not triggered', 'Not trigg'],}),
                Bit('', BitType.UNUSED)]
        bits_values = self.interpret_bits(data, bits)

        start_index, stop_index = 0, 5
        entries = self.get_decimal_number(bits_values, start_index, stop_index)
        self.putbs([Ann.REG_DATA, ['Entries: %d' % entries, '%d' % entries]], stop_index, start_index)

    def get_bit(self, channel):
        if (channel == Channel.MOSI and self.mosi is None) or \
                (channel == Channel.MISO and self.miso is None):
            raise Exception('No available data')

        mosi_bit, miso_bit = 0, 0
        if self.miso is not None:
            if len(self.mosi) < 0:
                raise Exception('No available data')
            miso_bit = self.miso.pop(0)
        if self.miso is not None:
            if len(self.miso) < 0:
                raise Exception('No available data')
            mosi_bit = self.mosi.pop(0)

        if channel == Channel.MOSI:
            return mosi_bit
        return miso_bit

    def decode(self, ss, es, data):
        ptype = data[0]

        if ptype == 'CS-CHANGE':
            cs_old, cs_new = data[1:]
            if cs_old is not None and cs_old == 1 and cs_new == 0:
                self.ss, self.es = ss, es
                self.state = St.ADDRESS_BYTE
            else:
                self.state = St.IDLE

        elif ptype == 'BITS':
            if data[1] is not None:
                self.mosi = list(reversed(data[1]))
            if data[2] is not None:
                self.miso = list(reversed(data[2]))

            if self.mosi is None and self.miso is None:
                return

            if self.state == St.ADDRESS_BYTE:
                # OPERATION BIT
                op_bit = self.get_bit(Channel.MOSI)
                self.put(op_bit[1], op_bit[2], self.out_ann,
                    [Ann.READ if op_bit[0] else Ann.WRITE, operations[op_bit[0]]])
                self.operation = Operation.READ if op_bit[0] else Operation.WRITE
                # MULTIPLE-BYTE BIT
                mb_bit = self.get_bit(Channel.MOSI)
                self.put(mb_bit[1], mb_bit[2], self.out_ann, [Ann.MB, number_bytes[mb_bit[0]]])

                # REGISTER 6-BIT ADDRESS
                self.address = 0
                start_sample = self.mosi[0][1]
                addr_bit = []
                for i in range(6):
                    addr_bit = self.get_bit(Channel.MOSI)
                    self.address |= addr_bit[0]
                    self.address <<= 1
                self.address >>= 1
                self.put(start_sample, addr_bit[2], self.out_ann,
                    [Ann.REG_ADDRESS, ['ADDRESS: 0x%02X' % self.address, 'ADDR: 0x%02X'
                    % self.address, '0x%02X' % self.address]])
                self.ss = -1
                self.state = St.DATA

            elif self.state == St.DATA:
                self.reg.extend(self.mosi if self.operation == Operation.WRITE else self.miso)

                self.mosi, self.miso = [], []
                if self.ss == -1:
                    self.ss, self.es = self.reg[0][1], es
                    self.samples_per_bit = self.reg[0][2] - self.ss

                if len(self.reg) < 8:
                    return
                else:
                    reg_value = 0
                    reg_bit = []
                    for offset in range(7, -1, -1):
                        reg_bit = self.reg.pop(0)

                        mask = reg_bit[0] << offset
                        reg_value |= mask

                    if self.address < 0x00 or self.address > 0x39:
                        return

                    if self.address in [0x32, 0x34, 0x36]:
                        self.start_index = self.ss

                    if 0x1D > self.address >= 0x00:
                        self.put(self.ss, reg_bit[2], self.out_ann, [Ann.REG_ADDRESS, [str(self.address)]])
                        self.put(self.ss, reg_bit[2], self.out_ann, [Ann.REG_DATA, [str(reg_value)]])
                    else:
                        self.put(self.ss, reg_bit[2], self.out_ann, [Ann.REG_ADDRESS, registers[self.address]])
                        handle_reg = getattr(self, 'handle_reg_0x%02x' % self.address)
                        handle_reg(reg_value)

                    self.reg = []
                    self.address += 1
                    self.ss = -1
