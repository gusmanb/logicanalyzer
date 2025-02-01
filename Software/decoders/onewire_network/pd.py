##
## This file is part of the libsigrokdecode project.
##
## Copyright (C) 2012 Iztok Jeras <iztok.jeras@gmail.com>
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

# Dictionary of ROM commands and their names, next state.
command = {
    0x33: ['Read ROM'                  , 'GET ROM'   ],
    0x0f: ['Conditional read ROM'      , 'GET ROM'   ],
    0xcc: ['Skip ROM'                  , 'TRANSPORT' ],
    0x55: ['Match ROM'                 , 'GET ROM'   ],
    0xf0: ['Search ROM'                , 'SEARCH ROM'],
    0xec: ['Conditional search ROM'    , 'SEARCH ROM'],
    0x3c: ['Overdrive skip ROM'        , 'TRANSPORT' ],
    0x69: ['Overdrive match ROM'       , 'GET ROM'   ],
    0xa5: ['Resume'                    , 'TRANSPORT' ],
    0x96: ['DS2408: Disable Test Mode' , 'GET ROM'   ],
}

class Decoder(srd.Decoder):
    api_version = 3
    id = 'onewire_network'
    name = '1-Wire network layer'
    longname = '1-Wire serial communication bus (network layer)'
    desc = 'Bidirectional, half-duplex, asynchronous serial bus.'
    license = 'gplv2+'
    inputs = ['onewire_link']
    outputs = ['onewire_network']
    tags = ['Embedded/industrial']
    annotations = (
        ('text', 'Text'),
    )

    def __init__(self):
        self.reset()

    def reset(self):
        self.ss_block = 0
        self.es_block = 0
        self.state = 'COMMAND'
        self.bit_cnt = 0
        self.search = 'P'
        self.data_p = 0x0
        self.data_n = 0x0
        self.data = 0x0
        self.rom = 0x0000000000000000

    def start(self):
        self.out_python = self.register(srd.OUTPUT_PYTHON)
        self.out_ann = self.register(srd.OUTPUT_ANN)

    def putx(self, data):
        # Helper function for most annotations.
        self.put(self.ss_block, self.es_block, self.out_ann, data)

    def puty(self, data):
        # Helper function for most protocol packets.
        self.put(self.ss_block, self.es_block, self.out_python, data)

    def decode(self, ss, es, data):
        code, val = data

        # State machine.
        if code == 'RESET/PRESENCE':
            self.search = 'P'
            self.bit_cnt = 0
            self.put(ss, es, self.out_ann,
                     [0, ['Reset/presence: %s' % ('true' if val else 'false')]])
            self.put(ss, es, self.out_python, ['RESET/PRESENCE', val])
            self.state = 'COMMAND'
            return

        # For now we're only interested in 'RESET/PRESENCE' and 'BIT' packets.
        if code != 'BIT':
            return

        if self.state == 'COMMAND':
            # Receiving and decoding a ROM command.
            if self.onewire_collect(8, val, ss, es) == 0:
                return
            if self.data in command:
                self.putx([0, ['ROM command: 0x%02x \'%s\''
                          % (self.data, command[self.data][0])]])
                self.state = command[self.data][1]
            else:
                self.putx([0, ['ROM command: 0x%02x \'%s\''
                          % (self.data, 'unrecognized')]])
                self.state = 'COMMAND ERROR'
        elif self.state == 'GET ROM':
            # A 64 bit device address is selected.
            # Family code (1 byte) + serial number (6 bytes) + CRC (1 byte)
            if self.onewire_collect(64, val, ss, es) == 0:
                return
            self.rom = self.data & 0xffffffffffffffff
            self.putx([0, ['ROM: 0x%016x' % self.rom]])
            self.puty(['ROM', self.rom])
            self.state = 'TRANSPORT'
        elif self.state == 'SEARCH ROM':
            # A 64 bit device address is searched for.
            # Family code (1 byte) + serial number (6 bytes) + CRC (1 byte)
            if self.onewire_search(64, val, ss, es) == 0:
                return
            self.rom = self.data & 0xffffffffffffffff
            self.putx([0, ['ROM: 0x%016x' % self.rom]])
            self.puty(['ROM', self.rom])
            self.state = 'TRANSPORT'
        elif self.state == 'TRANSPORT':
            # The transport layer is handled in byte sized units.
            if self.onewire_collect(8, val, ss, es) == 0:
                return
            self.putx([0, ['Data: 0x%02x' % self.data]])
            self.puty(['DATA', self.data])
        elif self.state == 'COMMAND ERROR':
            # Since the command is not recognized, print raw data.
            if self.onewire_collect(8, val, ss, es) == 0:
                return
            self.putx([0, ['ROM error data: 0x%02x' % self.data]])

    # Data collector.
    def onewire_collect(self, length, val, ss, es):
        # Storing the sample this sequence begins with.
        if self.bit_cnt == 0:
            self.ss_block = ss
        self.data = self.data & ~(1 << self.bit_cnt) | (val << self.bit_cnt)
        self.bit_cnt += 1
        # Storing the sample this sequence ends with.
        # In case the full length of the sequence is received, return 1.
        if self.bit_cnt == length:
            self.es_block = es
            self.data = self.data & ((1 << length) - 1)
            self.bit_cnt = 0
            return 1
        else:
            return 0

    # Search collector.
    def onewire_search(self, length, val, ss, es):
        # Storing the sample this sequence begins with.
        if (self.bit_cnt == 0) and (self.search == 'P'):
            self.ss_block = ss

        if self.search == 'P':
            # Master receives an original address bit.
            self.data_p = self.data_p & ~(1 << self.bit_cnt) | \
                          (val << self.bit_cnt)
            self.search = 'N'
        elif self.search == 'N':
            # Master receives a complemented address bit.
            self.data_n = self.data_n & ~(1 << self.bit_cnt) | \
                          (val << self.bit_cnt)
            self.search = 'D'
        elif self.search == 'D':
            # Master transmits an address bit.
            self.data = self.data & ~(1 << self.bit_cnt) | (val << self.bit_cnt)
            self.search = 'P'
            self.bit_cnt += 1

        # Storing the sample this sequence ends with.
        # In case the full length of the sequence is received, return 1.
        if self.bit_cnt == length:
            self.es_block = es
            self.data_p = self.data_p & ((1 << length) - 1)
            self.data_n = self.data_n & ((1 << length) - 1)
            self.data = self.data & ((1 << length) - 1)
            self.search = 'P'
            self.bit_cnt = 0
            return 1
        else:
            return 0
