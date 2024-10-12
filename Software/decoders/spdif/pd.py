##
## This file is part of the libsigrokdecode project.
##
## Copyright (C) 2014 Guenther Wenninger <robin@bitschubbser.org>
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

class SamplerateError(Exception):
    pass

class Decoder(srd.Decoder):
    api_version = 3
    id = 'spdif'
    name = 'S/PDIF'
    longname = 'Sony/Philips Digital Interface Format'
    desc = 'Serial bus for connecting digital audio devices.'
    license = 'gplv2+'
    inputs = ['logic']
    outputs = []
    tags = ['Audio', 'PC']
    channels = (
        {'id': 'data', 'name': 'Data', 'desc': 'Data line'},
    )
    annotations = (
        ('bitrate', 'Bitrate / baudrate'),
        ('preamble', 'Preamble'),
        ('bit', 'Bit'),
        ('aux', 'Auxillary-audio-databit'),
        ('sample', 'Audio Sample'),
        ('validity', 'Data Valid'),
        ('subcode', 'Subcode data'),
        ('chan_stat', 'Channnel Status'),
        ('parity', 'Parity Bit'),
    )
    annotation_rows = (
        ('bits', 'Bits', (2,)),
        ('info', 'Info', (0, 1, 3, 5, 6, 7, 8)),
        ('samples', 'Samples', (4,)),
    )

    def putx(self, ss, es, data):
        self.put(ss, es, self.out_ann, data)

    def puty(self, data):
        self.put(self.ss_edge, self.samplenum, self.out_ann, data)

    def __init__(self):
        self.reset()

    def reset(self):
        self.state = 'GET FIRST PULSE WIDTH'
        self.ss_edge = None
        self.first_edge = True
        self.samplenum_prev_edge = 0
        self.pulse_width = 0

        self.clocks = []
        self.range1 = 0
        self.range2 = 0

        self.preamble_state = 0
        self.preamble = []
        self.seen_preamble = False
        self.last_preamble = 0

        self.bitrate_message_start = 0
        self.bitrate_message_end = 0
        self.frame_counter = 0
        self.frame_start = 0
        self.frame_length = 0

        self.sampleratetmp = 1

        self.first_one = True
        self.subframe = []

    def start(self):
        self.out_ann = self.register(srd.OUTPUT_ANN)

    def metadata(self, key, value):
        if key == srd.SRD_CONF_SAMPLERATE:
            self.samplerate = value

    def get_pulse_type(self):
        if self.pulse_width >= self.range2:
            return 2
        elif self.pulse_width >= self.range1:
            return 0
        else:
            return 1

    def find_first_pulse_width(self):
        if self.pulse_width != 0:
            self.clocks.append(self.pulse_width)
            self.state = 'GET SECOND PULSE WIDTH'
            self.puty([2, ['Found width 1: %d' % self.pulse_width, 'W1: %d' % self.pulse_width]])
            self.ss_edge = self.samplenum

    def find_second_pulse_width(self):
        if self.pulse_width > (self.clocks[0] * 1.3) or \
                self.pulse_width <= (self.clocks[0] * 0.75):
            self.puty([2, ['Found width 2: %d' % self.pulse_width, 'W2: %d' % self.pulse_width]])
            self.clocks.append(self.pulse_width)
            self.state = 'GET THIRD PULSE WIDTH'
        else:
            self.puty([2, ['Search width 2: %d' % self.pulse_width, 'SW2: %d' % self.pulse_width]])
        self.ss_edge = self.samplenum

    def find_third_pulse_width(self):
        if not ((self.pulse_width > (self.clocks[0] * 1.3) or \
                self.pulse_width <= (self.clocks[0] * 0.75)) \
                and (self.pulse_width > (self.clocks[1] * 1.3) or \
                self.pulse_width <= (self.clocks[1] * 0.75))):
            self.puty([2, ['Search width 3: %d' % self.pulse_width, 'SW3: %d' % self.pulse_width]])
            self.ss_edge = self.samplenum
            return
        else:
            self.puty([2, ['Found width 3: %d' % self.pulse_width, 'W3: %d' % self.pulse_width]])
            self.ss_edge = self.samplenum
            # The message of the calculated bitrate should start at this sample
            # (right after the synchronisation).
            self.bitrate_message_start = self.samplenum

        self.clocks.append(self.pulse_width)
        self.clocks.sort()
        self.range1 = (self.clocks[0] + self.clocks[1]) / 2
        self.range2 = (self.clocks[1] + self.clocks[2]) / 2
        # Give some feedback during synchronisation and inform if sample rate
        # is too low.
        if self.clocks[0] <= 3:
            self.putx(0, self.samplenum, [0, ['Short pulses detected. Increase sample rate!']])
            raise SamplerateError('Short pulses detected')
        else:
            self.putx(0, self.samplenum, [0, ['Synchronisation']])
        self.ss_edge = 0

        # Mostly, the synchronisation ends with a long pulse because they
        # appear rarely. A skip of the next pulse will then prevent a 'M'
        # frame to be labeled an unknown preamble for the first decoded frame.
        (data,) = self.wait({0: 'e'})

        self.pulse_width = self.samplenum - self.samplenum_prev_edge
        self.samplenum_prev_edge = self.samplenum
        self.last_preamble = self.samplenum

        # We are done recovering the clock, now let's decode the data stream.
        self.state = 'DECODE STREAM'

    def decode_stream(self):
        pulse = self.get_pulse_type()

        if not self.seen_preamble:
            # This is probably the start of a preamble, decode it.
            if pulse == 2:
                self.preamble.append(self.get_pulse_type())
                self.state = 'DECODE PREAMBLE'
                self.ss_edge = self.samplenum - self.pulse_width
                # Use the first ten frames to calculate bit rates
                if self.frame_counter == 0:
                    # This is the first preamble to be decoded. Measurement of
                    # bit rates starts here.
                    self.frame_start = self.samplenum
                    # The bit rate message should end here.
                    self.bitrate_message_end = self.ss_edge
                elif self.frame_counter == 10:
                    self.frame_length = self.samplenum - self.frame_start
                    # Use section between end of synchronisation and start of
                    # first preamble to show measured bit rates.
                    if self.samplerate:
                        self.putx(self.bitrate_message_start, self.bitrate_message_end,\
                            [0, ['Audio samplingrate: %6.2f kHz; Bit rate: %6.3f MBit/s' %\
                            ((self.samplerate / 200 / self.frame_length), (self.samplerate / 200 * 64 / 1000 / self.frame_length))]])
                    else:
                        self.putx(self.bitrate_message_start, self.bitrate_message_end, [0, ['No sample rate given']])
                self.frame_counter += 1
            return

        # We've seen a preamble.
        if pulse == 1 and self.first_one:
            self.first_one = False
            self.subframe.append([pulse, self.samplenum - self.pulse_width, self.samplenum])
        elif pulse == 1 and not self.first_one:
            self.subframe[-1][2] = self.samplenum
            self.putx(self.subframe[-1][1], self.samplenum, [2, ['1']])
            self.bitcount += 1
            self.first_one = True
        else:
            self.subframe.append([pulse, self.samplenum - self.pulse_width, self.samplenum])
            self.putx(self.samplenum - self.pulse_width, self.samplenum, [2, ['0']])
            self.bitcount += 1

        if self.bitcount == 28:
            aux_audio_data = self.subframe[0:4]
            sam, sam_rot = '', ''
            for a in aux_audio_data:
                sam = sam + str(a[0])
                sam_rot = str(a[0]) + sam_rot
            sample = self.subframe[4:24]
            for s in sample:
                sam = sam + str(s[0])
                sam_rot = str(s[0]) + sam_rot
            validity = self.subframe[24:25]
            subcode_data = self.subframe[25:26]
            channel_status = self.subframe[26:27]
            parity = self.subframe[27:28]

            self.putx(aux_audio_data[0][1], aux_audio_data[3][2], \
                      [3, ['Aux 0x%x' % int(sam, 2), '0x%x' % int(sam, 2)]])
            self.putx(sample[0][1], sample[19][2], \
                      [3, ['Sample 0x%x' % int(sam, 2), '0x%x' % int(sam, 2)]])
            self.putx(aux_audio_data[0][1], sample[19][2], \
                      [4, ['Audio 0x%x' % int(sam_rot, 2), '0x%x' % int(sam_rot, 2)]])
            if validity[0][0] == 0:
                self.putx(validity[0][1], validity[0][2], [5, ['V']])
            else:
                self.putx(validity[0][1], validity[0][2], [5, ['E']])
            self.putx(subcode_data[0][1], subcode_data[0][2],
                [6, ['S: %d' % subcode_data[0][0]]])
            self.putx(channel_status[0][1], channel_status[0][2],
                [7, ['C: %d' % channel_status[0][0]]])
            self.putx(parity[0][1], parity[0][2], [8, ['P: %d' % parity[0][0]]])

            self.subframe = []
            self.seen_preamble = False
            self.bitcount = 0

    def decode_preamble(self):
        if self.preamble_state == 0:
            self.preamble.append(self.get_pulse_type())
            self.preamble_state = 1
        elif self.preamble_state == 1:
            self.preamble.append(self.get_pulse_type())
            self.preamble_state = 2
        elif self.preamble_state == 2:
            self.preamble.append(self.get_pulse_type())
            self.preamble_state = 0
            self.state = 'DECODE STREAM'
            if self.preamble == [2, 0, 1, 0]:
                self.puty([1, ['Preamble W', 'W']])
            elif self.preamble == [2, 2, 1, 1]:
                self.puty([1, ['Preamble M', 'M']])
            elif self.preamble == [2, 1, 1, 2]:
                self.puty([1, ['Preamble B', 'B']])
            else:
                self.puty([1, ['Unknown Preamble', 'Unknown Prea.', 'U']])
            self.preamble = []
            self.seen_preamble = True
            self.bitcount = 0
            self.first_one = True

        self.last_preamble = self.samplenum

    def decode(self):
        # Set samplerate to 0 if it is not given. Decoding is still possible.
        if not self.samplerate:
            self.samplerate = 0

        # Throw away first two edges as it might be mangled data.
        self.wait({0: 'e'})
        self.wait({0: 'e'})
        self.ss_edge = 0
        self.puty([2, ['Skip']])
        self.ss_edge = self.samplenum
        self.samplenum_prev_edge = self.samplenum

        while True:
            # Wait for any edge (rising or falling).
            (data,) = self.wait({0: 'e'})
            self.pulse_width = self.samplenum - self.samplenum_prev_edge
            self.samplenum_prev_edge = self.samplenum

            if self.state == 'GET FIRST PULSE WIDTH':
                self.find_first_pulse_width()
            elif self.state == 'GET SECOND PULSE WIDTH':
                self.find_second_pulse_width()
            elif self.state == 'GET THIRD PULSE WIDTH':
                self.find_third_pulse_width()
            elif self.state == 'DECODE STREAM':
                self.decode_stream()
            elif self.state == 'DECODE PREAMBLE':
                self.decode_preamble()
