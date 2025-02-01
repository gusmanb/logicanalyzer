##
## This file is part of the libsigrokdecode project.
##
## Copyright (C) 2017 Christoph Rackwitz <christoph.rackwitz@rwth-aachen.de>
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
from collections import deque
from common.srdhelper import bitpack, bitunpack

def gray_encode(plain):
    return plain & (plain >> 1)

def gray_decode(gray):
    temp = gray
    temp ^= (temp >> 8)
    temp ^= (temp >> 4)
    temp ^= (temp >> 2)
    temp ^= (temp >> 1)
    return temp

def prefix_fmt(value, emin=None):
    sgn = (value > 0) - (value < 0)
    value = abs(value)
    p = math.log10(value) if value else 0
    value = sgn * math.floor(value * 10**int(3 - p)) * 10**-int(3 - p)
    e = p // 3 * 3
    if emin is not None and e < emin:
        e = emin
    value *= 10**-e
    p -= e
    decimals = 2 - int(p)
    prefixes = {-9: 'n', -6: 'µ', -3: 'm', 0: '', 3: 'k', 6: 'M', 9: 'G'}
    return '{0:.{1}f} {2}'.format(value, decimals, prefixes[e])

class ChannelMapError(Exception):
    pass

class Value:
    def __init__(self, onchange):
        self.onchange = onchange
        self.timestamp = None
        self.value = None

    def get(self):
        return self.value

    def set(self, timestamp, newval):
        if newval != self.value:
            if self.value is not None:
                self.onchange(self.timestamp, self.value, timestamp, newval)

            self.value = newval
            self.timestamp = timestamp
        elif False:
            if self.value is not None:
                self.onchange(self.timestamp, self.value, timestamp, newval)

MAX_CHANNELS = 8 # 10 channels causes some weird problems...

class Decoder(srd.Decoder):
    api_version = 3
    id = 'graycode'
    name = 'Gray code'
    longname = 'Gray code and rotary encoder'
    desc = 'Accumulate rotary encoder increments, provide statistics.'
    license = 'gplv2+'
    inputs = ['logic']
    outputs = []
    tags = ['Encoding']
    optional_channels = tuple(
        {'id': 'd{}'.format(i), 'name': 'D{}'.format(i), 'desc': 'Data line {}'.format(i)}
        for i in range(MAX_CHANNELS)
    )
    options = (
        {'id': 'edges', 'desc': 'Edges per rotation', 'default': 0},
        {'id': 'avg_period', 'desc': 'Averaging period', 'default': 10},
    )
    annotations = (
        ('phase', 'Phase'),
        ('increment', 'Increment'),
        ('count', 'Count'),
        ('turn', 'Turn'),
        ('interval', 'Interval'),
        ('average', 'Average'),
        ('rpm', 'Rate'),
    )
    annotation_rows = tuple((u + 's', v + 's', (i,)) for i, (u, v) in enumerate(annotations))

    def __init__(self):
        self.reset()

    def reset(self):
        self.num_channels = 0
        self.samplerate = None
        self.last_n = deque()

        self.phase = Value(self.on_phase)
        self.increment = Value(self.on_increment)
        self.count = Value(self.on_count)
        self.turns = Value(self.on_turns)

    def on_phase(self, told, vold, tnew, vnew):
        self.put(told, tnew, self.out_ann, [0, ['{}'.format(vold)]])

    def on_increment(self, told, vold, tnew, vnew):
        if vold == 0:
            message = '0'
        elif abs(vold) == self.ENCODER_STEPS // 2:
            message = '±π'
        else:
            message = '{:+d}'.format(vold)
        self.put(told, tnew, self.out_ann, [1, [message]])

    def on_count(self, told, vold, tnew, vnew):
        self.put(told, tnew, self.out_ann, [2, ['{}'.format(vold)]])

    def on_turns(self, told, vold, tnew, vnew):
        self.put(told, tnew, self.out_ann, [3, ['{:+d}'.format(vold)]])

    def metadata(self, key, value):
        if key == srd.SRD_CONF_SAMPLERATE:
            self.samplerate = value

    def start(self):
        self.out_ann = self.register(srd.OUTPUT_ANN)

    def decode(self):
        chmask = [self.has_channel(i) for i in range(MAX_CHANNELS)]
        self.num_channels = sum(chmask)
        if chmask != [i < self.num_channels for i in range(MAX_CHANNELS)]:
            raise ChannelMapError('Assigned channels need to be contiguous')

        self.ENCODER_STEPS = 1 << self.num_channels

        startbits = self.wait()
        curtime = self.samplenum

        self.turns.set(self.samplenum, 0)
        self.count.set(self.samplenum, 0)
        self.phase.set(self.samplenum, gray_decode(bitpack(startbits[:self.num_channels])))

        while True:
            prevtime = curtime
            bits = self.wait([{i: 'e'} for i in range(self.num_channels)])
            curtime = self.samplenum

            oldcount = self.count.get()
            oldphase = self.phase.get()

            newphase = gray_decode(bitpack(bits[:self.num_channels]))
            self.phase.set(self.samplenum, newphase)

            phasedelta_raw = (newphase - oldphase + (self.ENCODER_STEPS // 2 - 1)) % self.ENCODER_STEPS - (self.ENCODER_STEPS // 2 - 1)
            phasedelta = phasedelta_raw
            self.increment.set(self.samplenum, phasedelta)
            if abs(phasedelta) == self.ENCODER_STEPS // 2:
                phasedelta = 0

            self.count.set(self.samplenum, self.count.get() + phasedelta)

            if self.options['edges']:
                self.turns.set(self.samplenum, self.count.get() // self.options['edges'])

            if self.samplerate:
                period = (curtime - prevtime) / self.samplerate
                freq = abs(phasedelta_raw) / period

                self.put(prevtime, curtime, self.out_ann, [4, [
                    '{}s, {}Hz'.format(prefix_fmt(period), prefix_fmt(freq))]])

                if self.options['avg_period']:
                    self.last_n.append((abs(phasedelta_raw), period))
                    if len(self.last_n) > self.options['avg_period']:
                        self.last_n.popleft()

                    avg_period = sum(v for u, v in self.last_n) / (sum(u for u, v in self.last_n) or 1)
                    self.put(prevtime, curtime, self.out_ann, [5, [
                        '{}s, {}Hz'.format(prefix_fmt(avg_period),
                            prefix_fmt(1 / avg_period))]])

                if self.options['edges']:
                    self.put(prevtime, curtime, self.out_ann, [6, ['{}rpm'.format(prefix_fmt(60 * freq / self.options['edges'], emin=0))]])
