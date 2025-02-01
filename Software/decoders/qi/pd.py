##
## This file is part of the libsigrokdecode project.
##
## Copyright (C) 2015 Josef Gajdusek <atx@atx.name>
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
import operator
import collections
from functools import reduce

end_codes = (
    'Unknown',
    'Charge Complete',
    'Internal Fault',
    'Over Temperature',
    'Over Voltage',
    'Over Current',
    'Battery Failure',
    'Reconfigure',
    'No Response',
)

class SamplerateError(Exception):
    pass

def calc_checksum(packet):
    return reduce(operator.xor, packet[:-1])

def bits_to_uint(bits):
    # LSB first
    return reduce(lambda i, v: (i >> 1) | (v << (len(bits) - 1)), bits, 0)

class Decoder(srd.Decoder):
    api_version = 3
    id = 'qi'
    name = 'Qi'
    longname = 'Qi charger protocol'
    desc = 'Protocol used by Qi receiver.'
    license = 'gplv2+'
    inputs = ['logic']
    outputs = []
    tags = ['Embedded/industrial', 'Wireless/RF']
    channels = (
        {'id': 'qi', 'name': 'Qi', 'desc': 'Demodulated Qi data line'},
    )
    annotations = (
        ('bit', 'Bit'),
        ('byte-error', 'Bit error'),
        ('byte-start', 'Start bit'),
        ('byte-info', 'Info bit'),
        ('byte-data', 'Data byte'),
        ('packet-data', 'Packet data'),
        ('packet-checksum-ok', 'Packet checksum OK'),
        ('packet-checksum-err', 'Packet checksum error'),
    )
    annotation_rows = (
        ('bits', 'Bits', (0,)),
        ('bytes', 'Bytes', (1, 2, 3, 4)),
        ('packets', 'Packets', (5, 6, 7)),
    )

    def __init__(self):
        self.reset()

    def reset(self):
        self.samplerate = None
        self.reset_variables()

    def reset_variables(self):
        self.counter = 0
        self.prev = None
        self.state = 'IDLE'
        self.lastbit = 0
        self.bytestart = 0
        self.deq = collections.deque(maxlen = 2)
        self.bits = []
        self.bitsi = [0]
        self.bytesi = []
        self.packet = []

    def metadata(self, key, value):
        if key == srd.SRD_CONF_SAMPLERATE:
            self.samplerate = value
            self.bit_width = float(self.samplerate) / 2e3

    def start(self):
        self.out_ann = self.register(srd.OUTPUT_ANN)
        self.reset_variables()

    def packet_len(self, byte):
        if 0x00 <= byte <= 0x1f:
            return int(1 + (byte - 0) / 32)
        if 0x20 <= byte <= 0x7f:
            return int(2 + (byte - 32) / 16)
        if 0x80 <= byte <= 0xdf:
            return int(8 + (byte - 128) / 8)
        if 0xe0 <= byte <= 0xff:
            return int(20 + (byte - 224) / 4)

    def in_tolerance(self, l):
        return (0.75 * self.bit_width) < l < (1.25 * self.bit_width)

    def putp(self, data):
        self.put(self.bytesi[0], self.bytesi[-1], self.out_ann, [5, data])

    def process_packet(self):
        if self.packet[0] == 0x01: # Signal Strength
            self.putp(['Signal Strength: %d' % self.packet[1],
                       'SS: %d' % self.packet[1], 'SS'])
        elif self.packet[0] == 0x02: # End Power Transfer
            reason = end_codes[self.packet[1]] if self.packet[1] < len(end_codes) else 'Reserved'
            self.putp(['End Power Transfer: %s' % reason,
                       'EPT: %s' % reason, 'EPT'])
        elif self.packet[0] == 0x03: # Control Error
            val = self.packet[1] if self.packet[1] < 128 else (self.packet[1] & 0x7f) - 128
            self.putp(['Control Error: %d' % val, 'CE: %d' % val, 'CE'])
        elif self.packet[0] == 0x04: # Received Power
            self.putp(['Received Power: %d' % self.packet[1],
                       'RP: %d' % self.packet[1], 'RP'])
        elif self.packet[0] == 0x05: # Charge Status
            self.putp(['Charge Status: %d' % self.packet[1],
                       'CS: %d' % self.packet[1], 'CS'])
        elif self.packet[0] == 0x06: # Power Control Hold-off
            self.putp(['Power Control Hold-off: %dms' % self.packet[1],
                       'PCH: %d' % self.packet[1]], 'PCH')
        elif self.packet[0] == 0x51: # Configuration
            powerclass = (self.packet[1] & 0xc0) >> 7
            maxpower = self.packet[1] & 0x3f
            prop = (self.packet[3] & 0x80) >> 7
            count = self.packet[3] & 0x07
            winsize = (self.packet[4] & 0xf8) >> 3
            winoff = self.packet[4] & 0x07
            self.putp(['Configuration: Power Class = %d, Maximum Power = %d, Prop = %d,'
                       'Count = %d, Window Size = %d, Window Offset = %d' %
                       (powerclass, maxpower, prop, count, winsize, winoff),
                       'C: PC = %d MP = %d P = %d C = %d WS = %d WO = %d' %
                       (powerclass, maxpower, prop, count, winsize, winoff),
                       'Configuration', 'C'])
        elif self.packet[0] == 0x71: # Identification
            version = '%d.%d' % ((self.packet[1] & 0xf0) >> 4, self.packet[1] & 0x0f)
            mancode = '%02x%02x' % (self.packet[2], self.packet[3])
            devid = '%02x%02x%02x%02x' % (self.packet[4] & ~0x80,
                    self.packet[5], self.packet[6], self.packet[7])
            self.putp(['Identification: Version = %s, Manufacturer = %s, ' \
                       'Device = %s' % (version, mancode, devid),
                       'ID: %s %s %s' % (version, mancode, devid), 'ID'])
        elif self.packet[0] == 0x81: # Extended Identification
            edevid = '%02x%02x%02x%02x%02x%02x%02x%02x' % self.packet[1:-1]
            self.putp(['Extended Identification: %s' % edevid,
                       'EI: %s' % edevid, 'EI'])
        elif self.packet[0] in (0x18, 0x19, 0x28, 0x29, 0x38, 0x48, 0x58, 0x68,
                0x78, 0x85, 0xa4, 0xc4, 0xe2): # Proprietary
            self.putp(['Proprietary', 'P'])
        else: # Unknown
            self.putp(['Unknown', '?'])
        self.put(self.bytesi[-1], self.samplenum, self.out_ann,
                 [6, ['Checksum OK', 'OK']] if \
                 calc_checksum(self.packet) == self.packet[-1]
                 else [6, ['Checksum error', 'ERR']])

    def process_byte(self):
        self.put(self.bytestart, self.bitsi[0], self.out_ann,
                 ([2, ['Start bit', 'Start', 'S']]) if self.bits[0] == 0 else
                 ([1, ['Start error', 'Start err', 'SE']]))
        databits = self.bits[1:9]
        data = bits_to_uint(databits)
        parity = reduce(lambda i, v: (i + v) % 2, databits, 1)
        self.put(self.bitsi[0], self.bitsi[8], self.out_ann, [4, ['%02x' % data]])
        self.put(self.bitsi[8], self.bitsi[9], self.out_ann,
                 ([3, ['Parity bit', 'Parity', 'P']]) if self.bits[9] == parity else
                 ([1, ['Parity error', 'Parity err', 'PE']]))
        self.put(self.bitsi[9], self.bitsi[10], self.out_ann,
                 ([3, ['Stop bit', 'Stop', 'S']]) if self.bits[10] == 1 else
                 ([1, ['Stop error', 'Stop err', 'SE']]))

        self.bytesi.append(self.bytestart)
        self.packet.append(data)
        if self.packet_len(self.packet[0]) + 2 == len(self.packet):
            self.process_packet()
            self.bytesi.clear()
            self.packet.clear()

    def add_bit(self, bit):
        self.bits.append(bit)
        self.bitsi.append(self.samplenum)

        if self.state == 'IDLE' and len(self.bits) >= 5 and \
                                    self.bits[-5:] == [1, 1, 1, 1, 0]:
            self.state = 'DATA'
            self.bytestart = self.bitsi[-2]
            self.bits = [0]
            self.bitsi = [self.samplenum]
            self.packet.clear()
        elif self.state == 'DATA' and len(self.bits) == 11:
            self.process_byte()
            self.bytestart = self.samplenum
            self.bits.clear()
            self.bitsi.clear()
        if self.state != 'IDLE':
            self.put(self.lastbit, self.samplenum, self.out_ann, [0, ['%d' % bit]])
        self.lastbit = self.samplenum

    def handle_transition(self, l, htl):
        self.deq.append(l)
        if len(self.deq) >= 2 and \
                (self.in_tolerance(self.deq[-1] + self.deq[-2]) or \
                htl and self.in_tolerance(l * 2) and \
                self.deq[-2] > 1.25 * self.bit_width):
            self.add_bit(1)
            self.deq.clear()
        elif self.in_tolerance(l):
            self.add_bit(0)
            self.deq.clear()
        elif l > (1.25 * self.bit_width):
            self.state = 'IDLE'
            self.bytesi.clear()
            self.packet.clear()
            self.bits.clear()
            self.bitsi.clear()

    def decode(self):
        if not self.samplerate:
            raise SamplerateError('Cannot decode without samplerate.')

        (qi,) = self.wait()
        self.handle_transition(self.samplenum, qi == 0)
        while True:
            prev = self.samplenum
            (qi,) = self.wait({0: 'e'})
            self.handle_transition(self.samplenum - prev, qi == 0)
