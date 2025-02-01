##
## This file is part of the libsigrokdecode project.
##
## Copyright (C) 2018 Michalis Pappas <mpappas@fastmail.fm>
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

WORD_ADDR_RESET         = 0x00
WORD_ADDR_SLEEP         = 0x01
WORD_ADDR_IDLE          = 0x02
WORD_ADDR_COMMAND       = 0x03

WORD_ADDR = {0x00: 'RESET', 0x01: 'SLEEP', 0x02: 'IDLE', 0x03: 'COMMAND'}

OPCODE_COUNTER          = 0x24
OPCODE_DERIVE_KEY       = 0x1c
OPCODE_DEV_REV          = 0x30
OPCODE_ECDH             = 0x43
OPCODE_GEN_DIG          = 0x15
OPCODE_GEN_KEY          = 0x40
OPCODE_HMAC             = 0x11
OPCODE_CHECK_MAC        = 0x28
OPCODE_LOCK             = 0x17
OPCODE_MAC              = 0x08
OPCODE_NONCE            = 0x16
OPCODE_PAUSE            = 0x01
OPCODE_PRIVWRITE        = 0x46
OPCODE_RANDOM           = 0x1b
OPCODE_READ             = 0x02
OPCODE_SHA              = 0x47
OPCODE_SIGN             = 0x41
OPCODE_UPDATE_EXTRA     = 0x20
OPCODE_VERIFY           = 0x45
OPCODE_WRITE            = 0x12

OPCODES = {
    0x01: 'Pause',
    0x02: 'Read',
    0x08: 'MAC',
    0x11: 'HMAC',
    0x12: 'Write',
    0x15: 'GenDig',
    0x16: 'Nonce',
    0x17: 'Lock',
    0x1b: 'Random',
    0x1c: 'DeriveKey',
    0x20: 'UpdateExtra',
    0x24: 'Counter',
    0x28: 'CheckMac',
    0x30: 'DevRev',
    0x40: 'GenKey',
    0x41: 'Sign',
    0x43: 'ECDH',
    0x45: 'Verify',
    0x46: 'PrivWrite',
    0x47: 'SHA',
}

ZONE_CONFIG             = 0x00
ZONE_OTP                = 0x01
ZONE_DATA               = 0x02

ZONES = {0x00: 'CONFIG', 0x01: 'OTP', 0x02: 'DATA'}

STATUS_SUCCESS          = 0x00
STATUS_CHECKMAC_FAIL    = 0x01
STATUS_PARSE_ERROR      = 0x03
STATUS_EXECUTION_ERROR  = 0x0f
STATUS_READY            = 0x11
STATUS_CRC_COMM_ERROR   = 0xff

STATUS = {
    0x00: 'Command success',
    0x01: 'Checkmac failure',
    0x03: 'Parse error',
    0x0f: 'Execution error',
    0x11: 'Ready',
    0xff: 'CRC / communications error',
}

class Decoder(srd.Decoder):
    api_version = 3
    id = 'atsha204a'
    name = 'ATSHA204A'
    longname = 'Microchip ATSHA204A'
    desc = 'Microchip ATSHA204A family crypto authentication protocol.'
    license = 'gplv2+'
    inputs = ['i2c']
    outputs = []
    tags = ['Security/crypto', 'IC', 'Memory']
    annotations = (
        ('waddr', 'Word address'),
        ('count', 'Count'),
        ('opcode', 'Opcode'),
        ('param1', 'Param1'),
        ('param2', 'Param2'),
        ('data', 'Data'),
        ('crc', 'CRC'),
        ('status', 'Status'),
        ('warning', 'Warning'),
    )
    annotation_rows = (
        ('frame', 'Frames', (0, 1, 2, 3, 4, 5, 6)),
        ('status-vals', 'Status', (7,)),
        ('warnings', 'Warnings', (8,)),
    )

    def __init__(self):
        self.reset()

    def reset(self):
        self.state = 'IDLE'
        self.waddr = self.opcode = -1
        self.ss_block = self.es_block = 0
        self.bytes = []

    def start(self):
        self.out_ann = self.register(srd.OUTPUT_ANN)

    def output_tx_bytes(self):
        b = self.bytes
        if len(b) < 1: # Ignore wakeup.
            return
        self.waddr = b[0][2]
        self.put_waddr(b[0])
        if self.waddr == WORD_ADDR_COMMAND:
            count = b[1][2]
            self.put_count(b[1])
            if len(b) - 1 != count:
                self.put_warning(b[0][0], b[-1][1],
                    'Invalid frame length: Got {}, expecting {} '.format(
                    len(b) - 1, count))
                return
            self.opcode = b[2][2]
            self.put_opcode(b[2])
            self.put_param1(b[3])
            self.put_param2([b[4], b[5]])
            self.put_data(b[6:-2])
            self.put_crc([b[-2], b[-1]])

    def output_rx_bytes(self):
        b = self.bytes
        count = b[0][2]
        self.put_count(b[0])
        if self.waddr == WORD_ADDR_RESET:
            self.put_data([b[1]])
            self.put_crc([b[2], b[3]])
            self.put_status(b[0][0], b[-1][1], b[1][2])
        elif self.waddr == WORD_ADDR_COMMAND:
            if count == 4: # Status / Error.
                self.put_data([b[1]])
                self.put_crc([b[2], b[3]])
                self.put_status(b[0][0], b[-1][1], b[1][2])
            else:
                self.put_data(b[1:-2])
                self.put_crc([b[-2], b[-1]])

    def putx(self, s, data):
        self.put(s[0], s[1], self.out_ann, data)

    def puty(self, s, data):
        self.put(s[0][0], s[1][1], self.out_ann, data)

    def putz(self, ss, es, data):
        self.put(ss, es, self.out_ann, data)

    def put_waddr(self, s):
        self.putx(s, [0, ['Word addr: %s' % WORD_ADDR[s[2]]]])

    def put_count(self, s):
        self.putx(s, [1, ['Count: %s' % s[2]]])

    def put_opcode(self, s):
        self.putx(s, [2, ['Opcode: %s' % OPCODES[s[2]]]])

    def put_param1(self, s):
        op = self.opcode
        if op in (OPCODE_CHECK_MAC, OPCODE_COUNTER, OPCODE_DEV_REV,     \
                  OPCODE_ECDH, OPCODE_GEN_KEY, OPCODE_HMAC, OPCODE_MAC, \
                  OPCODE_NONCE, OPCODE_RANDOM, OPCODE_SHA, OPCODE_SIGN, \
                  OPCODE_VERIFY):
            self.putx(s, [3, ['Mode: %02X' % s[2]]])
        elif op == OPCODE_DERIVE_KEY:
            self.putx(s, [3, ['Random: %s' % s[2]]])
        elif op == OPCODE_PRIVWRITE:
            self.putx(s, [3, ['Encrypted: {}'.format('Yes' if s[2] & 0x40 else 'No')]])
        elif op == OPCODE_GEN_DIG:
            self.putx(s, [3, ['Zone: %s' % ZONES[s[2]]]])
        elif op == OPCODE_LOCK:
            self.putx(s, [3, ['Zone: {}, Summary: {}'.format(
                'DATA/OTP' if s[2] else 'CONFIG',
                'Ignored' if s[2] & 0x80 else 'Used')]])
        elif op == OPCODE_PAUSE:
            self.putx(s, [3, ['Selector: %02X' % s[2]]])
        elif op == OPCODE_READ:
            self.putx(s, [3, ['Zone: {}, Length: {}'.format(ZONES[s[2] & 0x03],
                '32 bytes' if s[2] & 0x90 else '4 bytes')]])
        elif op == OPCODE_WRITE:
            self.putx(s, [3, ['Zone: {}, Encrypted: {}, Length: {}'.format(ZONES[s[2] & 0x03],
                'Yes' if s[2] & 0x40 else 'No', '32 bytes' if s[2] & 0x90 else '4 bytes')]])
        else:
            self.putx(s, [3, ['Param1: %02X' % s[2]]])

    def put_param2(self, s):
        op = self.opcode
        if op == OPCODE_DERIVE_KEY:
            self.puty(s, [4, ['TargetKey: {:02x} {:02x}'.format(s[1][2], s[0][2])]])
        elif op in (OPCODE_COUNTER, OPCODE_ECDH, OPCODE_GEN_KEY, OPCODE_PRIVWRITE, \
                    OPCODE_SIGN, OPCODE_VERIFY):
            self.puty(s, [4, ['KeyID: {:02x} {:02x}'.format(s[1][2], s[0][2])]])
        elif op in (OPCODE_NONCE, OPCODE_PAUSE, OPCODE_RANDOM):
            self.puty(s, [4, ['Zero: {:02x} {:02x}'.format(s[1][2], s[0][2])]])
        elif op in (OPCODE_HMAC, OPCODE_MAC, OPCODE_CHECK_MAC, OPCODE_GEN_DIG):
            self.puty(s, [4, ['SlotID: {:02x} {:02x}'.format(s[1][2], s[0][2])]])
        elif op == OPCODE_LOCK:
            self.puty(s, [4, ['Summary: {:02x} {:02x}'.format(s[1][2], s[0][2])]])
        elif op in (OPCODE_READ, OPCODE_WRITE):
            self.puty(s, [4, ['Address: {:02x} {:02x}'.format(s[1][2], s[0][2])]])
        elif op == OPCODE_UPDATE_EXTRA:
            self.puty(s, [4, ['NewValue: {:02x}'.format(s[0][2])]])
        else:
            self.puty(s, [4, ['-']])

    def put_data(self, s):
        if len(s) == 0:
            return
        op = self.opcode
        if op == OPCODE_CHECK_MAC:
            self.putz(s[0][0], s[31][1], [5, ['ClientChal: %s' % ' '.join(format(i[2], '02x') for i in s[0:32])]])
            self.putz(s[32][0], s[63][1], [5, ['ClientResp: %s' % ' '.join(format(i[2], '02x') for i in s[32:64])]])
            self.putz(s[64][0], s[76][1], [5, ['OtherData: %s' % ' '.join(format(i[2], '02x') for i in s[64:77])]])
        elif op == OPCODE_DERIVE_KEY:
            self.putz(s[0][0], s[31][1], [5, ['MAC: %s' % ' '.join(format(i[2], '02x') for i in s)]])
        elif op == OPCODE_ECDH:
            self.putz(s[0][0], s[31][1], [5, ['Pub X: %s' % ' '.join(format(i[2], '02x') for i in s[0:32])]])
            self.putz(s[32][0], s[63][1], [5, ['Pub Y: %s' % ' '.join(format(i[2], '02x') for i in s[32:64])]])
        elif op in (OPCODE_GEN_DIG, OPCODE_GEN_KEY):
            self.putz(s[0][0], s[3][1], [5, ['OtherData: %s' % ' '.join(format(i[2], '02x') for i in s)]])
        elif op == OPCODE_MAC:
            self.putz(s[0][0], s[31][1], [5, ['Challenge: %s' % ' '.join(format(i[2], '02x') for i in s)]])
        elif op == OPCODE_PRIVWRITE:
            if len(s) > 36: # Key + MAC.
                self.putz(s[0][0], s[-35][1], [5, ['Value: %s' % ' '.join(format(i[2], '02x') for i in s)]])
                self.putz(s[-32][0], s[-1][1], [5, ['MAC: %s' % ' '.join(format(i[2], '02x') for i in s)]])
            else: # Just value.
                self.putz(s[0][0], s[-1][1], [5, ['Value: %s' % ' '.join(format(i[2], '02x') for i in s)]])
        elif op == OPCODE_VERIFY:
            if len(s) >= 64: # ECDSA components (always present)
                self.putz(s[0][0], s[31][1], [5, ['ECDSA R: %s' % ' '.join(format(i[2], '02x') for i in s[0:32])]])
                self.putz(s[32][0], s[63][1], [5, ['ECDSA S: %s' % ' '.join(format(i[2], '02x') for i in s[32:64])]])
            if len(s) == 83: # OtherData (follow ECDSA components in validate / invalidate mode)
                self.putz(s[64][0], s[82][1], [5, ['OtherData: %s' % ' '.join(format(i[2], '02x') for i in s[64:83])]])
            if len(s) == 128: # Public key components (follow ECDSA components in external mode)
                self.putz(s[64][0], s[95][1], [5, ['Pub X: %s' % ' '.join(format(i[2], '02x') for i in s[64:96])]])
                self.putz(s[96][0], s[127][1], [5, ['Pub Y: %s' % ' '.join(format(i[2], '02x') for i in s[96:128])]])
        elif op == OPCODE_WRITE:
            if len(s) > 32: # Value + MAC.
                self.putz(s[0][0], s[-31][1], [5, ['Value: %s' % ' '.join(format(i[2], '02x') for i in s)]])
                self.putz(s[-32][0], s[-1][1], [5, ['MAC: %s' % ' '.join(format(i[2], '02x') for i in s)]])
            else: # Just value.
                self.putz(s[0][0], s[-1][1], [5, ['Value: %s' % ' '.join(format(i[2], '02x') for i in s)]])
        else:
            self.putz(s[0][0], s[-1][1], [5, ['Data: %s' % ' '.join(format(i[2], '02x') for i in s)]])

    def put_crc(self, s):
        self.puty(s, [6, ['CRC: {:02X} {:02X}'.format(s[0][2], s[1][2])]])

    def put_status(self, ss, es, status):
        self.putz(ss, es, [7, ['Status: %s' % STATUS[status]]])

    def put_warning(self, ss, es, msg):
        self.putz(ss, es, [8, ['Warning: %s' % msg]])

    def decode(self, ss, es, data):
        cmd, databyte = data
        # State machine.
        if self.state == 'IDLE':
            # Wait for an I²C START condition.
            if cmd != 'START':
                return
            self.state = 'GET SLAVE ADDR'
            self.ss_block = ss
        elif self.state == 'GET SLAVE ADDR':
            # Wait for an address read/write operation.
            if cmd == 'ADDRESS READ':
                self.state = 'READ REGS'
            elif cmd == 'ADDRESS WRITE':
                self.state = 'WRITE REGS'
        elif self.state == 'READ REGS':
            if cmd == 'DATA READ':
                self.bytes.append([ss, es, databyte])
            elif cmd == 'STOP':
                self.es_block = es
                # Reset the opcode before received data, as this causes
                # responses to be displayed incorrectly.
                self.opcode = -1
                if len(self.bytes) > 0:
                    self.output_rx_bytes()
                self.waddr = -1
                self.bytes = []
                self.state = 'IDLE'
        elif self.state == 'WRITE REGS':
            if cmd == 'DATA WRITE':
                self.bytes.append([ss, es, databyte])
            elif cmd == 'STOP':
                self.es_block = es
                self.output_tx_bytes()
                self.bytes = []
                self.state = 'IDLE'
