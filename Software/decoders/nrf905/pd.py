##
## This file is part of the libsigrokdecode project.
##
## Copyright (C) 2020 Jorge Solla Rubiales <jorgesolla@gmail.com>
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
from common.srdhelper import SrdIntEnum

CFG_REGS = {
    0: [{'name': 'CH_NO', 'stbit': 7, 'nbits': 8}],
    1: [
        {'name': 'AUTO_RETRAN', 'stbit': 5, 'nbits': 1,
         'opts': {0: 'No retransmission', 1: 'Retransmission of data packet'}},
        {'name': 'RX_RED_PWR', 'stbit': 4, 'nbits': 1,
         'opts': {0: 'Normal operation', 1: 'Reduced power'}},
        {'name': 'PA_PWR', 'stbit': 3, 'nbits': 2,
         'opts': {0: '-10 dBm', 1: '-2 dBm', 2: '+6 dBm', 3: '+10 dBm'}},
        {'name': 'HFREQ_PLL', 'stbit': 1, 'nbits': 1,
         'opts': {0: '433 MHz', 1: '868 / 915 MHz'}},
        {'name': 'CH_NO_8', 'stbit': 0, 'nbits': 1},
    ],
    2: [
        {'name': 'TX_AFW (TX addr width)', 'stbit': 6, 'nbits': 3},
        {'name': 'RX_AFW (RX addr width)', 'stbit': 2, 'nbits': 3},
    ],
    3: [{'name': 'RW_PW (RX payload width)', 'stbit': 5, 'nbits': 6}],
    4: [{'name': 'TX_PW (TX payload width)', 'stbit': 5, 'nbits': 6}],
    5: [{'name': 'RX_ADDR_0', 'stbit': 7, 'nbits': 8}],
    6: [{'name': 'RX_ADDR_1', 'stbit': 7, 'nbits': 8}],
    7: [{'name': 'RX_ADDR_2', 'stbit': 7, 'nbits': 8}],
    8: [{'name': 'RX_ADDR_3', 'stbit': 7, 'nbits': 8}],
    9: [
        {'name': 'CRC_MODE', 'stbit': 7, 'nbits': 1,
         'opts': {0: '8 CRC check bit', 1: '16 CRC check bit'}},
        {'name': 'CRC_EN', 'stbit': 6, 'nbits': 1,
         'opts': {0: 'Disabled', 1: 'Enabled'}},
        {'name': 'XOR', 'stbit': 5, 'nbits': 3,
         'opts': {0: '4 MHz', 1: '8 MHz', 2: '12 MHz',
                  3: '16 MHz', 4: '20 MHz'}},
        {'name': 'UP_CLK_EN', 'stbit': 2, 'nbits': 1,
         'opts': {0: 'No external clock signal avail.',
                  1: 'External clock signal enabled'}},
        {'name': 'UP_CLK_FREQ', 'stbit': 1, 'nbits': 2,
         'opts': {0: '4 MHz', 1: '2 MHz', 2: '1 MHz', 3: '500 kHz'}},
    ],
}

CHN_CFG = [
    {'name': 'PA_PWR', 'stbit': 3, 'nbits': 2,
     'opts': {0: '-10 dBm', 1: '-2 dBm', 2: '+6 dBm', 3: '+10 dBm'}},
    {'name': 'HFREQ_PLL', 'stbit': 1, 'nbits': 1,
     'opts': {0: '433 MHz', 1: '868 / 915 MHz'}},
]

STAT_REG = [
    {'name': 'AM', 'stbit': 7, 'nbits': 1},
    {'name': 'DR', 'stbit': 5, 'nbits': 1},
]

Ann = SrdIntEnum.from_str('Ann', 'CMD REG_WR REG_RD TX RX RESP WARN')

class Decoder(srd.Decoder):
    api_version = 3
    id = 'nrf905'
    name = 'nRF905'
    longname = 'Nordic Semiconductor nRF905'
    desc = '433/868/933MHz transceiver chip.'
    license = 'mit'
    inputs = ['spi']
    outputs = []
    tags = ['IC', 'Wireless/RF']
    annotations = (
        ('cmd', 'Command sent to the device'),
        ('reg-write', 'Config register written to the device'),
        ('reg-read', 'Config register read from the device'),
        ('tx-data', 'Payload sent to the device'),
        ('rx-data', 'Payload read from the device'),
        ('resp', 'Response to commands received from the device'),
        ('warning', 'Warning'),
    )
    annotation_rows = (
        ('commands', 'Commands', (Ann.CMD,)),
        ('responses', 'Responses', (Ann.RESP,)),
        ('registers', 'Registers', (Ann.REG_WR, Ann.REG_RD)),
        ('tx', 'Transmitted data', (Ann.TX,)),
        ('rx', 'Received data', (Ann.RX,)),
        ('warnings', 'Warnings', (Ann.WARN,)),
    )

    def __init__(self):
        self.ss_cmd, self.es_cmd = 0, 0
        self.cs_asserted = False
        self.reset()

    def reset(self):
        self.mosi_bytes, self.miso_bytes = [], []
        self.cmd_samples = {'ss': 0, 'es': 0}

    def start(self):
        self.out_ann = self.register(srd.OUTPUT_ANN)

    def extract_bits(self, byte, start_bit, num_bits):
        begin = 7 - start_bit
        end = begin + num_bits
        if begin < 0 or end > 8:
            return 0
        binary = format(byte, '08b')[begin:end]
        return int(binary, 2)

    def extract_vars(self, reg_vars, reg_value):
        # Iterate all vars on current register.
        data = ''
        for var in reg_vars:
            var_value = self.extract_bits(reg_value, var['stbit'], var['nbits'])
            data += var['name'] + ' = ' + str(var_value)
            opt = ''

            # If var has options, just add the option meaning.
            if 'opts' in var:
                opt = var['opts'].get(var_value, 'unknown')
                data += ' (' + opt + ')'

            # Add var separator.
            if reg_vars.index(var) != len(reg_vars) - 1:
                data += ' | '
        return data

    def parse_config_register(self, addr, value, is_write):
        reg_value = value[0]
        data = 'CFG_REG[' + hex(addr) + '] -> '

        # Get register vars for this register.
        if addr in CFG_REGS:
            reg_vars = CFG_REGS[addr]
        else:
            # Invalid register address.
            self.put(value[1], value[2],
                     self.out_ann, [Ann.WARN, ['Invalid reg. addr']])
            return

        data += self.extract_vars(reg_vars, reg_value)

        ann = Ann.REG_WR if is_write else Ann.REG_RD
        self.put(value[1], value[2], self.out_ann, [ann, [data]])

    def parse_config_registers(self, addr, registers, is_write):
        i = 0
        while i < len(registers):
            reg_addr = i + addr
            if reg_addr <= 9:
                self.parse_config_register(reg_addr, registers[i], is_write)
            i += 1

    def dump_cmd_bytes(self, prefix, cmd_bytes, ann):
        ss, es = cmd_bytes[1][1], 0
        data = ''
        for byte in cmd_bytes[1:]:
            data += format(byte[0], '02X') + ' '
            es = byte[2]
        self.put(ss, es, self.out_ann, [ann, [prefix + data]])

    def handle_WC(self):
        start_addr = self.mosi_bytes[0][0] & 0x0F
        if start_addr > 9:
            return
        self.parse_config_registers(start_addr, self.mosi_bytes[1:], True)

    def handle_RC(self):
        start_addr = self.mosi_bytes[0][0] & 0x0F
        if start_addr > 9:
            return
        self.parse_config_registers(start_addr, self.miso_bytes[1:], False)

    def handle_WTP(self):
        self.dump_cmd_bytes('Write TX payload.: ', self.mosi_bytes, Ann.TX)

    def handle_RTP(self):
        self.dump_cmd_bytes('Read TX payload: ', self.miso_bytes, Ann.RESP)

    def handle_WTA(self):
        self.dump_cmd_bytes('Write TX addr: ', self.mosi_bytes, Ann.REG_WR)

    def handle_RTA(self):
        self.dump_cmd_bytes('Read TX addr: ', self.miso_bytes, Ann.RESP)

    def handle_RRP(self):
        self.dump_cmd_bytes('Read RX payload: ', self.miso_bytes, Ann.RX)

    def handle_CC(self):
        cmd, dta = self.mosi_bytes[0], self.mosi_bytes[1]
        channel = ((cmd[0] & 0x01) << 8) + dta
        data = self.extract_vars(CHN_CFG, cmd[0])
        data += '| CHN = ' + str(channel)
        self.put(self.mosi_bytes[0][1], self.mosi_bytes[1][2],
                 self.out_ann, [Ann.REG_WR, [data]])

    def handle_STAT(self):
        status = 'STAT = ' + self.extract_vars(STAT_REG, self.miso_bytes[0][0])
        self.put(self.miso_bytes[0][1], self.miso_bytes[0][2],
                 self.out_ann, [Ann.REG_RD, [status]])

    def process_cmd(self):
        cmd, cmd_name, cmd_hnd = '', '', None

        for byte in self.mosi_bytes:
            cmd += hex(byte[0]) + ' '

        cmd = self.mosi_bytes[0][0]

        if (cmd & 0xF0) == 0x00:
            cmd_name, cmd_hnd = 'CMD: W_CONFIG (WC)', self.handle_WC
        elif (cmd & 0xF0) == 0x10:
            cmd_name, cmd_hnd = 'CMD: R_CONFIG (RC)', self.handle_RC
        elif cmd == 0x20:
            cmd_name, cmd_hnd = 'CMD: W_TX_PAYLOAD (WTP)', self.handle_WTP
        elif cmd == 0x21:
            cmd_name, cmd_hnd = 'CMD: R_TX_PAYLOAD (RTP)', self.handle_RTP
        elif cmd == 0x22:
            cmd_name, cmd_hnd = 'CMD: W_TX_ADDRESS (WTA)', self.handle_WTA
        elif cmd == 0x23:
            cmd_name, cmd_hnd = 'CMD: R_TX_ADDRESS (RTA)', self.handle_RTA
        elif cmd == 0x24:
            cmd_name, cmd_hnd = 'CMD: R_RX_PAYLOAD (RRP)', self.handle_RRP
        elif (cmd & 0xF0 == 0x80):
            cmd_name, cmd_hnd = 'CMD: CHANNEL_CONFIG (CC)', self.handle_CC

        # Report command name.
        self.put(self.cmd_samples['ss'], self.cmd_samples['es'],
                 self.out_ann, [Ann.CMD, [cmd_name]])

        # Handle status byte.
        self.handle_STAT()

        # Handle command.
        if cmd_hnd is not None:
            cmd_hnd()

    def set_cs_status(self, sample, asserted):
        if self.cs_asserted == asserted:
            return

        if asserted:
            self.cmd_samples['ss'] = sample
            self.cmd_samples['es'] = -1
        else:
            self.cmd_samples['es'] = sample

        self.cs_asserted = asserted

    def decode(self, ss, es, data):
        ptype, data1, data2 = data

        if ptype == 'CS-CHANGE':
            if data1 is None and data2 is None:
                self.requirements_met = False
                raise ChannelError('CS# pin required.')

            if data1 is None and data2 == 0:
                self.set_cs_status(ss, True)

            elif data1 is None and data2 == 1:
                self.set_cs_status(ss, False)

            elif data1 == 1 and data2 == 0:
                self.set_cs_status(ss, True)

            elif data1 == 0 and data2 == 1:
                self.set_cs_status(ss, False)
                if len(self.mosi_bytes):
                    self.process_cmd()
                    self.reset()

        elif ptype == 'DATA':
            # Ignore traffic if CS is not asserted.
            if self.cs_asserted is False:
                return

            mosi, miso = data1, data2
            if miso is None or mosi is None:
                raise ChannelError('Both MISO and MOSI pins required.')

            self.mosi_bytes.append((mosi, ss, es))
            self.miso_bytes.append((miso, ss, es))
