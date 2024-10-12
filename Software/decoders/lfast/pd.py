##
## This file is part of the libsigrokdecode project.
##
## Copyright (C) 2020 Soeren Apel <soeren@apelpie.net>
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
from common.srdhelper import bitpack
import decimal

'''
OUTPUT_PYTHON format:

[ss, es, data] where data is a data byte of the LFAST payload. All bytes of
the payload are sent at once, each with its start and end sample.
'''

# See tc27xD_um_v2.2.pdf, Table 20-10
payload_sizes = {
    0b000: '8 bit',
    0b001: '32 bit / 4 byte',
    0b010: '64 bit / 8 byte',
    0b011: '96 bit / 12 byte',
    0b100: '128 bit / 16 byte',
    0b101: '256 bit / 32 byte',
    0b110: '512 bit / 64 byte',
    0b111: '288 bit / 36 byte'
}

# See tc27xD_um_v2.2.pdf, Table 20-10
payload_byte_sizes = {
    0b000: 1,
    0b001: 4,
    0b010: 8,
    0b011: 12,
    0b100: 16,
    0b101: 32,
    0b110: 64,
    0b111: 36
}

# See tc27xD_um_v2.2.pdf, Table 20-11
channel_types = {
    0b0000: 'Interface Control / PING',
    0b0001: 'Unsolicited Status (32 bit)',
    0b0010: 'Slave Interface Control / Read',
    0b0011: 'CTS Transfer',
    0b0100: 'Data Channel A',
    0b0101: 'Data Channel B',
    0b0110: 'Data Channel C',
    0b0111: 'Data Channel D',
    0b1000: 'Data Channel E',
    0b1001: 'Data Channel F',
    0b1010: 'Data Channel G',
    0b1011: 'Data Channel H',
    0b1100: 'Reserved',
    0b1101: 'Reserved',
    0b1110: 'Reserved',
    0b1111: 'Reserved',
}

# See tc27xD_um_v2.2.pdf, Table 20-12
control_payloads = {
    0x00: 'PING',
    0x01: 'Reserved',
    0x02: 'Slave interface clock multiplier start',
    0x04: 'Slave interface clock multiplier stop',
    0x08: 'Use 5 MBaud for M->S',
    0x10: 'Use 320 MBaud for M->S',
    0x20: 'Use 5 MBaud for S->M',
    0x40: 'Use 20 MBaud for S->M (needs 20 MHz SysClk)',
    0x80: 'Use 320 MBaud for S->M',
    0x31: 'Enable slave interface transmitter',
    0x32: 'Disable slave interface transmitter',
    0x34: 'Enable clock test mode',
    0x38: 'Disable clock test mode and payload loopback',
    0xFF: 'Enable payload loopback',
}


ann_bit, ann_sync, ann_header_pl_size, ann_header_ch_type, ann_header_cts, \
    ann_payload, ann_control_data, ann_sleepbit, ann_warning = range(9)
state_sync, state_header, state_payload, state_sleepbit = range(4)

class Decoder(srd.Decoder):
    api_version = 3
    id = 'lfast'
    name = 'LFAST'
    longname = 'NXP LFAST interface'
    desc = 'Differential high-speed P2P interface'
    license = 'gplv2+'
    inputs = ['logic']
    outputs = ['lfast']
    tags = ['Embedded/industrial']
    channels = (
        {'id': 'data', 'name': 'Data', 'desc': 'TXP or RXP'},
    )
    annotations = (
        ('bit', 'Bits'),
        ('sync', 'Sync Pattern'),
        ('header_pl_size', 'Payload Size'),
        ('header_ch_type', 'Logical Channel Type'),
        ('header_cts', 'Clear To Send'),
        ('payload', 'Payload'),
        ('ctrl_data', 'Control Data'),
        ('sleep', 'Sleep Bit'),
        ('warning', 'Warning'),
    )
    annotation_rows = (
        ('bits', 'Bits', (ann_bit,)),
        ('fields', 'Fields', (ann_sync, ann_header_pl_size, ann_header_ch_type,
            ann_header_cts, ann_payload, ann_control_data, ann_sleepbit,)),
        ('warnings', 'Warnings', (ann_warning,)),
    )

    def __init__(self):
        decimal.getcontext().rounding = decimal.ROUND_HALF_UP
        self.bit_len = 0xFFFFFFFF
        self.reset()

    def reset(self):
        self.prev_bit_len = self.bit_len
        self.ss = self.es = 0
        self.ss_payload = self.es_payload = 0
        self.ss_byte = 0
        self.bits = []
        self.payload = []
        self.payload_size = 0  # Expected number of bytes, as read from header
        self.bit_len = 0       # Length of one bit time, in samples
        self.timeout = 0       # Desired timeout for next edge, in samples
        self.ch_type_id = 0    # ID of channel type
        self.state = state_sync

    def metadata(self, key, value):
        pass

    def start(self):
        self.out_python = self.register(srd.OUTPUT_PYTHON)
        self.out_ann = self.register(srd.OUTPUT_ANN)

    def put_ann(self, ss, es, ann_class, value):
        self.put(ss, es, self.out_ann, [ann_class, value])

    def put_payload(self):
        self.put(self.ss_payload, self.es_payload, self.out_python, self.payload)

    def handle_sync(self):
        if len(self.bits) == 1:
            self.ss_sync = self.ss_bit

        if len(self.bits) == 16:
            value = bitpack(self.bits)
            if value == 0xA84B:
                self.put_ann(self.ss_sync, self.es_bit, ann_sync, ['Sync OK'])
            else:
                self.put_ann(self.ss_sync, self.es_bit, ann_warning, ['Wrong Sync Value: {:02X}'.format(value)])
                self.reset()

            # Only continue if we didn't just reset
            if self.ss > 0:
                self.bits = []
                self.state = state_header
                self.timeout = int(9.4 * self.bit_len)

    def handle_header(self):
        if len(self.bits) == 1:
            self.ss_header = self.ss_bit

        if len(self.bits) == 8:
            # See tc27xD_um_v2.2.pdf, Figure 20-47, for the header structure
            bit_len = (self.es_bit - self.ss_header) / 8
            value = bitpack(self.bits)

            ss = self.ss_header
            es = ss + 3 * bit_len
            size_id = (value & 0xE0) >> 5
            size = payload_sizes.get(size_id)
            self.payload_size = payload_byte_sizes.get(size_id)
            self.put_ann(int(ss), int(es), ann_header_pl_size, [size])

            ss = es
            es = ss + 4 * bit_len
            self.ch_type_id = (value & 0x1E) >> 1
            ch_type = channel_types.get(self.ch_type_id)
            self.put_ann(int(ss), int(es), ann_header_ch_type, [ch_type])

            ss = es
            es = ss + bit_len
            cts = value & 0x01
            self.put_ann(int(ss), int(es), ann_header_cts, ['{}'.format(cts)])

            self.bits = []
            self.state = state_payload
            self.timeout = int(9.4 * self.bit_len)

    def handle_payload(self):
        self.timeout = int((self.payload_size - len(self.payload)) * 8 * self.bit_len)

        if len(self.bits) == 1:
            self.ss_byte = self.ss_bit
            if self.ss_payload == 0:
                self.ss_payload = self.ss_bit

        if len(self.bits) == 8:
            value = bitpack(self.bits)
            value_hex = '{:02X}'.format(value)

            # Control transfers have no SIPI payload, show them as control transfers
            # Check the channel_types list for the meaning of the magic values
            if (self.ch_type_id >= 0b0100) and (self.ch_type_id <= 0b1011):
                self.put_ann(self.ss_byte, self.es_bit, ann_payload, [value_hex])
            else:
                # Control transfers are 8-bit transfers, so only evaluate the first byte
                if len(self.payload) == 0:
                    ctrl_data = control_payloads.get(value, value_hex)
                    self.put_ann(self.ss_byte, self.es_bit, ann_control_data, [ctrl_data])
                else:
                    self.put_ann(self.ss_byte, self.es_bit, ann_control_data, [value_hex])

            self.bits = []
            self.es_payload = self.es_bit
            self.payload.append((self.ss_byte, self.es_payload, value))

            if (len(self.payload) == self.payload_size):
                self.timeout = int(1.4 * self.bit_len)
                self.state = state_sleepbit

    def handle_sleepbit(self):
        if len(self.bits) == 0:
            self.put_ann(self.ss_bit, self.es_bit, ann_sleepbit, ['No LVDS sleep mode request', 'No sleep', 'N'])
        elif len(self.bits) > 1:
            self.put_ann(self.ss_bit, self.es_bit, ann_warning, ['Expected only the sleep bit, got {} bits instead'.format(len(self.bits))])
        else:
            if self.bits[0] == 1:
                self.put_ann(self.ss_bit, self.es_bit, ann_sleepbit, ['LVDS sleep mode request', 'Sleep', 'Y'])
            else:
                self.put_ann(self.ss_bit, self.es_bit, ann_sleepbit, ['No LVDS sleep mode request', 'No sleep', 'N'])

        # We only send the payload out if this is an actual data transfer;
        # check the channel_types list for the meaning of the magic values
        if (self.ch_type_id >= 0b0100) and (self.ch_type_id <= 0b1011):
            if len(self.payload) > 0:
                self.put_payload()

    def decode(self):
        while True:
            if self.timeout == 0:
                rising_edge, = self.wait({0: 'e'})
            else:
                rising_edge, = self.wait([{0: 'e'}, {'skip': self.timeout}])

            # If this is the first edge, we only update ss
            if self.ss == 0:
                self.ss = self.samplenum
                # Let's set the timeout for the sync pattern as well
                self.timeout = int(16.2 * self.prev_bit_len)
                continue

            self.es = self.samplenum

            # Check for the sleep bit if this is a timeout condition
            if (len(self.matched) == 2) and self.matched[1]:
                rising_edge = ~rising_edge
                if self.state == state_sync:
                    self.reset()
                    continue
                elif self.state == state_sleepbit:
                    self.ss_bit += self.bit_len
                    self.es_bit = self.ss_bit + self.bit_len
                    self.handle_sleepbit()
                    self.reset()
                    continue

            # Shouldn't happen but we check just in case
            if int(self.es - self.ss) == 0:
                continue

            # We use the first bit to deduce the bit length
            if self.bit_len == 0:
                self.bit_len = self.es - self.ss

            # Determine number of bits covered by this edge
            bit_count = (self.es - self.ss) / self.bit_len
            bit_count = int(decimal.Decimal(bit_count).to_integral_value())

            if bit_count == 0:
                self.put_ann(self.ss, self.es, ann_warning, ['Bit time too short'])
                self.reset()
                continue

            bit_value = '0' if rising_edge else '1'

            divided_len = (self.es - self.ss) / bit_count
            for i in range(bit_count):
                self.ss_bit = int(self.ss + i * divided_len)
                self.es_bit = int(self.ss_bit + divided_len)
                self.put_ann(self.ss_bit, self.es_bit, ann_bit, [bit_value])

                # Place the new bit at the front of the bit list
                self.bits.insert(0, (0 if rising_edge else 1))

                if self.state == state_sync:
                    self.handle_sync()
                elif self.state == state_header:
                    self.handle_header()
                elif self.state == state_payload:
                    self.handle_payload()
                elif self.state == state_sleepbit:
                    self.handle_sleepbit()
                    self.reset()

                if self.ss == 0:
                    break  # Because reset() was called, invalidating everything

            # Only update ss if we didn't just perform a reset
            if self.ss > 0:
                self.ss = self.samplenum

            # If we got here when a timeout occurred, we have processed all null
            # bits that we could and should reset now to find the next packet
            if (len(self.matched) == 2) and self.matched[1]:
                self.reset()
