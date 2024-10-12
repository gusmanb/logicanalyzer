##
## This file is part of the libsigrokdecode project.
##
## Copyright (C) 2018 Steve R <steversig@virginmedia.com>
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
Samples:    The Samples array is sent when a DECODE_TIMEOUT occurs.
[<start>, <finish>, <state>]
<start> is the sample number of the start of the decoded bit. This may not line
up with the pulses that were converted into the decoded bit particularly for
Manchester encoding.
<finish> is the sample number of the end of the decoded bit.
<state> is a single character string which is the state of the decoded bit.
This can be
'0'   zero or low
'1'   one or high
'E'   Error or invalid. This can be caused by missing transitions or the wrong
pulse lengths according to the rules for the particular encoding. In some cases
this is intentional (Oregon 1 preamble) and is part of the sync pattern. In
other cases the signal could simply be broken.

If there are more than self.max_errors (default 5) in decoding then the
OUTPUT_PYTHON is not sent as the data is assumed to be worthless.
There also needs to be a low for five times the preamble period at the end of
each set of pulses to trigger a DECODE_TIMEOUT and get the OUTPUT_PYTHON sent.
'''

class SamplerateError(Exception):
    pass

class Decoder(srd.Decoder):
    api_version = 3
    id = 'ook'
    name = 'OOK'
    longname = 'On-off keying'
    desc = 'On-off keying protocol.'
    license = 'gplv2+'
    inputs = ['logic']
    outputs = ['ook']
    tags = ['Encoding']
    channels = (
        {'id': 'data', 'name': 'Data', 'desc': 'Data line'},
    )
    annotations = (
        ('frame', 'Frame'),
        ('info', 'Info'),
        ('1111', '1111'),
        ('1010', '1010'),
        ('diffman', 'Diff man'),
        ('nrz', 'NRZ'),
    )
    annotation_rows = (
        ('frames', 'Framing', (0,)),
        ('info-vals', 'Info', (1,)),
        ('man1111', 'Man 1111', (2,)),
        ('man1010', 'Man 1010', (3,)),
        ('diffmans', 'Diff man', (4,)),
        ('nrz-vals', 'NRZ', (5,)),
    )
    binary = (
        ('pulse-lengths', 'Pulse lengths'),
    )
    options = (
        {'id': 'invert', 'desc': 'Invert data', 'default': 'no',
         'values': ('no', 'yes')},
        {'id': 'decodeas', 'desc': 'Decode type', 'default': 'Manchester',
         'values': ('NRZ', 'Manchester', 'Diff Manchester')},
        {'id': 'preamble', 'desc': 'Preamble', 'default': 'auto',
         'values': ('auto', '1010', '1111')},
        {'id': 'preamlen', 'desc': 'Filter length', 'default': '7',
         'values': ('0', '3', '4', '5', '6', '7', '8', '9', '10')},
        {'id': 'diffmanvar', 'desc': 'Transition at start', 'default': '1',
         'values': ('1', '0')},
    )

    def __init__(self):
        self.reset()

    def reset(self):
        self.samplerate = None
        self.ss = self.es = -1
        self.ss_1111 = self.ss_1010 = -1
        self.samplenumber_last = None
        self.sample_first = None
        self.sample_high = 0
        self.sample_low = 0
        self.edge_count = 0
        self.word_first = None
        self.word_count = 0
        self.state = 'IDLE'
        self.lstate = None
        self.lstate_1010 = None
        self.insync = 0                 # Preamble in sync flag
        self.man_errors = 0
        self.man_errors_1010 = 0
        self.preamble = []              # Preamble buffer
        self.half_time = -1             # Half time for man 1111
        self.half_time_1010 = 0         # Half time for man 1010
        self.pulse_lengths = []         # Pulse lengths
        self.decoded = []               # Decoded stream
        self.decoded_1010 = []          # Decoded stream
        self.diff_man_trans = '0'       # Transition
        self.diff_man_len = 1           # Length of pulse in half clock periods
        self.max_errors = 5             # Max number of errors to output OOK

    def metadata(self, key, value):
        if key == srd.SRD_CONF_SAMPLERATE:
            self.samplerate = value

    def start(self):
        self.out_ann = self.register(srd.OUTPUT_ANN)
        self.out_python = self.register(srd.OUTPUT_PYTHON)
        self.out_binary = self.register(srd.OUTPUT_BINARY)
        self.invert = self.options['invert']
        self.decodeas = self.options['decodeas']
        self.preamble_val = self.options['preamble']
        self.preamble_len = self.options['preamlen']
        self.diffmanvar = self.options['diffmanvar']

    def putx(self, data):
        self.put(self.ss, self.es, self.out_ann, data)

    def putp(self, data):
        self.put(self.ss, self.es, self.out_python, data)

    def dump_pulse_lengths(self):
        if self.samplerate:
            self.pulse_lengths[-1] = self.sample_first # Fix final pulse length.
            s = 'Pulses(us)='
            s += ','.join(str(int(int(x) * 1000000 / self.samplerate))
                          for x in self.pulse_lengths)
            s += '\n'
            self.put(self.samplenum - 10, self.samplenum, self.out_binary,
                     [0, bytes([ord(c) for c in s])])

    def decode_nrz(self, start, samples, state):
        self.pulse_lengths.append(samples)
        # Use different high and low widths to compensate skewed waveforms.
        dsamples = self.sample_high if state == '1' else self.sample_low
        self.ss, self.es = start, start + samples
        while samples > dsamples * 0.5:
            if samples >= dsamples * 1.5: # More than one bit.
                self.es = self.ss + dsamples
                self.putx([5, [state]])
                self.decoded.append([self.ss, self.es, state])
                self.edge_count += 1
            elif samples >= dsamples * 0.5 and samples < dsamples * 1.5: # Last bit.
                self.putx([5, [state]])
                self.decoded.append([self.ss, self.es, state])
                self.edge_count += 1
            else:
                self.edge_count += 1
            samples -= dsamples
            self.ss += dsamples
            self.es += dsamples

            # Ensure 2nd row doesn't go past end of 1st row.
            if self.es > self.samplenum:
                self.es = self.samplenum

            if self.state == 'DECODE_TIMEOUT': # Five bits - reset.
                self.ss = self.decoded[0][0]
                self.es = self.decoded[len(self.decoded) - 1][1]
                self.dump_pulse_lengths()
                self.putp(self.decoded)
                self.decode_timeout()
                break

    def lock_onto_preamble(self, samples, state): # Filters and recovers clock.
        self.edge_count += 1
        l2s = 5 # Max ratio of long to short pulses.

        # Filter incoming pulses to remove random noise.
        if self.state == 'DECODE_TIMEOUT':
            self.preamble = []
            self.edge_count = 0
            self.word_first = self.samplenum
            self.sample_first = self.samplenum - self.samplenumber_last
            self.state = 'WAITING_FOR_PREAMBLE'
            self.man_errors = 0

        pre_detect = int(self.preamble_len) # Number of valid pulses to detect.
        pre_samples = self.samplenum - self.samplenumber_last
        if len(self.preamble) > 0:
            if (pre_samples * l2s < self.preamble[-1][1] or
                self.preamble[-1][1] * l2s < pre_samples): # Garbage in.
                self.put(self.samplenum, self.samplenum,
                         self.out_ann, [0, ['R']]) # Display resets.
                self.preamble = [] # Clear buffer.
                self.preamble.append([self.samplenumber_last,
                                     pre_samples, state])
                self.edge_count = 0
                self.samplenumber_last = self.samplenum
                self.word_first = self.samplenum
            else:
                self.preamble.append([self.samplenumber_last,
                                     pre_samples, state])
        else:
            self.preamble.append([self.samplenumber_last,
                                 pre_samples, state])

        pre = self.preamble
        if len(self.preamble) == pre_detect: # Have a valid series of pulses.
            if self.preamble[0][2] == '1':
                self.sample_high = self.preamble[0][1] # Allows skewed pulses.
                self.sample_low = self.preamble[1][1]
            else:
                self.sample_high = self.preamble[1][1]
                self.sample_low = self.preamble[0][1]

            self.edge_count = 0

            for i in range(len(self.preamble)):
                if i > 1:
                    if (pre[i][1] > pre[i - 2][1] * 1.25 or
                        pre[i][1] * 1.25 < pre[i - 2][1]): # Adjust ref width.
                        if pre[i][2] == '1':
                            self.sample_high = pre[i][1]
                        else:
                            self.sample_low = pre[i][1]

                # Display start of preamble.
                if self.decodeas == 'NRZ':
                    self.decode_nrz(pre[i][0], pre[i][1], pre[i][2])
                if self.decodeas == 'Manchester':
                    self.decode_manchester(pre[i][0], pre[i][1], pre[i][2])
                if self.decodeas == 'Diff Manchester':
                    self.es = pre[i][0] + pre[i][1]
                    self.decode_diff_manchester(pre[i][0], pre[i][1], pre[i][2])

                # Used to timeout signal.
                self.sample_first = int((self.sample_high + self.sample_low)/2)
            self.insync = 1
            self.state = 'DECODING'
        self.lstate = state
        self.lstate_1010 = state

    def decode_diff_manchester(self, start, samples, state):
        self.pulse_lengths.append(samples)

        # Use different high and low widths to compensate skewed waveforms.
        dsamples = self.sample_high if state == '1' else self.sample_low

        self.es = start + samples
        p_length = round(samples / dsamples) # Find relative pulse length.

        if self.edge_count == 0:
            self.diff_man_trans = '1'  # Very first pulse must be a transition.
            self.diff_man_len = 1      # Must also be a half pulse.
            self.ss = start
        elif self.edge_count % 2 == 1: # Time to make a decision.
            if self.diffmanvar == '0': # Transition at self.ss is a zero.
                self.diff_man_trans = '0' if self.diff_man_trans == '1' else '1'
            if self.diff_man_len == 1 and p_length == 1:
                self.putx([4, [self.diff_man_trans]])
                self.decoded.append([self.ss, self.es, self.diff_man_trans])
                self.diff_man_trans = '1'
            elif self.diff_man_len == 1 and p_length == 2:
                self.es -= int(samples / 2)
                self.putx([4, [self.diff_man_trans]])
                self.decoded.append([self.ss, self.es, self.diff_man_trans])
                self.diff_man_trans = '0'
                self.edge_count += 1 # Add a virt edge to keep in sync with clk.
            elif self.diff_man_len == 2 and p_length == 1:
                self.putx([4, [self.diff_man_trans]])
                self.decoded.append([self.ss, self.es, self.diff_man_trans])
                self.diff_man_trans = '1'
            elif self.diff_man_len == 2 and p_length == 2: # Double illegal E E.
                self.es -= samples
                self.putx([4, ['E']])
                self.decoded.append([self.ss, self.es, 'E'])
                self.ss = self.es
                self.es += samples
                self.putx([4, ['E']])
                self.decoded.append([self.ss, self.es, 'E'])
                self.diff_man_trans = '1'
            elif self.diff_man_len == 1 and p_length > 4:
                if self.state == 'DECODE_TIMEOUT':
                    self.es = self.ss + 2 * self.sample_first
                    self.putx([4, [self.diff_man_trans]]) # Write error.
                    self.decoded.append([self.ss, self.es, self.diff_man_trans])
                    self.ss = self.decoded[0][0]
                    self.es = self.decoded[len(self.decoded) - 1][1]
                    self.dump_pulse_lengths()
                    if self.man_errors < self.max_errors:
                        self.putp(self.decoded)
                    else:
                        error_message = 'Probably not Diff Manchester encoded'
                        self.ss = self.word_first
                        self.putx([1, [error_message]])
                    self.decode_timeout()
                self.diff_man_trans = '1'
            self.ss = self.es
        self.diff_man_len = p_length # Save the previous length.
        self.edge_count += 1

    def decode_manchester_sim(self, start, samples, state,
                              dsamples, half_time, lstate, ss, pream):
        ook_bit = []
        errors = 0
        if self.edge_count == 0:
            half_time += 1
        if samples > 0.75 * dsamples and samples <= 1.5 * dsamples: # Long p.
            half_time += 2
            if half_time % 2 == 0: # Transition.
                es = start
            else:
                es = start + int(samples / 2)
            if ss == start:
                lstate = 'E'
                es = start + samples
            if not (self.edge_count == 0 and pream == '1010'): # Skip first p.
                ook_bit = [ss, es, lstate]
            lstate = state
            ss = es
        elif samples > 0.25 * dsamples and samples <= 0.75 * dsamples: # Short p.
            half_time += 1
            if (half_time % 2 == 0): # Transition.
                es = start + samples
                ook_bit = [ss, es, lstate]
                lstate = state
                ss = es
            else: # 1st half.
                ss = start
                lstate = state
        else: # Too long or too short - error.
            errors = 1
            if self.state != 'DECODE_TIMEOUT': # Error condition.
                lstate = 'E'
                es = ss + samples
            else: # Assume final half bit buried in timeout pulse.
                es = ss + self.sample_first
            ook_bit = [ss, es, lstate]
            ss = es

        return (half_time, lstate, ss, ook_bit, errors)

    def decode_manchester(self, start, samples, state):
        self.pulse_lengths.append(samples)

        # Use different high and low widths to compensate skewed waveforms.
        dsamples = self.sample_high if state == '1' else self.sample_low

        if self.preamble_val != '1010': # 1111 preamble is half clock T.
            (self.half_time, self.lstate, self.ss_1111, ook_bit, errors) = (
             self.decode_manchester_sim(start, samples, state, dsamples * 2,
                                    self.half_time, self.lstate,
                                    self.ss_1111, '1111'))
            self.man_errors += errors
            if ook_bit != []:
                self.decoded.append([ook_bit[0], ook_bit[1], ook_bit[2]])

        if self.preamble_val != '1111': # 1010 preamble is clock T.
            (self.half_time_1010, self.lstate_1010, self.ss_1010,
             ook_bit, errors) = (
              self.decode_manchester_sim(start, samples, state, dsamples,
                                    self.half_time_1010, self.lstate_1010,
                                    self.ss_1010, '1010'))
            self.man_errors_1010 += errors
            if ook_bit != []:
                self.decoded_1010.append([ook_bit[0], ook_bit[1], ook_bit[2]])

        self.edge_count += 1

        # Stream display and save ook_bit.
        if ook_bit != []:
            self.ss, self.es = ook_bit[0], ook_bit[1]
            if self.preamble_val == '1111':
                self.putx([2, [ook_bit[2]]])
            if self.preamble_val == '1010':
                self.putx([3, [ook_bit[2]]])

        if self.state == 'DECODE_TIMEOUT': # End of packet.
            self.dump_pulse_lengths()

            decoded = []
            # If 1010 preamble has less errors use it.
            if (self.preamble_val == '1010' or
                (self.man_errors_1010 < self.max_errors and
                self.man_errors_1010 < self.man_errors and
                len(self.decoded_1010) > 0)):
                decoded = self.decoded_1010
                man_errors = self.man_errors_1010
                d_row = 3
            else:
                decoded = self.decoded
                man_errors = self.man_errors
                d_row = 2

            if self.preamble_val == 'auto': # Display OOK packet.
                for i in range(len(decoded)):
                    self.ss, self.es = decoded[i][0], decoded[i][1]
                    self.putx([d_row, [decoded[i][2]]])

            if (man_errors < self.max_errors and len(decoded) > 0):
                self.ss, self.es = decoded[0][0], decoded[len(decoded) - 1][1]
                self.putp(decoded)
            else:
                error_message = 'Not Manchester encoded or wrong preamble'
                self.ss = self.word_first
                self.putx([1, [error_message]])

            self.put(self.es, self.es, self.out_ann, [0, ['T']]) # Mark timeout.
            self.decode_timeout()

    def decode_timeout(self):
        self.word_count = 0
        self.samplenumber_last = None
        self.edge_count = 0
        self.man_errors = 0                     # Clear the bit error counters.
        self.man_errors_1010 = 0
        self.state = 'IDLE'
        self.wait({0: 'e'})                     # Get rid of long pulse.
        self.samplenumber_last = self.samplenum
        self.word_first = self.samplenum
        self.insync = 0                         # Preamble in sync flag
        self.preamble = []                      # Preamble buffer
        self.half_time = -1                     # Half time for man 1111
        self.half_time_1010 = 0                 # Half time for man 1010
        self.decoded = []                       # Decoded bits
        self.decoded_1010 = []                  # Decoded bits for man 1010
        self.pulse_lengths = []

    def decode(self):
        while True:
            if self.edge_count == 0: # Waiting for a signal.
                pin = self.wait({0: 'e'})
                self.state = 'DECODING'
            else:
                pin = self.wait([{0: 'e'}, {'skip': 5 * self.sample_first}])
                if self.matched[1] and not self.matched[0]: # No edges for 5 p's.
                    self.state = 'DECODE_TIMEOUT'

            if not self.samplenumber_last: # Set counters to start of signal.
                self.samplenumber_last = self.samplenum
                self.word_first = self.samplenum
                continue
            samples = self.samplenum - self.samplenumber_last
            if not self.sample_first: # Get number of samples for first pulse.
                self.sample_first = samples

            pinstate = pin[0]
            if self.state == 'DECODE_TIMEOUT': # No edge so flip the state.
                pinstate = int(not pinstate)
            if self.invert == 'yes': # Invert signal.
                pinstate = int(not pinstate)
            state = '0' if pinstate else '1'

            # No preamble filtering or checking and no skew correction.
            if self.preamble_len == '0':
                self.sample_high = self.sample_first
                self.sample_low = self.sample_first
                self.insync = 0

            if self.insync == 0:
                self.lock_onto_preamble(samples, state)
            else:
                if self.decodeas == 'NRZ':
                    self.decode_nrz(self.samplenumber_last, samples, state)
                if self.decodeas == 'Manchester':
                    self.decode_manchester(self.samplenumber_last,
                                           samples, state)
                if self.decodeas == 'Diff Manchester':
                    self.decode_diff_manchester(self.samplenumber_last,
                                                samples, state)

            self.samplenumber_last = self.samplenum
