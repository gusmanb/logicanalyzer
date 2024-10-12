##
## This file is part of the libsigrokdecode project.
##
## Copyright (C) 2016 Robert Bosch Car Multimedia GmbH
## Authors: Oleksij Rempel
##              <fixed-term.Oleksij.Rempel@de.bosch.com>
##              <linux@rempel-privat.de>
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

class Decoder(srd.Decoder):
    api_version = 3
    id = 'ssi32'
    name = 'SSI32'
    longname = 'Synchronous Serial Interface (32bit)'
    desc = 'Synchronous Serial Interface (32bit) protocol.'
    license = 'gplv2+'
    inputs = ['spi']
    outputs = []
    tags = ['Embedded/industrial']
    options = (
        {'id': 'msgsize', 'desc': 'Message size', 'default': 64},
    )
    annotations = (
        ('ctrl-tx', 'CTRL TX'),
        ('ack-tx', 'ACK TX'),
        ('ctrl-rx', 'CTRL RX'),
        ('ack-rx', 'ACK RX'),
    )
    annotation_rows = (
        ('tx', 'TX', (0, 1)),
        ('rx', 'RX', (2, 3)),
    )

    def __init__(self):
        self.reset()

    def reset(self):
        self.ss_cmd, self.es_cmd = 0, 0
        self.mosi_bytes = []
        self.miso_bytes = []
        self.es_array = []
        self.rx_size = 0
        self.tx_size = 0

    def start(self):
        self.out_ann = self.register(srd.OUTPUT_ANN)

    def putx(self, data):
        self.put(self.ss_cmd, self.es_cmd, self.out_ann, data)

    def reset_data(self):
        self.mosi_bytes = []
        self.miso_bytes = []
        self.es_array = []

    def handle_ack(self):
        # Only first byte should have ACK data, other 3 bytes are reserved.
        self.es_cmd = self.es_array[0]
        self.putx([1, ['> ACK:0x%02x' % (self.mosi_bytes[0])]])
        self.putx([3, ['< ACK:0x%02x' % (self.miso_bytes[0])]])

    def handle_ctrl(self):
        mosi = miso = ''
        self.tx_size = self.mosi_bytes[2]
        self.rx_size = self.miso_bytes[2]

        if self.tx_size > 0:
            mosi = ', DATA:0x' + ''.join(format(x, '02x') for x in self.mosi_bytes[4:self.tx_size + 4])
        if self.rx_size > 0:
            miso = ', DATA:0x' + ''.join(format(x, '02x') for x in self.miso_bytes[4:self.rx_size + 4])

        self.es_cmd = self.es_array[self.tx_size + 3]
        self.putx([0, ['> CTRL:0x%02x, LUN:0x%02x, SIZE:0x%02x, CRC:0x%02x%s'
                   % (self.mosi_bytes[0], self.mosi_bytes[1],
                      self.mosi_bytes[2], self.mosi_bytes[3], mosi)]])

        self.es_cmd = self.es_array[self.rx_size + 3]
        self.putx([2, ['< CTRL:0x%02x, LUN:0x%02x, SIZE:0x%02x, CRC:0x%02x%s'
                   % (self.miso_bytes[0], self.miso_bytes[1],
                      self.miso_bytes[2], self.miso_bytes[3], miso)]])

    def decode(self, ss, es, data):
        ptype = data[0]
        if ptype == 'CS-CHANGE':
            self.reset_data()
            return

        # Don't care about anything else.
        if ptype != 'DATA':
            return
        mosi, miso = data[1:]

        self.ss, self.es = ss, es

        if len(self.mosi_bytes) == 0:
            self.ss_cmd = ss
        self.mosi_bytes.append(mosi)
        self.miso_bytes.append(miso)
        self.es_array.append(es)

        if self.mosi_bytes[0] & 0x80:
            if len(self.mosi_bytes) < 4:
                return

            self.handle_ack()
            self.reset_data()
        else:
            if len(self.mosi_bytes) < self.options['msgsize']:
                return

            self.handle_ctrl()
            self.reset_data()
