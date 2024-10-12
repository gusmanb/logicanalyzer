##
## This file is part of the libsigrokdecode project.
##
## Copyright (C) 2018 Dave Craig <dcraig@brightsign.biz>
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

msg_ids = {
    2: 'AKE_Init',
    3: 'AKE_Send_Cert',
    4: 'AKE_No_stored_km',
    5: 'AKE_Stored_km',

    7: 'AKE_Send_H_prime',
    8: 'AKE_Send_Pairing_Info',

    9: 'LC_Init',
    10: 'LC_Send_L_prime',

    11: 'SKE_Send_Eks',
    12: 'RepeaterAuth_Send_ReceiverID_List',

    15: 'RepeaterAuth_Send_Ack',
    16: 'RepeaterAuth_Stream_Manage',
    17: 'RepeaterAuth_Stream_Ready',
}

write_items = {
    0x00: '1.4 Bksv - Receiver KSV',
    0x08: '1.4 Ri\' - Link Verification',
    0x0a: '1.4 Pj\' - Enhanced Link Verification',
    0x10: '1.4 Aksv - Transmitter KSV',
    0x15: '1.4 Ainfo - Transmitter KSV',
    0x18: '1.4 An - Session random number',
    0x20: '1.4 V\'H0',
    0x24: '1.4 V\'H1',
    0x28: '1.4 V\'H2',
    0x2c: '1.4 V\'H3',
    0x30: '1.4 V\'H4',
    0x40: '1.4 Bcaps',
    0x41: '1.4 Bstatus',
    0x43: '1.4 KSV FIFO',
    0x50: 'HDCP2Version',
    0x60: 'Write_Message',
    0x70: 'RxStatus',
    0x80: 'Read_Message',
}

class Decoder(srd.Decoder):
    api_version = 3
    id = 'hdcp'
    name = 'HDCP'
    longname = 'HDCP over HDMI'
    desc = 'HDCP protocol over HDMI.'
    license = 'gplv2+'
    inputs = ['i2c']
    outputs = ['hdcp']
    tags = ['PC', 'Security/crypto']
    annotations = \
        tuple(('message-0x%02X' % i, 'Message 0x%02X' % i) for i in range(18)) + (
        ('summary', 'Summary'),
        ('warning', 'Warning'),
    )
    annotation_rows = (
        ('messages', 'Messages', tuple(range(18))),
        ('summaries', 'Summaries', (18,)),
        ('warnings', 'Warnings', (19,)),
    )

    def __init__(self):
        self.reset()

    def reset(self):
        self.state = 'IDLE'
        self.stack = []
        self.msg = -1
        self.ss = self.es = self.ss_block = self.es_block = 0
        self.init_seq = []
        self.valid = 0
        self.type = ''

    def start(self):
        self.out_ann = self.register(srd.OUTPUT_ANN)

    def putb(self, data):
        self.put(self.ss_block, self.es_block, self.out_ann, data)

    def decode(self, ss, es, data):
        cmd, databyte = data

        # Collect the 'BITS' packet, then return. The next packet is
        # guaranteed to belong to these bits we just stored.
        if cmd == 'BITS':
            self.bits = databyte
            return

        self.ss, self.es = ss, es

        # State machine.
        if self.state == 'IDLE':
            # Wait for an I2C START condition.
            if cmd == 'START':
                self.reset()
                self.ss_block = ss
            elif cmd != 'START REPEAT':
                return
            self.state = 'GET SLAVE ADDR'
        elif self.state == 'GET SLAVE ADDR':
            if cmd == 'ADDRESS READ':
                self.state = 'BUFFER DATA'
                if databyte != 0x3a:
                    self.state = 'IDLE'
            elif cmd == 'ADDRESS WRITE':
                self.state = 'WRITE OFFSET'
                if databyte != 0x3a:
                    self.state = 'IDLE'
        elif self.state == 'WRITE OFFSET':
            if cmd == 'DATA WRITE':
                if databyte in write_items:
                    self.type = write_items[databyte]
                if databyte in (0x10, 0x15, 0x18, 0x60):
                    self.state = 'BUFFER DATA'
                # If we are reading, then jump back to IDLE for a start repeat.
                # If we are writing, then just continue onwards.
                if self.state == 'BUFFER DATA':
                    pass
                elif self.type != '':
                    self.state = 'IDLE'
        elif self.state == 'BUFFER DATA':
            if cmd in ('STOP', 'NACK'):
                self.es_block = es
                self.state = 'IDLE'
                if self.type == '':
                    return
                if not self.stack:
                    self.putb([18, ['%s' % (self.type)]])
                    return
                if self.type == 'RxStatus':
                    rxstatus = (self.stack.pop() << 8) | self.stack.pop()
                    reauth_req = (rxstatus & 0x800) != 0
                    ready = (rxstatus & 0x400) != 0
                    length = rxstatus & 0x3ff
                    text = '%s, reauth %s, ready %s, length %s' % \
                        (self.type, reauth_req, ready, length)
                    self.putb([18, [text]])
                elif self.type == '1.4 Bstatus':
                    bstatus = (self.stack.pop() << 8) | self.stack.pop()
                    device_count = bstatus & 0x7f
                    max_devs_exceeded = (bstatus & 0x80) != 0
                    depth = ((bstatus & 0x700) >> 8)
                    max_cascase_exceeded = bstatus & 0x800
                    hdmi_mode = (bstatus & 0x1000) != 0
                    text = '%s, %s devices, depth %s, hdmi mode %s' % \
                        (self.type, device_count, depth, hdmi_mode)
                    self.putb([18, [text]])
                elif self.type == 'Read_Message':
                    msg = self.stack.pop(0)
                    self.putb([msg, ['%s, %s' % (self.type,
                        msg_ids.get(msg, 'Invalid'))]])
                elif self.type == 'Write_Message':
                    msg = self.stack.pop(0)
                    self.putb([msg, ['%s, %s' % (self.type,
                        msg_ids.get(msg, 'Invalid'))]])
                elif self.type == 'HDCP2Version':
                    version = self.stack.pop(0)
                    if (version & 0x4):
                        self.putb([18, ['HDCP2']])
                    else:
                        self.putb([18, ['NOT HDCP2']])
                else:
                    self.putb([18, ['%s' % (self.type)]])
            elif cmd == 'DATA READ':
                # Stack up our data bytes.
                self.stack.append(databyte)
            elif cmd == 'DATA WRITE':
                # Stack up our data bytes.
                self.stack.append(databyte)
