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
from binascii import crc_hqx

# See tc27xD_um_v2.2.pdf, Table 20-2
# (name, addr byte count, data byte count)
command_codes = {
    0b00000: ('Read byte', 4, 0),
    0b00001: ('Read 2 byte', 4, 0),
    0b00010: ('Read 4 byte', 4, 0),
    # Reserved
    0b00100: ('Write byte with ACK', 4, 4),
    0b00101: ('Write 2 byte with ACK', 4, 4),
    0b00110: ('Write 4 byte with ACK', 4, 4),
    # Reserved
    0b01000: ('ACK', 0, 0),
    0b01001: ('NACK (Target Error)', 0, 0),
    0b01010: ('Read Answer with ACK', 4, 4),
    # Reserved
    0b01100: ('Trigger with ACK', 0, 0),
    # Reserved
    # Reserved
    # Reserved
    # Reserved
    # Reserved
    0b10010: ('Read 4-byte JTAG ID', 0, 0),
    # Reserved
    # Reserved
    # Reserved
    # Reserved
    0b10111: ('Stream 32 byte with ACK', 0, 32)
    # Rest is reserved
}


ann_header_tag, ann_header_cmd, ann_header_ch, ann_address, ann_data, \
    ann_crc, ann_warning = range(7)

class Decoder(srd.Decoder):
    api_version = 3
    id = 'sipi'
    name = 'SIPI (Zipwire)'
    longname = 'NXP SIPI interface'
    desc = 'Serial Inter-Processor Interface (SIPI) aka Zipwire, aka HSSL'
    license = 'gplv2+'
    inputs = ['lfast']
    outputs = []
    tags = ['Embedded/industrial']
    annotations = (
        ('header_tag', 'Transaction Tag'),
        ('header_cmd', 'Command Code'),
        ('header_ch', 'Channel'),
        ('address', 'Address'),
        ('data', 'Data'),
        ('crc', 'CRC'),
        ('warning', 'Warning'),
    )
    annotation_rows = (
        ('fields', 'Fields', (ann_header_tag, ann_header_cmd,
            ann_header_ch, ann_address, ann_data, ann_crc,)),
        ('warnings', 'Warnings', (ann_warning,)),
    )

    def __init__(self):
        self.reset()

    def reset(self):
        self.byte_len = 0
        self.frame_len = 0

    def start(self):
        self.out_ann = self.register(srd.OUTPUT_ANN)
        self.out_binary = self.register(srd.OUTPUT_BINARY)

    def put_ann(self, ss, es, ann_class, value):
        self.put(int(ss), int(es), self.out_ann, [ann_class, value])

    def put_header(self, ss_header, es_header, value):
        ss = ss_header
        es = ss + 3 * self.bit_len
        tag = (value & 0xE000) >> 13
        self.put_ann(ss, es, ann_header_tag, ['{:02X}'.format(tag)])

        ss = es
        es = ss + 5 * self.bit_len
        cmd_id = (value & 0x1F00) >> 8
        cmd_name, self.addr_len, self.data_len = \
            command_codes.get(cmd_id, ('Reserved ({:02X})'.format(cmd_id), 0, 0))
        self.frame_len = 2 + 2 + self.addr_len + self.data_len  # +Header +CRC
        self.put_ann(ss, es, ann_header_cmd, [cmd_name])

        # Bits 4..7 are reserved and should be 0, warn if they're not
        ss = es
        es = ss + 4 * self.bit_len
        reserved_bits = (value & 0x00F0) >> 4
        if reserved_bits > 0:
            self.put_ann(ss, es, ann_warning, ['Reserved bits #4..7 should be 0'])

        ss = es
        es = ss + 3 * self.bit_len
        ch = (value & 0x000E) >> 1  # See tc27xD_um_v2.2.pdf, Table 20-1
        self.put_ann(ss, es, ann_header_ch, [str(ch)])

        # Bit 0 is reserved and should be 0, warn if it's not
        if (value & 0x0001) == 0x0001:
            ss = es
            es = ss + self.bit_len
            self.put_ann(ss, es, ann_warning, ['Reserved bit #0 should be 0'])

    def put_payload(self, data):
        byte_idx = 0
        if self.addr_len > 0:
            for value_tuple in data[:self.addr_len]:
                ss, es, value = value_tuple
                self.put_ann(ss, es, ann_address, ['{:02X}'.format(value)])
            byte_idx = self.addr_len

        if self.data_len > 0:
            for value_tuple in data[byte_idx:]:
                ss, es, value = value_tuple
                self.put_ann(ss, es, ann_data, ['{:02X}'.format(value)])

    def put_crc(self, ss, es, crc_value, crc_payload_data):
        crc_payload = []
        for value_tuple in crc_payload_data:
            crc_payload.append(value_tuple[2])

        calculated_crc = crc_hqx(bytes(crc_payload), 0xFFFF)

        if calculated_crc == crc_value:
            self.put_ann(ss, es, ann_crc, ['CRC OK'])
        else:
            self.put_ann(ss, es, ann_crc, ['Have {:02X} but calculated {:02X}'.format(crc_value, calculated_crc)])
            self.put_ann(ss, es, ann_warning, ['CRC mismatch'])

    def decode(self, ss, es, data):
        if len(data) == 1:
            self.put_ann(ss, es, ann_warning, ['Header too short'])
            return

        # ss and es are now unused, we use them as local variables instead

        self.bit_len = (data[0][1] - data[0][0]) / 8.0

        byte_idx = 0

        ss = data[byte_idx][0]
        es = data[byte_idx + 1][1]
        self.put_header(ss, es, (data[byte_idx][2] << 8) + data[byte_idx + 1][2])
        byte_idx += 2

        payload_len = self.frame_len - 2 - 2  # -Header -CRC
        if payload_len > 0:
            self.put_payload(data[byte_idx:-2])
            byte_idx += payload_len

        ss = data[byte_idx][0]
        es = data[byte_idx + 1][1]
        if byte_idx == len(data) - 2:
            # CRC is calculated over header + payload bytes
            self.put_crc(ss, es, (data[byte_idx][2] << 8) + data[byte_idx + 1][2], data[0:-2])
        else:
            self.put_ann(ss, es, ann_warning, ['CRC incomplete or missing'])
