##
## This file is part of the libsigrokdecode project.
##
## Copyright (C) 2019 Stephan Thiele <stephan.thiele@mailbox.org>
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

# Selection of constants as defined in FlexRay specification 3.0.1 Chapter A.1:
class Const:
    cChannelIdleDelimiter = 11
    cCrcInitA = 0xFEDCBA
    cCrcInitB = 0xABCDEF
    cCrcPolynomial = 0x5D6DCB
    cCrcSize = 24
    cCycleCountMax = 63
    cdBSS = 2
    cdCAS = 30
    cdFES = 2
    cdFSS = 1
    cHCrcInit = 0x01A
    cHCrcPolynomial = 0x385
    cHCrcSize = 11
    cSamplesPerBit = 8
    cSlotIDMax = 2047
    cStaticSlotIDMax = 1023
    cVotingSamples = 5

class SamplerateError(Exception):
    pass

class Decoder(srd.Decoder):
    api_version = 3
    id = 'flexray'
    name = 'FlexRay'
    longname = 'FlexRay'
    desc = 'Automotive network communications protocol.'
    license = 'gplv2+'
    inputs = ['logic']
    outputs = []
    tags = ['Automotive']
    channels = (
        {'id': 'channel', 'name': 'Channel', 'desc': 'FlexRay bus channel'},
    )
    options = (
        {'id': 'channel_type', 'desc': 'Channel type', 'default': 'A',
            'values': ('A', 'B')},
        {'id': 'bitrate', 'desc': 'Bitrate (bit/s)', 'default': 10000000,
            'values': (10000000, 5000000, 2500000)},
    )
    annotations = (
        ('data', 'FlexRay payload data'),
        ('tss', 'Transmission start sequence'),
        ('fss', 'Frame start sequence'),
        ('reserved-bit', 'Reserved bit'),
        ('ppi', 'Payload preamble indicator'),
        ('null-frame', 'Nullframe indicator'),
        ('sync-frame', 'Full identifier'),
        ('startup-frame', 'Startup frame indicator'),
        ('id', 'Frame ID'),
        ('length', 'Data length'),
        ('header-crc', 'Header CRC'),
        ('cycle', 'Cycle code'),
        ('data-byte', 'Data byte'),
        ('frame-crc', 'Frame CRC'),
        ('fes', 'Frame end sequence'),
        ('bss', 'Byte start sequence'),
        ('warning', 'Warning'),
        ('bit', 'Bit'),
        ('cid', 'Channel idle delimiter'),
        ('dts', 'Dynamic trailing sequence'),
        ('cas', 'Collision avoidance symbol'),
    )
    annotation_rows = (
        ('bits', 'Bits', (15, 17)),
        ('fields', 'Fields', tuple(range(15)) + (18, 19, 20)),
        ('warnings', 'Warnings', (16,)),
    )

    def __init__(self):
        self.reset()

    def reset(self):
        self.samplerate = None
        self.reset_variables()

    def start(self):
        self.out_ann = self.register(srd.OUTPUT_ANN)

    def metadata(self, key, value):
        if key == srd.SRD_CONF_SAMPLERATE:
            bitrate = float(self.options['bitrate'])
            self.samplerate = value
            self.bit_width = float(self.samplerate) / bitrate
            self.sample_point = (self.bit_width / 100.0) * self.sample_point_percent

    # Generic helper for FlexRay bit annotations.
    def putg(self, ss, es, data):
        left, right = int(self.sample_point), int(self.bit_width - self.sample_point)
        self.put(ss - left, es + right, self.out_ann, data)

    # Single-FlexRay-bit annotation using the current samplenum.
    def putx(self, data):
        self.putg(self.samplenum, self.samplenum, data)

    # Multi-FlexRay-bit annotation from self.ss_block to current samplenum.
    def putb(self, data):
        self.putg(self.ss_block, self.samplenum, data)

    # Generic CRC algorithm for any bit size and any data length. Used for
    # 11-bit header and 24-bit trailer. Not very efficient but at least it
    # works for now.
    #
    # TODO:
    # - use precalculated tables to increase performance.
    # - Add support for reverse CRC calculations.

    @staticmethod
    def crc(data, data_len_bits, polynom, crc_len_bits, iv=0, xor=0):
        reg = iv ^ xor

        for i in range(data_len_bits - 1, -1, -1):
            bit = ((reg >> (crc_len_bits - 1)) & 0x1) ^ ((data >> i) & 0x1)
            reg <<= 1
            if bit:
                reg ^= polynom

        mask = (1 << crc_len_bits) - 1
        crc = reg & mask

        return crc ^ xor

    def reset_variables(self):
        self.sample_point_percent = 50 # TODO: use vote based sampling
        self.state = 'IDLE'
        self.tss_start = self.tss_end = self.frame_type = self.dlc = None
        self.rawbits = [] # All bits, including byte start sequence bits
        self.bits = [] # Only actual FlexRay frame bits (no byte start sequence bits)
        self.curbit = 0 # Current bit of FlexRay frame (bit 0 == FSS)
        self.last_databit = 999 # Positive value that bitnum+x will never match
        self.last_xmit_bit = 999 # Positive value that bitnum+x will never match
        self.ss_block = None
        self.ss_databytebits = []
        self.end_of_frame = False
        self.dynamic_frame = False
        self.ss_bit0 = None
        self.ss_bit1 = None
        self.ss_bit2 = None

    # Poor man's clock synchronization. Use signal edges which change to
    # dominant state in rather simple ways. This naive approach is neither
    # aware of the SYNC phase's width nor the specific location of the edge,
    # but improves the decoder's reliability when the input signal's bitrate
    # does not exactly match the nominal rate.
    def dom_edge_seen(self, force=False):
        self.dom_edge_snum = self.samplenum
        self.dom_edge_bcount = self.curbit

    # Determine the position of the next desired bit's sample point.
    def get_sample_point(self, bitnum):
        samplenum = self.dom_edge_snum
        samplenum += self.bit_width * (bitnum - self.dom_edge_bcount)
        samplenum += self.sample_point
        return int(samplenum)

    def is_bss_sequence(self):
        # FlexRay uses NRZ encoding and adds a binary 10 sequence before each
        # byte. After each 8 data bits, a BSS sequence is added but not after
        # frame CRC.

        if self.end_of_frame:
          return False

        if (len(self.rawbits) - 2) % 10 == 0:
            return True
        elif (len(self.rawbits) - 3) % 10 == 0:
            return True

        return False

    def handle_bit(self, fr_rx):
        self.rawbits.append(fr_rx)
        self.bits.append(fr_rx)

        # Get the index of the current FlexRay frame bit.
        bitnum = len(self.bits) - 1

        # If this is a byte start sequence remove it from self.bits and ignore it.
        if self.is_bss_sequence():
            self.bits.pop()

            if bitnum > 1:
                self.putx([15, [str(fr_rx)]])
            else:
                if len(self.rawbits) == 2:
                    self.ss_bit1 = self.samplenum
                elif len(self.rawbits) == 3:
                    self.ss_bit2 = self.samplenum

            self.curbit += 1 # Increase self.curbit (bitnum is not affected).
            return
        else:
            if bitnum > 1:
                self.putx([17, [str(fr_rx)]])

        # Bit 0: Frame start sequence (FSS) bit
        if bitnum == 0:
            self.ss_bit0 = self.samplenum

        # Bit 1: Start of header
        elif bitnum == 1:
            if self.rawbits[:3] == [1, 1, 0]:
                self.put(self.tss_start, self.tss_end, self.out_ann,
                        [1, ['Transmission start sequence', 'TSS']])

                self.putg(self.ss_bit0, self.ss_bit0, [17, [str(self.rawbits[:3][0])]])
                self.putg(self.ss_bit0, self.ss_bit0, [2,  ['FSS', 'Frame start sequence']])
                self.putg(self.ss_bit1, self.ss_bit1, [15, [str(self.rawbits[:3][1])]])
                self.putg(self.ss_bit2, self.ss_bit2, [15, [str(self.rawbits[:3][2])]])
                self.putx([17, [str(fr_rx)]])
                self.putx([3, ['Reserved bit: %d' % fr_rx, 'RB: %d' % fr_rx, 'RB']])
            else:
                self.put(self.tss_start, self.tss_end, self.out_ann,
                        [20, ['Collision avoidance symbol', 'CAS']])
                self.reset_variables()

            # TODO: warning, if sequence is neither [1, 1, 0] nor [1, 1, 1]

        # Bit 2: Payload preamble indicator. Must be 0 if null frame indicator is 0.
        elif bitnum == 2:
            self.putx([4, ['Payload preamble indicator: %d' % fr_rx,
                           'PPI: %d' % fr_rx]])

        # Bit 3: Null frame indicator (inversed)
        elif bitnum == 3:
            data_type = 'data frame' if fr_rx else 'null frame'
            self.putx([5, ['Null frame indicator: %s' % data_type,
                           'NF: %d' % fr_rx, 'NF']])

        # Bit 4: Sync frame indicator
        # Must be 1 if startup frame indicator is 1.
        elif bitnum == 4:
            self.putx([6, ['Sync frame indicator: %d' % fr_rx,
                           'Sync: %d' % fr_rx, 'Sync']])

        # Bit 5: Startup frame indicator
        elif bitnum == 5:
            self.putx([7, ['Startup frame indicator: %d' % fr_rx,
                           'Startup: %d' % fr_rx, 'Startup']])

        # Remember start of ID (see below).
        elif bitnum == 6:
            self.ss_block = self.samplenum

        # Bits 6-16: Frame identifier (ID[10..0])
        # ID must NOT be 0.
        elif bitnum == 16:
            self.id = int(''.join(str(d) for d in self.bits[6:]), 2)
            self.putb([8, ['Frame ID: %d' % self.id, 'ID: %d' % self.id,
                           '%d' % self.id]])

        # Remember start of payload length (see below).
        elif bitnum == 17:
            self.ss_block = self.samplenum

        # Bits 17-23: Payload length (Length[7..0])
        # Payload length in header is the half of the real payload size.
        elif bitnum == 23:
            self.payload_length = int(''.join(str(d) for d in self.bits[17:]), 2)
            self.putb([9, ['Payload length: %d' % self.payload_length,
                           'Length: %d' % self.payload_length,
                           '%d' % self.payload_length]])

        # Remember start of header CRC (see below).
        elif bitnum == 24:
            self.ss_block = self.samplenum

        # Bits 24-34: Header CRC (11-bit) (HCRC[11..0])
        # Calculation of header CRC is equal on both channels.
        elif bitnum == 34:
            bits = ''.join([str(b) for b in self.bits[4:24]])
            header_to_check = int(bits, 2)
            expected_crc = self.crc(header_to_check, len(bits),
                Const.cHCrcPolynomial, Const.cHCrcSize, Const.cHCrcInit)
            self.header_crc = int(''.join(str(d) for d in self.bits[24:]), 2)

            crc_ok = self.header_crc == expected_crc
            crc_ann = "OK" if crc_ok else "bad"

            self.putb([10, ['Header CRC: 0x%X (%s)' % (self.header_crc, crc_ann),
                            '0x%X (%s)' % (self.header_crc, crc_ann),
                            '0x%X' % self.header_crc]])

        # Remember start of cycle code (see below).
        elif bitnum == 35:
            self.ss_block = self.samplenum

        # Bits 35-40: Cycle code (Cyc[6..0])
        # Cycle code. Must be between 0 and 63.
        elif bitnum == 40:
            self.cycle = int(''.join(str(d) for d in self.bits[35:]), 2)
            self.putb([11, ['Cycle: %d' % self.cycle, 'Cyc: %d' % self.cycle,
                            '%d' % self.cycle]])
            self.last_databit = 41 + 2 * self.payload_length * 8

        # Remember all databyte bits, except the very last one.
        elif bitnum in range(41, self.last_databit):
            self.ss_databytebits.append(self.samplenum)

        # Bits 41-X: Data field (0-254 bytes, depending on length)
        # The bits within a data byte are transferred MSB-first.
        elif bitnum == self.last_databit:
            self.ss_databytebits.append(self.samplenum) # Last databyte bit.
            for i in range(2 * self.payload_length):
                x = 40 + (8 * i) + 1
                b = int(''.join(str(d) for d in self.bits[x:x + 8]), 2)
                ss = self.ss_databytebits[i * 8]
                es = self.ss_databytebits[((i + 1) * 8) - 1]
                self.putg(ss, es, [12, ['Data byte %d: 0x%02x' % (i, b),
                                        'DB%d: 0x%02x' % (i, b), '%02X' % b]])
            self.ss_databytebits = []
            self.ss_block = self.samplenum # Remember start of trailer CRC.

        # Trailer CRC (24-bit) (CRC[11..0])
        # Initialization vector of channel A and B are different, so CRCs are
        # different for same data.
        elif bitnum == self.last_databit + 23:
            bits = ''.join([str(b) for b in self.bits[1:-24]])
            frame_to_check = int(bits, 2)
            iv = Const.cCrcInitA if self.options['channel_type'] == 'A' else Const.cCrcInitB
            expected_crc = self.crc(frame_to_check, len(bits),
                Const.cCrcPolynomial, Const.cCrcSize, iv=iv)
            self.frame_crc = int(''.join(str(d) for d in self.bits[self.last_databit:]), 2)

            crc_ok = self.frame_crc == expected_crc
            crc_ann = "OK" if crc_ok else "bad"

            self.putb([13, ['Frame CRC: 0x%X (%s)' % (self.frame_crc, crc_ann),
                            '0x%X (%s)' % (self.frame_crc, crc_ann),
                            '0x%X' % self.frame_crc]])
            self.end_of_frame = True

        # Remember start of frame end sequence (see below).
        elif bitnum == self.last_databit + 24:
            self.ss_block = self.samplenum

        # Frame end sequence, must be 1 followed by 0.
        elif bitnum == self.last_databit + 25:
            self.putb([14, ['Frame end sequence', 'FES']])

        # Check for DTS
        elif bitnum == self.last_databit + 26:
            if not fr_rx:
                self.dynamic_frame = True
            else:
                self.last_xmit_bit = bitnum
            self.ss_block = self.samplenum

        # Remember start of channel idle delimiter (see below).
        elif bitnum == self.last_xmit_bit:
            self.ss_block = self.samplenum

        # Channel idle limiter (CID[11..0])
        elif bitnum == self.last_xmit_bit + Const.cChannelIdleDelimiter - 1:
            self.putb([18, ['Channel idle delimiter', 'CID']])
            self.reset_variables()

        # DTS if dynamic frame
        elif bitnum > self.last_databit + 27:
            if self.dynamic_frame:
                if fr_rx:
                    if self.last_xmit_bit == 999:
                        self.putb([19, ['Dynamic trailing sequence', 'DTS']])
                        self.last_xmit_bit = bitnum + 1
                        self.ss_block = self.samplenum

        self.curbit += 1

    def decode(self):
        if not self.samplerate:
            raise SamplerateError('Cannot decode without samplerate.')

        while True:
            # State machine.
            if self.state == 'IDLE':
                # Wait for a dominant state (logic 0) on the bus.
                (fr_rx,) = self.wait({0: 'l'})
                self.tss_start = self.samplenum
                (fr_rx,) = self.wait({0: 'h'})
                self.tss_end = self.samplenum
                self.dom_edge_seen(force = True)
                self.state = 'GET BITS'
            elif self.state == 'GET BITS':
                # Wait until we're in the correct bit/sampling position.
                pos = self.get_sample_point(self.curbit)
                (fr_rx,) = self.wait([{'skip': pos - self.samplenum}, {0: 'f'}])
                if self.matched[1]:
                    self.dom_edge_seen()
                if self.matched[0]:
                    self.handle_bit(fr_rx)
