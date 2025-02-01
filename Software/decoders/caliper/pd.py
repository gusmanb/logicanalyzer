##
## This file is part of the libsigrokdecode project.
##
## Copyright (C) 2020 Tomas Mudrunka <harvie@github>
##
## Permission is hereby granted, free of charge, to any person obtaining a copy
## of this software and associated documentation files (the "Software"), to deal
## in the Software without restriction, including without limitation the rights
## to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
## copies of the Software, and to permit persons to whom the Software is
## furnished to do so, subject to the following conditions:
##
## The above copyright notice and this permission notice shall be included in all
## copies or substantial portions of the Software.
##
## THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
## IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
## FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
## AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
## LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
## OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
## SOFTWARE.

import sigrokdecode as srd
from common.srdhelper import bitpack

# Millimeters per inch.
mm_per_inch = 25.4

class Decoder(srd.Decoder):
    api_version = 3
    id = 'caliper'
    name = 'Caliper'
    longname = 'Digital calipers'
    desc = 'Protocol of cheap generic digital calipers.'
    license = 'mit'
    inputs = ['logic']
    outputs = []
    channels = (
        {'id': 'clk', 'name': 'CLK', 'desc': 'Serial clock line'},
        {'id': 'data', 'name': 'DATA', 'desc': 'Serial data line'},
    )
    options = (
        {'id': 'timeout_ms', 'desc': 'Packet timeout in ms, 0 to disable',
            'default': 10},
        {'id': 'unit', 'desc': 'Convert units', 'default': 'keep',
            'values': ('keep', 'mm', 'inch')},
        {'id': 'changes', 'desc': 'Changes only', 'default': 'no',
            'values': ('no', 'yes')},
    )
    tags = ['Analog/digital', 'Sensor']
    annotations = (
        ('measurement', 'Measurement'),
        ('warning', 'Warning'),
    )
    annotation_rows = (
        ('measurements', 'Measurements', (0,)),
        ('warnings', 'Warnings', (1,)),
    )

    def metadata(self, key, value):
       if key == srd.SRD_CONF_SAMPLERATE:
            self.samplerate = value

    def __init__(self):
        self.reset()

    def reset(self):
        self.ss, self.es = 0, 0
        self.number_bits = []
        self.flags_bits = []

    def start(self):
        self.out_ann = self.register(srd.OUTPUT_ANN)

    def putg(self, ss, es, cls, data):
        self.put(ss, es, self.out_ann, [cls, data])

    def decode(self):
        last_sent = None
        timeout_ms = self.options['timeout_ms']
        want_unit = self.options['unit']
        show_all = self.options['changes'] == 'no'
        wait_cond = [{0: 'r'}]
        if timeout_ms:
            snum_per_ms = self.samplerate / 1000
            timeout_snum = timeout_ms * snum_per_ms
            wait_cond.append({'skip': round(timeout_snum)})
        while True:
            # Sample data at the rising clock edge. Optionally timeout
            # after inactivity for a user specified period. Present the
            # number of unprocessed bits to the user for diagnostics.
            clk, data = self.wait(wait_cond)
            if timeout_ms and not self.matched[0]:
                if self.number_bits or self.flags_bits:
                    count = len(self.number_bits) + len(self.flags_bits)
                    self.putg(self.ss, self.samplenum, 1, [
                        'timeout with {} bits in buffer'.format(count),
                        'timeout ({} bits)'.format(count),
                        'timeout',
                    ])
                self.reset()
                continue

            # Store position of first bit and last activity.
            # Shift in measured number and flag bits.
            if not self.ss:
                self.ss = self.samplenum
            self.es = self.samplenum
            if len(self.number_bits) < 16:
                self.number_bits.append(data)
                continue
            if len(self.flags_bits) < 8:
                self.flags_bits.append(data)
                if len(self.flags_bits) < 8:
                    continue

            # Get raw values from received data bits. Run the number
            # conversion, controlled by flags and/or user specs.
            negative = bool(self.flags_bits[4])
            is_inch = bool(self.flags_bits[7])
            number = bitpack(self.number_bits)
            if negative:
                number = -number
            if is_inch:
                number /= 2000
                if want_unit == 'mm':
                    number *= mm_per_inch
                    is_inch = False
            else:
                number /= 100
                if want_unit == 'inch':
                    number = round(number / mm_per_inch, 4)
                    is_inch = True
            unit = 'in' if is_inch else 'mm'

            # Construct and emit an annotation.
            if show_all or (number, unit) != last_sent:
                self.putg(self.ss, self.es, 0, [
                    '{number}{unit}'.format(**locals()),
                    '{number}'.format(**locals()),
                ])
                last_sent = (number, unit)

            # Reset internal state for the start of the next packet.
            self.reset()
