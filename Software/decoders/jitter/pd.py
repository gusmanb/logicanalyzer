##
## This file is part of the libsigrokdecode project.
##
## Copyright (C) 2014 Sebastien Bourdelin <sebastien.bourdelin@savoirfairelinux.com>
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

# Helper dictionary for edge detection.
edge_detector = {
    'rising':  lambda x, y: bool(not x and y),
    'falling': lambda x, y: bool(x and not y),
    'both':    lambda x, y: bool(x ^ y),
}

class SamplerateError(Exception):
    pass

class Decoder(srd.Decoder):
    api_version = 3
    id = 'jitter'
    name = 'Jitter'
    longname = 'Timing jitter calculation'
    desc = 'Retrieves the timing jitter between two digital signals.'
    license = 'gplv2+'
    inputs = ['logic']
    outputs = []
    tags = ['Clock/timing', 'Util']
    channels = (
        {'id': 'clk', 'name': 'Clock', 'desc': 'Clock reference channel'},
        {'id': 'sig', 'name': 'Resulting signal', 'desc': 'Resulting signal controlled by the clock'},
    )
    options = (
        {'id': 'clk_polarity', 'desc': 'Clock edge polarity',
            'default': 'rising', 'values': ('rising', 'falling', 'both')},
        {'id': 'sig_polarity', 'desc': 'Resulting signal edge polarity',
            'default': 'rising', 'values': ('rising', 'falling', 'both')},
    )
    annotations = (
        ('jitter', 'Jitter value'),
        ('clk_miss', 'Clock miss'),
        ('sig_miss', 'Signal miss'),
    )
    annotation_rows = (
        ('jitter_vals', 'Jitter values', (0,)),
        ('clk_misses', 'Clock misses', (1,)),
        ('sig_misses', 'Signal misses', (2,)),
    )
    binary = (
        ('ascii-float', 'Jitter values as newline-separated ASCII floats'),
    )

    def __init__(self):
        self.reset()

    def reset(self):
        self.state = 'CLK'
        self.samplerate = None
        self.oldclk, self.oldsig = 0, 0
        self.clk_start = None
        self.sig_start = None
        self.clk_missed = 0
        self.sig_missed = 0

    def start(self):
        self.clk_edge = edge_detector[self.options['clk_polarity']]
        self.sig_edge = edge_detector[self.options['sig_polarity']]
        self.out_ann = self.register(srd.OUTPUT_ANN)
        self.out_binary = self.register(srd.OUTPUT_BINARY)
        self.out_clk_missed = self.register(srd.OUTPUT_META,
            meta=(int, 'Clock missed', 'Clock transition missed'))
        self.out_sig_missed = self.register(srd.OUTPUT_META,
            meta=(int, 'Signal missed', 'Resulting signal transition missed'))

    def metadata(self, key, value):
        if key == srd.SRD_CONF_SAMPLERATE:
            self.samplerate = value

    # Helper function for jitter time annotations.
    def putx(self, delta):
        # Adjust granularity.
        if delta == 0 or delta >= 1:
            delta_s = '%.1fs' % (delta)
        elif delta <= 1e-12:
            delta_s = '%.1ffs' % (delta * 1e15)
        elif delta <= 1e-9:
            delta_s = '%.1fps' % (delta * 1e12)
        elif delta <= 1e-6:
            delta_s = '%.1fns' % (delta * 1e9)
        elif delta <= 1e-3:
            delta_s = '%.1fμs' % (delta * 1e6)
        else:
            delta_s = '%.1fms' % (delta * 1e3)

        self.put(self.clk_start, self.sig_start, self.out_ann, [0, [delta_s]])

    # Helper function for ASCII float jitter values (one value per line).
    def putb(self, delta):
        if delta is None:
            return
        # Format the delta to an ASCII float value terminated by a newline.
        x = str(delta) + '\n'
        self.put(self.clk_start, self.sig_start, self.out_binary,
                 [0, x.encode('UTF-8')])

    # Helper function for missed clock and signal annotations.
    def putm(self, data):
        self.put(self.samplenum, self.samplenum, self.out_ann, data)

    def handle_clk(self, clk, sig):
        if self.clk_start == self.samplenum:
            # Clock transition already treated.
            # We have done everything we can with this sample.
            return True

        if self.clk_edge(self.oldclk, clk):
            # Clock edge found.
            # We note the sample and move to the next state.
            self.clk_start = self.samplenum
            self.state = 'SIG'
            return False
        else:
            if self.sig_start is not None \
               and self.sig_start != self.samplenum \
               and self.sig_edge(self.oldsig, sig):
                # If any transition in the resulting signal
                # occurs while we are waiting for a clock,
                # we increase the missed signal counter.
                self.sig_missed += 1
                self.put(self.samplenum, self.samplenum, self.out_sig_missed, self.sig_missed)
                self.putm([2, ['Missed signal', 'MS']])
            # No clock edge found, we have done everything we
            # can with this sample.
            return True

    def handle_sig(self, clk, sig):
        if self.sig_start == self.samplenum:
            # Signal transition already treated.
            # We have done everything we can with this sample.
            return True

        if self.sig_edge(self.oldsig, sig):
            # Signal edge found.
            # We note the sample, calculate the jitter
            # and move to the next state.
            self.sig_start = self.samplenum
            self.state = 'CLK'
            # Calculate and report the timing jitter.
            delta = (self.sig_start - self.clk_start) / self.samplerate
            self.putx(delta)
            self.putb(delta)
            return False
        else:
            if self.clk_start != self.samplenum \
               and self.clk_edge(self.oldclk, clk):
                # If any transition in the clock signal
                # occurs while we are waiting for a resulting
                # signal, we increase the missed clock counter.
                self.clk_missed += 1
                self.put(self.samplenum, self.samplenum, self.out_clk_missed, self.clk_missed)
                self.putm([1, ['Missed clock', 'MC']])
            # No resulting signal edge found, we have done
            # everything we can with this sample.
            return True

    def decode(self):
        if not self.samplerate:
            raise SamplerateError('Cannot decode without samplerate.')
        while True:
            # Wait for a transition on CLK and/or SIG.
            clk, sig = self.wait([{0: 'e'}, {1: 'e'}])

            # State machine:
            # For each sample we can move 2 steps forward in the state machine.
            while True:
                # Clock state has the lead.
                if self.state == 'CLK':
                    if self.handle_clk(clk, sig):
                        break
                if self.state == 'SIG':
                    if self.handle_sig(clk, sig):
                        break

            # Save current CLK/SIG values for the next round.
            self.oldclk, self.oldsig = clk, sig
