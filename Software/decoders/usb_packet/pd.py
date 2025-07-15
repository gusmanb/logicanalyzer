##
## This file is part of the libsigrokdecode project.
##
## Copyright (C) 2011 Gareth McMullin <gareth@blacksphere.co.nz>
## Copyright (C) 2012-2014 Uwe Hermann <uwe@hermann-uwe.de>
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

'''
OUTPUT_PYTHON format:

Packet:
[<ptype>, <pdata>]

<ptype>, <pdata>:
 - 'SYNC', <sync>
 - 'PID', <pid>
 - 'ADDR', <addr>
 - 'EP', <ep>
 - 'CRC5', <crc5>
 - 'CRC5 ERROR', <crc5>
 - 'CRC16', <crc16>
 - 'CRC16 ERROR', <crc16>
 - 'EOP', <eop>
 - 'FRAMENUM', <framenum>
 - 'DATABYTE', <databyte>
 - 'HUBADDR', <hubaddr>
 - 'SC', <sc>
 - 'PORT', <port>
 - 'S', <s>
 - 'E/U', <e/u>
 - 'ET', <et>
 - 'PACKET', [<pcategory>, <pname>, <pinfo>]

<pcategory>, <pname>, <pinfo>:
 - 'TOKEN', 'OUT', [<sync>, <pid>, <addr>, <ep>, <crc5>, <eop>]
 - 'TOKEN', 'IN', [<sync>, <pid>, <addr>, <ep>, <crc5>, <eop>]
 - 'TOKEN', 'SOF', [<sync>, <pid>, <framenum>, <crc5>, <eop>]
 - 'TOKEN', 'SETUP', [<sync>, <pid>, <addr>, <ep>, <crc5>, <eop>]
 - 'DATA', 'DATA0', [<sync>, <pid>, <databytes>, <crc16>, <eop>]
 - 'DATA', 'DATA1', [<sync>, <pid>, <databytes>, <crc16>, <eop>]
 - 'DATA', 'DATA2', [<sync>, <pid>, <databytes>, <crc16>, <eop>]
 - 'DATA', 'MDATA', [<sync>, <pid>, <databytes>, <crc16>, <eop>]
 - 'HANDSHAKE', 'ACK', [<sync>, <pid>, <eop>]
 - 'HANDSHAKE', 'NAK', [<sync>, <pid>, <eop>]
 - 'HANDSHAKE', 'STALL', [<sync>, <pid>, <eop>]
 - 'HANDSHAKE', 'NYET', [<sync>, <pid>, <eop>]
 - 'SPECIAL', 'PRE', [<sync>, <pid>, <addr>, <ep>, <crc5>, <eop>]
 - 'SPECIAL', 'ERR', [<sync>, <pid>, <eop>]
 - 'SPECIAL', 'SPLIT',
   [<sync>, <pid>, <hubaddr>, <sc>, <port>, <s>, <e/u>, <et>, <crc5>, <eop>]
 - 'SPECIAL', 'PING', [<sync>, <pid>, <addr>, <ep>, <crc5>, <eop>]
 - 'SPECIAL', 'Reserved', None

<sync>: SYNC field bitstring, normally '00000001' (8 chars).
<pid>: Packet ID bitstring, e.g. '11000011' for DATA0 (8 chars).
<addr>: Address field number, 0-127 (7 bits).
<ep>: Endpoint number, 0-15 (4 bits).
<crc5>: CRC-5 number (5 bits).
<crc16>: CRC-16 number (16 bits).
<eop>: End of packet marker. List of symbols, usually ['SE0', 'SE0', 'J'].
<framenum>: USB (micro)frame number, 0-2047 (11 bits).
<databyte>: A single data byte, e.g. 0x55.
<databytes>: List of data bytes, e.g. [0x55, 0xaa, 0x99] (0 - 1024 bytes).
<hubaddr>: TODO
<sc>: TODO
<port>: TODO
<s>: TODO
<e/u>: TODO
<et>: TODO
'''

# Packet IDs (PIDs).
# The first 4 bits are the 'packet type' field, the last 4 bits are the
# 'check field' (each bit in the check field must be the inverse of the resp.
# bit in the 'packet type' field; if not, that's a 'PID error').
# For the 4-bit strings, the left-most '1' or '0' is the LSB, i.e. it's sent
# to the bus first.
pids = {
    # Tokens
    '10000111': ['OUT', 'Address & EP number in host-to-function transaction'],
    '10010110': ['IN', 'Address & EP number in function-to-host transaction'],
    '10100101': ['SOF', 'Start-Of-Frame marker & frame number'],
    '10110100': ['SETUP', 'Address & EP number in host-to-function transaction for SETUP to a control pipe'],

    # Data
    # Note: DATA2 and MDATA are HS-only.
    '11000011': ['DATA0', 'Data packet PID even'],
    '11010010': ['DATA1', 'Data packet PID odd'],
    '11100001': ['DATA2', 'Data packet PID HS, high bandwidth isosynchronous transaction in a microframe'],
    '11110000': ['MDATA', 'Data packet PID HS for split and high-bandwidth isosynchronous transactions'],

    # Handshake
    '01001011': ['ACK', 'Receiver accepts error-free packet'],
    '01011010': ['NAK', 'Receiver cannot accept or transmitter cannot send'],
    '01111000': ['STALL', 'EP halted or control pipe request unsupported'],
    '01101001': ['NYET', 'No response yet from receiver'],

    # Special
    '00111100': ['PRE', 'Host-issued preamble; enables downstream bus traffic to low-speed devices'],
    #'00111100': ['ERR', 'Split transaction error handshake'],
    '00011110': ['SPLIT', 'HS split transaction token'],
    '00101101': ['PING', 'HS flow control probe for a bulk/control EP'],
    '00001111': ['Reserved', 'Reserved PID'],
}

def get_category(pidname):
    if pidname in ('OUT', 'IN', 'SOF', 'SETUP'):
        return 'TOKEN'
    elif pidname in ('DATA0', 'DATA1', 'DATA2', 'MDATA'):
        return 'DATA'
    elif pidname in ('ACK', 'NAK', 'STALL', 'NYET'):
        return 'HANDSHAKE'
    else:
        return 'SPECIAL'

def ann_index(pidname):
    l = ['OUT', 'IN', 'SOF', 'SETUP', 'DATA0', 'DATA1', 'DATA2', 'MDATA',
         'ACK', 'NAK', 'STALL', 'NYET', 'PRE', 'ERR', 'SPLIT', 'PING',
         'Reserved']
    if pidname not in l:
        return 28
    return l.index(pidname) + 11

def bitstr_to_num(bitstr):
    if not bitstr:
        return 0
    l = list(bitstr)
    l.reverse()
    return int(''.join(l), 2)

def reverse_number(num, count):
    out = list(count * '0')
    for i in range(0, count):
        if num >> i & 1:
            out[i] = '1'
    return int(''.join(out), 2)

def calc_crc5(bitstr):
    poly5 = 0x25
    crc5 = 0x1f
    for bit in bitstr:
        crc5 <<= 1
        if int(bit) != (crc5 >> 5):
            crc5 ^= poly5
        crc5 &= 0x1f
    crc5 ^= 0x1f
    return reverse_number(crc5, 5)

def calc_crc16(bitstr):
    poly16 = 0x18005
    crc16 = 0xffff
    for bit in bitstr:
        crc16 <<= 1
        if int(bit) != (crc16 >> 16):
            crc16 ^= poly16
        crc16 &= 0xffff
    crc16 ^= 0xffff
    return reverse_number(crc16, 16)

class Decoder(srd.Decoder):
    api_version = 3
    id = 'usb_packet'
    name = 'USB packet'
    longname = 'Universal Serial Bus (LS/FS) packet'
    desc = 'USB (low-speed and full-speed) packet protocol.'
    license = 'gplv2+'
    inputs = ['usb_signalling']
    outputs = ['usb_packet']
    tags = ['PC']
    options = (
        {'id': 'signalling', 'desc': 'Signalling',
            'default': 'full-speed', 'values': ('full-speed', 'low-speed')},
    )
    annotations = (
        ('sync-ok', 'SYNC'),
        ('sync-err', 'SYNC (error)'),
        ('pid', 'PID'),
        ('framenum', 'FRAMENUM'),
        ('addr', 'ADDR'),
        ('ep', 'EP'),
        ('crc5-ok', 'CRC5'),
        ('crc5-err', 'CRC5 (error)'),
        ('data', 'DATA'),
        ('crc16-ok', 'CRC16'),
        ('crc16-err', 'CRC16 (error)'),
        ('packet-out', 'Packet: OUT'),
        ('packet-in', 'Packet: IN'),
        ('packet-sof', 'Packet: SOF'),
        ('packet-setup', 'Packet: SETUP'),
        ('packet-data0', 'Packet: DATA0'),
        ('packet-data1', 'Packet: DATA1'),
        ('packet-data2', 'Packet: DATA2'),
        ('packet-mdata', 'Packet: MDATA'),
        ('packet-ack', 'Packet: ACK'),
        ('packet-nak', 'Packet: NAK'),
        ('packet-stall', 'Packet: STALL'),
        ('packet-nyet', 'Packet: NYET'),
        ('packet-pre', 'Packet: PRE'),
        ('packet-err', 'Packet: ERR'),
        ('packet-split', 'Packet: SPLIT'),
        ('packet-ping', 'Packet: PING'),
        ('packet-reserved', 'Packet: Reserved'),
        ('packet-invalid', 'Packet: Invalid'),
    )
    annotation_rows = (
        ('fields', 'Packet fields', tuple(range(10 + 1))),
        ('packet', 'Packets', tuple(range(11, 28 + 1))),
    )

    def __init__(self):
        self.reset()

    def reset(self):
        self.bits = []
        self.packet = []
        self.packet_summary = ''
        self.ss = self.es = None
        self.ss_packet = self.es_packet = None
        self.state = 'WAIT FOR SOP'

    def putpb(self, data):
        self.put(self.ss, self.es, self.out_python, data)

    def putb(self, data):
        self.put(self.ss, self.es, self.out_ann, data)

    def putpp(self, data):
        self.put(self.ss_packet, self.es_packet, self.out_python, data)

    def putp(self, data):
        self.put(self.ss_packet, self.es_packet, self.out_ann, data)

    def start(self):
        self.out_python = self.register(srd.OUTPUT_PYTHON)
        self.out_ann = self.register(srd.OUTPUT_ANN)

    def handle_packet(self):
        packet = ''
        for (bit, ss, es) in self.bits:
            packet += bit

        if len(packet) < 8:
            self.putp([28, ['Invalid packet (shorter than 8 bits)']])
            return

        # Bits[0:7]: SYNC
        sync = packet[:7 + 1]
        self.ss, self.es = self.bits[0][1], self.bits[7][2]
        # The SYNC pattern for low-speed/full-speed is KJKJKJKK (00000001).
        if sync != '00000001':
            self.putpb(['SYNC ERROR', sync])
            self.putb([1, ['SYNC ERROR: %s' % sync, 'SYNC ERR: %s' % sync,
                           'SYNC ERR', 'SE', 'S']])
        else:
            self.putpb(['SYNC', sync])
            self.putb([0, ['SYNC: %s' % sync, 'SYNC', 'S']])
        self.packet.append(sync)

        if len(packet) < 16:
            self.putp([28, ['Invalid packet (shorter than 16 bits)']])
            return

        # Bits[8:15]: PID
        pid = packet[8:15 + 1]
        pidname = pids.get(pid, ('UNKNOWN', 'Unknown PID'))[0]
        self.ss, self.es = self.bits[8][1], self.bits[15][2]
        self.putpb(['PID', pidname])
        self.putb([2, ['PID: %s' % pidname, pidname, pidname[0]]])
        self.packet.append(pid)
        self.packet_summary += pidname

        if pidname in ('OUT', 'IN', 'SOF', 'SETUP', 'PING'):
            if len(packet) < 32:
                self.putp([28, ['Invalid packet (shorter than 32 bits)']])
                return

            if pidname == 'SOF':
                # Bits[16:26]: Framenum
                framenum = bitstr_to_num(packet[16:26 + 1])
                self.ss, self.es = self.bits[16][1], self.bits[26][2]
                self.putpb(['FRAMENUM', framenum])
                self.putb([3, ['Frame: %d' % framenum, 'Frame', 'Fr', 'F']])
                self.packet.append(framenum)
                self.packet_summary += ' %d' % framenum
            else:
                # Bits[16:22]: Addr
                addr = bitstr_to_num(packet[16:22 + 1])
                self.ss, self.es = self.bits[16][1], self.bits[22][2]
                self.putpb(['ADDR', addr])
                self.putb([4, ['Address: %d' % addr, 'Addr: %d' % addr,
                               'Addr', 'A']])
                self.packet.append(addr)
                self.packet_summary += ' ADDR %d' % addr

                # Bits[23:26]: EP
                ep = bitstr_to_num(packet[23:26 + 1])
                self.ss, self.es = self.bits[23][1], self.bits[26][2]
                self.putpb(['EP', ep])
                self.putb([5, ['Endpoint: %d' % ep, 'EP: %d' % ep, 'EP', 'E']])
                self.packet.append(ep)
                self.packet_summary += ' EP %d' % ep

            # Bits[27:31]: CRC5
            crc5 = bitstr_to_num(packet[27:31 + 1])
            crc5_calc = calc_crc5(packet[16:27])
            self.ss, self.es = self.bits[27][1], self.bits[31][2]
            if crc5 == crc5_calc:
                self.putpb(['CRC5', crc5])
                self.putb([6, ['CRC5: 0x%02X' % crc5, 'CRC5', 'C']])
            else:
                self.putpb(['CRC5 ERROR', crc5])
                self.putb([7, ['CRC5 ERROR: 0x%02X' % crc5, 'CRC5 ERR', 'CE', 'C']])
            self.packet.append(crc5)
        elif pidname in ('DATA0', 'DATA1', 'DATA2', 'MDATA'):
            # Bits[16:packetlen-16]: Data
            data = packet[16:-16]
            # TODO: len(data) must be a multiple of 8.
            databytes = []
            self.packet_summary += ' ['
            for i in range(0, len(data), 8):
                db = bitstr_to_num(data[i:i + 8])
                self.ss, self.es = self.bits[16 + i][1], self.bits[23 + i][2]
                self.putpb(['DATABYTE', db])
                self.putb([8, ['Databyte: %02X' % db, 'Data: %02X' % db,
                               'DB: %02X' % db, '%02X' % db]])
                databytes.append(db)
                self.packet_summary += ' %02X' % db
            self.packet_summary += ' ]'

            if len(packet) < 32:
                self.putp([28, ['Invalid packet (shorter than 32 bits)']])
                return

            # Convenience Python output (no annotation) for all bytes together.
            self.ss, self.es = self.bits[16][1], self.bits[-16][2]
            self.putpb(['DATABYTES', databytes])
            self.packet.append(databytes)

            # Bits[packetlen-16:packetlen]: CRC16
            crc16 = bitstr_to_num(packet[-16:])
            crc16_calc = calc_crc16(packet[16:-16])
            self.ss, self.es = self.bits[-16][1], self.bits[-1][2]
            if crc16 == crc16_calc:
                self.putpb(['CRC16', crc16])
                self.putb([9, ['CRC16: 0x%04X' % crc16, 'CRC16', 'C']])
            else:
                self.putpb(['CRC16 ERROR', crc16])
                self.putb([10, ['CRC16 ERROR: 0x%04X' % crc16, 'CRC16 ERR', 'CE', 'C']])
            self.packet.append(crc16)
        elif pidname in ('ACK', 'NAK', 'STALL', 'NYET', 'ERR'):
            pass # Nothing to do, these only have SYNC+PID+EOP fields.
        elif pidname in ('PRE'):
            pass # Nothing to do, PRE only has SYNC+PID fields.
        else:
            pass # TODO: Handle 'SPLIT' and possibly 'Reserved' packets.

        # Output a (summary of) the whole packet.
        pcategory, pname, pinfo = get_category(pidname), pidname, self.packet
        self.putpp(['PACKET', [pcategory, pname, pinfo]])
        self.putp([ann_index(pidname), ['%s' % self.packet_summary]])

        self.packet, self.packet_summary = [], ''

    def decode(self, ss, es, data):
        (ptype, pdata) = data

        # We only care about certain packet types for now.
        if ptype not in ('SOP', 'BIT', 'EOP', 'ERR'):
            return

        # State machine.
        if self.state == 'WAIT FOR SOP':
            if ptype != 'SOP':
                return
            self.ss_packet = ss
            self.state = 'GET BIT'
        elif self.state == 'GET BIT':
            if ptype == 'BIT':
                self.bits.append([pdata, ss, es])
            elif ptype == 'EOP' or ptype == 'ERR':
                self.es_packet = es
                self.handle_packet()
                self.packet, self.packet_summary = [], ''
                self.bits, self.state = [], 'WAIT FOR SOP'
            else:
                pass # TODO: Error
