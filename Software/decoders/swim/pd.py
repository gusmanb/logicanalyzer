##
## This file is part of the libsigrokdecode project.
##
## Copyright (C) 2018 Mike Jagdis <mjagdis@eris-associates.co.uk>
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

import math
import sigrokdecode as srd

class SamplerateError(Exception):
    pass

class Decoder(srd.Decoder):
    api_version = 3
    id = 'swim'
    name = 'SWIM'
    longname = 'STM8 SWIM bus'
    desc = 'STM8 Single Wire Interface Module (SWIM) protocol.'
    license = 'gplv2+'
    inputs = ['logic']
    outputs = []
    tags = ['Debug/trace']
    options = (
        {'id': 'debug', 'desc': 'Debug', 'default': 'no', 'values': ('yes', 'no') },
    )
    channels = (
        {'id': 'swim', 'name': 'SWIM', 'desc': 'SWIM data line'},
    )
    annotations = (
        ('bit', 'Bit'),
        ('enterseq', 'SWIM enter sequence'),
        ('start-host', 'Start bit (host)'),
        ('start-target', 'Start bit (target)'),
        ('parity', 'Parity bit'),
        ('ack', 'Acknowledgement'),
        ('nack', 'Negative acknowledgement'),
        ('byte-write', 'Byte write'),
        ('byte-read', 'Byte read'),
        ('cmd-unknown', 'Unknown SWIM command'),
        ('cmd', 'SWIM command'),
        ('bytes', 'Byte count'),
        ('address', 'Address'),
        ('data-write', 'Data write'),
        ('data-read', 'Data read'),
        ('debug-msg', 'Debug message'),
    )
    annotation_rows = (
        ('bits', 'Bits', (0,)),
        ('framing', 'Framing', (2, 3, 4, 5, 6, 7, 8)),
        ('protocol', 'Protocol', (1, 9, 10, 11, 12, 13, 14)),
        ('debug', 'Debug', (15,)),
    )
    binary = (
        ('tx', 'Dump of data written to target'),
        ('rx', 'Dump of data read from target'),
    )

    def __init__(self):
        # SWIM clock for the target is normally HSI/2 where HSI is 8MHz +- 5%
        # although the divisor can be removed by setting the SWIMCLK bit in
        # the CLK_SWIMCCR register. There is no standard for the host so we
        # will be generous and assume it is using an 8MHz +- 10% oscillator.
        # We do not need to be accurate. We just need to avoid treating enter
        # sequence pulses as bits. A synchronization frame will cause this
        # to be adjusted.
        self.HSI = 8000000
        self.HSI_min = self.HSI * 0.9
        self.HSI_max = self.HSI * 1.1
        self.swim_clock = self.HSI_min / 2

        self.eseq_edge = [[-1, None], [-1, None]]
        self.eseq_pairnum = 0
        self.eseq_pairstart = None

        self.reset()

    def reset(self):
        self.bit_edge = [[-1, None], [-1, None]]
        self.bit_maxlen = -1
        self.bitseq_len = 0
        self.bitseq_end = None
        self.proto_state = 'CMD'

    def metadata(self, key, value):
        if key == srd.SRD_CONF_SAMPLERATE:
            self.samplerate = value

    def adjust_timings(self):
        # A low-speed bit is 22 SWIM clocks long.
        # There are options to shorten bits to 10 clocks or use HSI rather
        # than HSI/2 as the SWIM clock but the longest valid bit should be no
        # more than this many samples. This does not need to be accurate.
        # It exists simply to prevent bits extending unecessarily far into
        # trailing bus-idle periods. This will be adjusted every time we see
        # a synchronization frame or start bit in order to show idle periods
        # as accurately as possible.
        self.bit_reflen = math.ceil(self.samplerate * 22 / self.swim_clock)

    def start(self):
        self.out_ann = self.register(srd.OUTPUT_ANN)
        self.out_binary = self.register(srd.OUTPUT_BINARY)

        if not self.samplerate:
            raise SamplerateError('Cannot decode without samplerate.')

        # A synchronization frame is a low that lasts for more than 64 but no
        # more than 128 SWIM clock periods based on the standard SWIM clock.
        # Note: we also allow for the possibility that the SWIM clock divisor
        # has been disabled here.
        self.sync_reflen_min = math.floor(self.samplerate * 64 / self.HSI_max)
        self.sync_reflen_max = math.ceil(self.samplerate * 128 / (self.HSI_min / 2))

        self.debug = True if self.options['debug'] == 'yes' else False

        # The SWIM entry sequence is 4 pulses at 2kHz followed by 4 at 1kHz.
        self.eseq_reflen = math.ceil(self.samplerate / 2048)

        self.adjust_timings()

    def protocol(self):
        if self.proto_state == 'CMD':
            # Command
            if self.bitseq_value == 0x00:
                self.put(self.bitseq_start, self.bitseq_end, self.out_ann, [10, ['system reset', 'SRST', '!']])
            elif self.bitseq_value == 0x01:
                self.proto_state = 'N'
                self.put(self.bitseq_start, self.bitseq_end, self.out_ann, [10, ['read on-the-fly', 'ROTF', 'r']])
            elif self.bitseq_value == 0x02:
                self.proto_state = 'N'
                self.put(self.bitseq_start, self.bitseq_end, self.out_ann, [10, ['write on-the-fly', 'WOTF', 'w']])
            else:
                self.put(self.bitseq_start, self.bitseq_end, self.out_ann, [9, ['unknown', 'UNK']])
        elif self.proto_state == 'N':
            # Number of bytes
            self.proto_byte_count = self.bitseq_value
            self.proto_state = '@E'
            self.put(self.bitseq_start, self.bitseq_end, self.out_ann, [11, ['byte count 0x%02x' % self.bitseq_value, 'bytes 0x%02x' % self.bitseq_value, '0x%02x' % self.bitseq_value, '%02x' % self.bitseq_value, '%x' % self.bitseq_value]])
        elif self.proto_state == '@E':
            # Address byte 1
            self.proto_addr = self.bitseq_value
            self.proto_addr_start = self.bitseq_start
            self.proto_state = '@H'
        elif self.proto_state == '@H':
            # Address byte 2
            self.proto_addr = (self.proto_addr << 8) | self.bitseq_value
            self.proto_state = '@L'
        elif self.proto_state == '@L':
            # Address byte 3
            self.proto_addr = (self.proto_addr << 8) | self.bitseq_value
            self.proto_state = 'D'
            self.put(self.proto_addr_start, self.bitseq_end, self.out_ann, [12, ['address 0x%06x' % self.proto_addr, 'addr 0x%06x' % self.proto_addr, '0x%06x' % self.proto_addr, '%06x' %self.proto_addr, '%x' % self.proto_addr]])
        else:
            if self.proto_byte_count > 0:
                self.proto_byte_count -= 1
                if self.proto_byte_count == 0:
                    self.proto_state = 'CMD'

            self.put(self.bitseq_start, self.bitseq_end, self.out_ann, [13 + self.bitseq_dir, ['0x%02x' % self.bitseq_value, '%02x' % self.bitseq_value, '%x' % self.bitseq_value]])
            self.put(self.bitseq_start, self.bitseq_end, self.out_binary, [0 + self.bitseq_dir, bytes([self.bitseq_value])])
            if self.debug:
                self.put(self.bitseq_start, self.bitseq_end, self.out_ann, [15, ['%d more' % self.proto_byte_count, '%d' % self.proto_byte_count]])

    def bitseq(self, bitstart, bitend, bit):
        if self.bitseq_len == 0:
            # Looking for start of a bit sequence (command or byte).
            self.bit_reflen = bitend - bitstart
            self.bitseq_value = 0
            self.bitseq_dir = bit
            self.bitseq_len = 1
            self.put(bitstart, bitend, self.out_ann, [2 + self.bitseq_dir, ['start', 's']])
        elif (self.proto_state == 'CMD' and self.bitseq_len == 4) or (self.proto_state != 'CMD' and self.bitseq_len == 9):
            # Parity bit
            self.bitseq_end = bitstart
            self.bitseq_len += 1

            self.put(bitstart, bitend, self.out_ann, [4, ['parity', 'par', 'p']])

            # The start bit is not data but was used for parity calculation.
            self.bitseq_value &= 0xff
            self.put(self.bitseq_start, self.bitseq_end, self.out_ann, [7 + self.bitseq_dir, ['0x%02x' % self.bitseq_value, '%02x' % self.bitseq_value, '%x' % self.bitseq_value]])
        elif (self.proto_state == 'CMD' and self.bitseq_len == 5) or (self.proto_state != 'CMD' and self.bitseq_len == 10):
            # ACK/NACK bit.
            if bit:
                self.put(bitstart, bitend, self.out_ann, [5, ['ack', 'a']])
            else:
                self.put(bitstart, bitend, self.out_ann, [6, ['nack', 'n']])

            # We only pass data that was ack'd up the stack.
            if bit:
                self.protocol()

            self.bitseq_len = 0
        else:
            if self.bitseq_len == 1:
                self.bitseq_start = bitstart
            self.bitseq_value = (self.bitseq_value << 1) | bit
            self.bitseq_len += 1

    def bit(self, start, mid, end):
        if mid - start >= end - mid:
            self.put(start, end, self.out_ann, [0, ['0']])
            bit = 0
        else:
            self.put(start, end, self.out_ann, [0, ['1']])
            bit = 1

        self.bitseq(start, end, bit)

    def detect_synchronize_frame(self, start, end):
        # Strictly speaking, synchronization frames are only recognised when
        # SWIM is active. A falling edge on reset disables SWIM and an enter
        # sequence is needed to re-enable it. However we do not want to be
        # reliant on seeing the NRST pin just for that and we also want to be
        # able to decode SWIM even if we just sample parts of the dialogue.
        # For this reason we limit ourselves to only recognizing
        # synchronization frames that have believable lengths based on our
        # knowledge of the range of possible SWIM clocks.
        if self.samplenum - self.eseq_edge[1][1] >= self.sync_reflen_min and self.samplenum - self.eseq_edge[1][1] <= self.sync_reflen_max:
            self.put(self.eseq_edge[1][1], self.samplenum, self.out_ann, [1, ['synchronization frame', 'synchronization', 'sync', 's']])

            # A low that lasts for more than 64 SWIM clock periods causes a
            # reset of the SWIM communication state machine and will switch
            # the SWIM to low-speed mode (SWIM_CSR.HS is cleared).
            self.reset()

            # The low SHOULD last 128 SWIM clocks. This is used to
            # resynchronize in order to allow for variation in the frequency
            # of the internal RC oscillator.
            self.swim_clock = 128 * (self.samplerate / (self.samplenum - self.eseq_edge[1][1]))
            self.adjust_timings()

    def eseq_potential_start(self, start, end):
        self.eseq_pairstart = start
        self.eseq_reflen = end - start
        self.eseq_pairnum = 1

    def detect_enter_sequence(self, start, end):
        # According to the spec the enter sequence is four pulses at 2kHz
        # followed by four at 1kHz. We do not check the frequency but simply
        # check the lengths of successive pulses against the first. This means
        # we have no need to account for the accuracy (or lack of) of the
        # host's oscillator.
        if self.eseq_pairnum == 0 or abs(self.eseq_reflen - (end - start)) > 2:
            self.eseq_potential_start(start, end)

        elif self.eseq_pairnum < 4:
            # The next three pulses should be the same length as the first.
            self.eseq_pairnum += 1

            if self.eseq_pairnum == 4:
                self.eseq_reflen /= 2
        else:
            # The final four pulses should each be half the length of the
            # initial pair. Again, a mismatch causes us to reset and use the
            # current pulse as a new potential enter sequence start.
            self.eseq_pairnum += 1
            if self.eseq_pairnum == 8:
                # Four matching pulses followed by four more that match each
                # other but are half the length of the first 4. SWIM is active!
                self.put(self.eseq_pairstart, end, self.out_ann, [1, ['enter sequence', 'enter seq', 'enter', 'ent', 'e']])
                self.eseq_pairnum = 0

    def decode(self):
        while True:
            if self.bit_maxlen >= 0:
                (swim,) = self.wait()
                self.bit_maxlen -= 1
            else:
                (swim,) = self.wait({0: 'e'})

            if swim != self.eseq_edge[1][0]:
                if swim == 1 and self.eseq_edge[1][1] is not None:
                    self.detect_synchronize_frame(self.eseq_edge[1][1], self.samplenum)
                    if self.eseq_edge[0][1] is not None:
                        self.detect_enter_sequence(self.eseq_edge[0][1], self.samplenum)
                self.eseq_edge.pop(0)
                self.eseq_edge.append([swim, self.samplenum])

            if (swim != self.bit_edge[1][0] and (swim != 1 or self.bit_edge[1][0] != -1)) or self.bit_maxlen == 0:
                if self.bit_maxlen == 0 and self.bit_edge[1][0] == 1:
                    swim = -1

                if self.bit_edge[1][0] != 0 and swim == 0:
                    self.bit_maxlen = self.bit_reflen

                if self.bit_edge[0][0] == 0 and self.bit_edge[1][0] == 1 and self.samplenum - self.bit_edge[0][1] <= self.bit_reflen + 2:
                    self.bit(self.bit_edge[0][1], self.bit_edge[1][1], self.samplenum)

                self.bit_edge.pop(0)
                self.bit_edge.append([swim, self.samplenum])
