##
## This file is part of the libsigrokdecode project.
##
## Copyright (C) 2016 Anthony Symons <antus@pcmhacking.net>
## Copyright (C) 2023 Gerhard Sittig <gerhard.sittig@gmx.net>
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
from common.srdhelper import bitpack_msb

# VPW Timings. From the SAE J1850 1995 rev section 23.406 documentation.
# Ideal, minimum and maximum tolerances.
VPW_SOF = 200
VPW_SOFL = 164
VPW_SOFH = 245  # 240 by the spec, 245 so a 60us 4x sample will pass
VPW_LONG = 128
VPW_LONGL = 97
VPW_LONGH = 170 # 164 by the spec but 170 for low sample rate tolerance.
VPW_SHORT = 64
VPW_SHORTL = 24 # 35 by the spec, 24 to allow down to 6us as measured in practice for 4x @ 1mhz sampling
VPW_SHORTH = 97
VPW_IFS = 240

class SamplerateError(Exception):
    pass

(
    ANN_SOF, ANN_BIT, ANN_IFS, ANN_BYTE,
    ANN_PRIO, ANN_DEST, ANN_SRC, ANN_MODE, ANN_DATA, ANN_CSUM,
    ANN_M1_PID,
    ANN_WARN,
) = range(12)

class Decoder(srd.Decoder):
    api_version = 3
    id = 'sae_j1850_vpw'
    name = 'SAE J1850 VPW'
    longname = 'SAE J1850 VPW.'
    desc = 'SAE J1850 Variable Pulse Width 1x and 4x.'
    license = 'gplv2+'
    inputs = ['logic']
    outputs = []
    tags = ['Automotive']
    channels = (
        {'id': 'data', 'name': 'Data', 'desc': 'Data line'},
    )
    annotations = (
        ('sof', 'SOF'),
        ('bit', 'Bit'),
        ('ifs', 'EOF/IFS'),
        ('byte', 'Byte'),
        ('prio', 'Priority'),
        ('dest', 'Destination'),
        ('src', 'Source'),
        ('mode', 'Mode'),
        ('data', 'Data'),
        ('csum', 'Checksum'),
        ('m1_pid', 'Pid'),
        ('warn', 'Warning'),
    )
    annotation_rows = (
        ('bits', 'Bits', (ANN_SOF, ANN_BIT, ANN_IFS,)),
        ('bytes', 'Bytes', (ANN_BYTE,)),
        ('fields', 'Fields', (ANN_PRIO, ANN_DEST, ANN_SRC, ANN_MODE, ANN_DATA, ANN_CSUM,)),
        ('values', 'Values', (ANN_M1_PID,)),
        ('warns', 'Warnings', (ANN_WARN,)),
    )
    # TODO Add support for options? Polarity. Glitch length.

    def __init__(self):
        self.reset()

    def reset(self):
        self.samplerate = None
        self.active = 0 # Signal polarity. Needs to become an option?
        self.bits = []
        self.fields = {}

    def start(self):
        self.out_ann = self.register(srd.OUTPUT_ANN)

    def metadata(self, key, value):
        if key == srd.SRD_CONF_SAMPLERATE:
            self.samplerate = value

    def putg(self, ss, es, cls, texts):
        self.put(ss, es, self.out_ann, [cls, texts])

    def invalidate_frame_details(self):
        self.bits.clear()
        self.fields.clear()

    def handle_databytes(self, fields, data):
        # TODO Deep inspection of header fields and data values, including
        # checksum verification results.
        mode = fields.get('mode', None)
        if mode is None:
            return
        if mode == 1:
            # An earlier implementation commented that for mode 1 the
            # first data byte would be the PID. But example captures
            # have no data bytes in packets for that mode. This position
            # is taken by the checksum. Is this correct?
            pid = data[0] if data else fields.get('csum', None)
            if pid is None:
                text = ['PID missing']
                self.putg(ss, es, ANN_WARN, text)
            else:
                byte_text = '{:02x}'.format(pid)
                self.putg(ss, es, ANN_M1_PID, [byte_text])

    def handle_byte(self, ss, es, b):
        # Annotate all raw byte values. Inspect and process the first
        # bytes in a frame already. Cease inspection and only accumulate
        # all other bytes after the mode. The checksum's position and
        # thus the data bytes' span will only be known when EOF or IFS
        # were seen. Implementor's note: This method just identifies
        # header fields. Processing is left to the .handle_databytes()
        # method. Until then validity will have been checked, too (CS).
        byte_text = '{:02x}'.format(b)
        self.putg(ss, es, ANN_BYTE, [byte_text])

        if not 'prio' in self.fields:
            self.fields.update({'prio': b})
            self.putg(ss, es, ANN_PRIO, [byte_text])
            return
        if not 'dest' in self.fields:
            self.fields.update({'dest': b})
            self.putg(ss, es, ANN_DEST, [byte_text])
            return
        if not 'src' in self.fields:
            self.fields.update({'src': b})
            self.putg(ss, es, ANN_SRC, [byte_text])
            return
        if not 'mode' in self.fields:
            self.fields.update({'mode': b})
            self.putg(ss, es, ANN_MODE, [byte_text])
            return
        if not 'data' in self.fields:
            self.fields.update({'data': [], 'csum': None})
        self.fields['data'].append((b, ss, es))

    def handle_sof(self, ss, es, speed):
        text = ['{speed:d}x SOF', 'S{speed:d}', 'S']
        text = [f.format(speed = speed) for f in text]
        self.putg(ss, es, ANN_SOF, text)
        self.invalidate_frame_details()
        self.fields.update({'speed': speed})

    def handle_bit(self, ss, es, b):
        self.bits.append((b, ss, es))
        self.putg(ss, es, ANN_BIT, ['{:d}'.format(b)])
        if len(self.bits) < 8:
            return
        ss, es = self.bits[0][1], self.bits[-1][2]
        b = bitpack_msb(self.bits, 0)
        self.bits.clear()
        self.handle_byte(ss, es, b)

    def handle_eof(self, ss, es, is_ifs = False):
        # EOF or IFS were seen. Post process the data bytes sequence.
        # Separate the checksum from the data bytes. Emit annotations.
        # Pass data bytes and header fields to deeper inspection.
        data = self.fields.get('data', {})
        if not data:
            text = ['Short data phase', 'Data']
            self.putg(ss, es, ANN_WARN, text)
        csum = None
        if len(data) >= 1:
            csum, ss_csum, es_csum = data.pop()
            self.fields.update({'csum': csum})
            # TODO Verify checksum's correctness?
        if data:
            ss_data, es_data = data[0][1], data[-1][2]
            text = ' '.join(['{:02x}'.format(b[0]) for b in data])
            self.putg(ss_data, es_data, ANN_DATA, [text])
        if csum is not None:
            text = '{:02x}'.format(csum)
            self.putg(ss_csum, es_csum, ANN_CSUM, [text])
        text = ['IFS', 'I'] if is_ifs else ['EOF', 'E']
        self.putg(ss, es, ANN_IFS, text)
        self.handle_databytes(self.fields, data);
        self.invalidate_frame_details()

    def handle_unknown(self, ss, es):
        text = ['Unknown condition', 'Unknown', 'UNK']
        self.putg(ss, es, ANN_WARN, text)
        self.invalidate_frame_details()

    def usecs_to_samples(self, us):
        us *= 1e-6
        us *= self.samplerate
        return int(us)

    def samples_to_usecs(self, n):
        n /= self.samplerate
        n *= 1000.0 * 1000.0
        return int(n)

    def decode(self):
        if not self.samplerate:
            raise SamplerateError('Cannot decode without samplerate.')

        # Get the distance between edges. Classify the distance
        # to derive symbols and data bit values. Prepare waiting
        # for an interframe gap as well, while this part of the
        # condition is optional (switches in and out at runtime).
        conds_edge = {0: 'e'}
        conds_edge_only = [conds_edge]
        conds_edge_idle = [conds_edge, {'skip': 0}]
        conds = conds_edge_only
        self.wait(conds)
        es = self.samplenum
        spd = None
        while True:
            ss = es
            pin, = self.wait(conds)
            es = self.samplenum
            count = es - ss
            t = self.samples_to_usecs(count)

            # Synchronization to the next frame. Wait for SOF.
            # Silently keep synchronizing until SOF was seen.
            if spd is None:
                if not self.matched[0]:
                    continue
                if pin != self.active:
                    continue

                # Detect the frame's speed from the SOF length. Adjust
                # the expected BIT lengths to the SOF derived speed.
                # Arrange for the additional supervision of EOF/IFS.
                if t in range(VPW_SOFL // 1, VPW_SOFH // 1):
                    spd = 1
                elif t in range(VPW_SOFL // 4, VPW_SOFH // 4):
                    spd = 4
                else:
                    continue
                short_lower, short_upper = VPW_SHORTL // spd, VPW_SHORTH // spd
                long_lower, long_upper = VPW_LONGL // spd, VPW_LONGH // spd
                samples = self.usecs_to_samples(VPW_IFS // spd)
                conds_edge_idle[-1]['skip'] = samples
                conds = conds_edge_idle

                # Emit the SOF annotation. Start collecting DATA.
                self.handle_sof(ss, es, spd)
                continue

            # Inside the DATA phase. Get data bits. Handle EOF/IFS.
            if len(conds) > 1 and self.matched[1]:
                # TODO The current implementation gets here after a
                # pre-determined minimum wait time. Does not differ
                # between EOF and IFS. An earlier implementation had
                # this developer note: EOF=239-280 IFS=281+
                self.handle_eof(ss, es)
                # Enter the IDLE phase. Wait for the next SOF.
                spd = None
                conds = conds_edge_only
                continue
            if t in range(short_lower, short_upper):
                value = 1 if pin == self.active else 0
                self.handle_bit(ss, es, value)
                continue
            if t in range(long_lower, long_upper):
                value = 0 if pin == self.active else 1
                self.handle_bit(ss, es, value)
                continue

            # Implementation detail: An earlier implementation used to
            # ignore everything that was not handled above. This would
            # be motivated by the noisy environment the protocol is
            # typically used in. This more recent implementation accepts
            # short glitches, but by design falls back to synchronization
            # to the input stream for other unhandled conditions. This
            # wants to improve usability of the decoder, by presenting
            # potential issues to the user. The threshold (microseconds
            # between edges that are not valid symbols that are handled
            # above) is an arbitrary choice.
            if t <= 2:
                continue
            self.handle_unknown(ss, es)
            spd = None
            conds = conds_edge_only
