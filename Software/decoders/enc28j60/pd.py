##
## This file is part of the libsigrokdecode project.
##
## Copyright (C) 2019 Jiahao Li <reg@ljh.me>
##
## Permission is hereby granted, free of charge, to any person obtaining a copy
## of this software and associated documentation files (the "Software"), to deal
## in the Software without restriction, including without limitation the rights
## to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
## copies of the Software, and to permit persons to whom the Software is
## furnished to do so, subject to the following conditions:
##
## The above copyright notice and this permission notice shall be included in all
## copies or substantial portions of the Software.
##
## THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
## IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
## FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
## AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
## LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
## OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
## SOFTWARE.

import sigrokdecode as srd
from .lists import *

OPCODE_MASK = 0b11100000
REG_ADDR_MASK = 0b00011111

OPCODE_HANDLERS = {
    0b00000000: '_process_rcr',
    0b00100000: '_process_rbm',
    0b01000000: '_process_wcr',
    0b01100000: '_process_wbm',
    0b10000000: '_process_bfs',
    0b10100000: '_process_bfc',
    0b11100000: '_process_src',
}

(ANN_RCR, ANN_RBM, ANN_WCR, ANN_WBM, ANN_BFS, ANN_BFC, ANN_SRC, ANN_DATA,
ANN_REG_ADDR, ANN_WARNING) = range(10)

REG_ADDR_ECON1 = 0x1F
BIT_ECON1_BSEL0 = 0b00000001
BIT_ECON1_BSEL1 = 0b00000010

class Decoder(srd.Decoder):
    api_version = 3
    id = 'enc28j60'
    name = 'ENC28J60'
    longname = 'Microchip ENC28J60'
    desc = 'Microchip ENC28J60 10Base-T Ethernet controller protocol.'
    license = 'mit'
    inputs = ['spi']
    outputs = []
    tags = ['Embedded/industrial', 'Networking']
    annotations = (
        ('rcr', 'Read Control Register'),
        ('rbm', 'Read Buffer Memory'),
        ('wcr', 'Write Control Register'),
        ('wbm', 'Write Buffer Memory'),
        ('bfs', 'Bit Field Set'),
        ('bfc', 'Bit Field Clear'),
        ('src', 'System Reset Command'),
        ('data', 'Data'),
        ('reg-addr', 'Register Address'),
        ('warning', 'Warning'),
    )
    annotation_rows = (
        ('fields', 'Fields', (ANN_DATA, ANN_REG_ADDR)),
        ('commands', 'Commands',
            (ANN_RCR, ANN_RBM, ANN_WCR, ANN_WBM, ANN_BFS, ANN_BFC, ANN_SRC)),
        ('warnings', 'Warnings', (ANN_WARNING,)),
    )

    def __init__(self):
        self.reset()

    def reset(self):
        self.mosi = []
        self.miso = []
        self.ranges = []
        self.cmd_ss = None
        self.cmd_es = None
        self.range_ss = None
        self.range_es = None
        self.active = False
        self.bsel0 = None
        self.bsel1 = None

    def start(self):
        self.out_ann = self.register(srd.OUTPUT_ANN)

    def putc(self, data):
        self.put(self.cmd_ss, self.cmd_es, self.out_ann, data)

    def putr(self, data):
        self.put(self.range_ss, self.range_es, self.out_ann, data)

    def _process_command(self):
        if len(self.mosi) == 0:
            self.active = False
            return

        header = self.mosi[0]
        opcode = header & OPCODE_MASK

        if opcode not in OPCODE_HANDLERS:
            self._put_command_warning("Unknown opcode.")
            self.active = False
            return

        getattr(self, OPCODE_HANDLERS[opcode])()

        self.active = False

    def _get_register_name(self, reg_addr):
        if (self.bsel0 is None) or (self.bsel1 is None):
            # We don't know the bank we're in yet.
            return None
        else:
            bank = (self.bsel1 << 1) + self.bsel0
            return REGS[bank][reg_addr]

    def _put_register_header(self):
        reg_addr = self.mosi[0] & REG_ADDR_MASK
        reg_name = self._get_register_name(reg_addr)

        self.range_ss, self.range_es = self.cmd_ss, self.ranges[1][0]

        if reg_name is None:
            # We don't know the bank we're in yet.
            self.putr([ANN_REG_ADDR, [
                'Reg Bank ? Addr 0x{0:02X}'.format(reg_addr),
                '?:{0:02X}'.format(reg_addr)]])
            self.putr([ANN_WARNING, ['Warning: Register bank not known yet.',
                                     'Warning']])
        else:
            self.putr([ANN_REG_ADDR, ['Reg {0}'.format(reg_name),
                                      '{0}'.format(reg_name)]])

            if (reg_name == '-') or (reg_name == 'Reserved'):
                self.putr([ANN_WARNING, ['Warning: Invalid register accessed.',
                                         'Warning']])

    def _put_data_byte(self, data, byte_index, binary=False):
        self.range_ss = self.ranges[byte_index][0]
        if byte_index == len(self.mosi) - 1:
            self.range_es = self.cmd_es
        else:
            self.range_es = self.ranges[byte_index + 1][0]

        if binary:
            self.putr([ANN_DATA, ['Data 0b{0:08b}'.format(data),
                                  '{0:08b}'.format(data)]])
        else:
            self.putr([ANN_DATA, ['Data 0x{0:02X}'.format(data),
                                  '{0:02X}'.format(data)]])

    def _put_command_warning(self, reason):
        self.putc([ANN_WARNING, ['Warning: {0}'.format(reason), 'Warning']])

    def _process_rcr(self):
        self.putc([ANN_RCR, ['Read Control Register', 'RCR']])

        if (len(self.mosi) != 2) and (len(self.mosi) != 3):
            self._put_command_warning('Invalid command length.')
            return

        self._put_register_header()

        reg_name = self._get_register_name(self.mosi[0] & REG_ADDR_MASK)
        if reg_name is None:
            # We can't tell if we're accessing MAC/MII registers or not
            # Let's trust the user in this case.
            pass
        else:
            if (reg_name[0] == 'M') and (len(self.mosi) != 3):
                self._put_command_warning('Attempting to read a MAC/MII '
                    + 'register without using the dummy byte.')
                return

            if (reg_name[0] != 'M') and (len(self.mosi) != 2):
                self._put_command_warning('Attempting to read a non-MAC/MII '
                                          + 'register using the dummy byte.')
                return

        if len(self.mosi) == 2:
            self._put_data_byte(self.miso[1], 1)
        else:
            self.range_ss, self.range_es = self.ranges[1][0], self.ranges[2][0]
            self.putr([ANN_DATA, ['Dummy Byte', 'Dummy']])
            self._put_data_byte(self.miso[2], 2)

    def _process_rbm(self):
        if self.mosi[0] != 0b00111010:
            self._put_command_warning('Invalid header byte.')
            return

        self.putc([ANN_RBM, ['Read Buffer Memory: Length {0}'.format(
                             len(self.mosi) - 1), 'RBM']])

        for i in range(1, len(self.miso)):
            self._put_data_byte(self.miso[i], i)

    def _process_wcr(self):
        self.putc([ANN_WCR, ['Write Control Register', 'WCR']])

        if len(self.mosi) != 2:
            self._put_command_warning('Invalid command length.')
            return

        self._put_register_header()
        self._put_data_byte(self.mosi[1], 1)

        if self.mosi[0] & REG_ADDR_MASK == REG_ADDR_ECON1:
            self.bsel0 = (self.mosi[1] & BIT_ECON1_BSEL0) >> 0
            self.bsel1 = (self.mosi[1] & BIT_ECON1_BSEL1) >> 1

    def _process_wbm(self):
        if self.mosi[0] != 0b01111010:
            self._put_command_warning('Invalid header byte.')
            return

        self.putc([ANN_WBM, ['Write Buffer Memory: Length {0}'.format(
                             len(self.mosi) - 1), 'WBM']])

        for i in range(1, len(self.mosi)):
            self._put_data_byte(self.mosi[i], i)

    def _process_bfc(self):
        self.putc([ANN_BFC, ['Bit Field Clear', 'BFC']])

        if len(self.mosi) != 2:
            self._put_command_warning('Invalid command length.')
            return

        self._put_register_header()
        self._put_data_byte(self.mosi[1], 1, True)

        if self.mosi[0] & REG_ADDR_MASK == REG_ADDR_ECON1:
            if self.mosi[1] & BIT_ECON1_BSEL0:
                self.bsel0 = 0
            if self.mosi[1] & BIT_ECON1_BSEL1:
                self.bsel1 = 0

    def _process_bfs(self):
        self.putc([ANN_BFS, ['Bit Field Set', 'BFS']])

        if len(self.mosi) != 2:
            self._put_command_warning('Invalid command length.')
            return

        self._put_register_header()
        self._put_data_byte(self.mosi[1], 1, True)

        if self.mosi[0] & REG_ADDR_MASK == REG_ADDR_ECON1:
            if self.mosi[1] & BIT_ECON1_BSEL0:
                self.bsel0 = 1
            if self.mosi[1] & BIT_ECON1_BSEL1:
                self.bsel1 = 1

    def _process_src(self):
        self.putc([ANN_SRC, ['System Reset Command', 'SRC']])

        if len(self.mosi) != 1:
            self._put_command_warning('Invalid command length.')
            return

        self.bsel0 = 0
        self.bsel1 = 0

    def decode(self, ss, es, data):
        ptype, data1, data2 = data

        if ptype == 'CS-CHANGE':
            new_cs = data2

            if new_cs == 0:
                self.active = True
                self.cmd_ss = ss
                self.mosi = []
                self.miso = []
                self.ranges = []
            elif new_cs == 1:
                if self.active:
                    self.cmd_es = es
                    self._process_command()
        elif ptype == 'DATA':
            mosi, miso = data1, data2

            self.mosi.append(mosi)
            self.miso.append(miso)
            self.ranges.append((ss, es))
