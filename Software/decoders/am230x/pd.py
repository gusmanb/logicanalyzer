##
## This file is part of the libsigrokdecode project.
##
## Copyright (C) 2014 Johannes Roemer <jroemer@physik.uni-wuerzburg.de>
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

# Define valid timing values (in microseconds).
timing = {
    'START LOW'     : {'min': 750, 'max': 25000},
    'START HIGH'    : {'min': 10, 'max': 10000},
    'RESPONSE LOW'  : {'min': 50, 'max': 90},
    'RESPONSE HIGH' : {'min': 50, 'max': 90},
    'BIT LOW'       : {'min': 45, 'max': 90},
    'BIT 0 HIGH'    : {'min': 20, 'max': 35},
    'BIT 1 HIGH'    : {'min': 65, 'max': 80},
}

class SamplerateError(Exception):
    pass

class Decoder(srd.Decoder):
    api_version = 3
    id = 'am230x'
    name = 'AM230x'
    longname = 'Aosong AM230x/DHTxx/RHTxx'
    desc = 'Aosong AM230x/DHTxx/RHTxx humidity/temperature sensor.'
    license = 'gplv2+'
    inputs = ['logic']
    outputs = []
    tags = ['IC', 'Sensor']
    channels = (
        {'id': 'sda', 'name': 'SDA', 'desc': 'Single wire serial data line'},
    )
    options = (
        {'id': 'device', 'desc': 'Device type',
            'default': 'am230x', 'values': ('am230x/rht', 'dht11')},
    )
    annotations = (
        ('start', 'Start'),
        ('response', 'Response'),
        ('bit', 'Bit'),
        ('end', 'End'),
        ('byte', 'Byte'),
        ('humidity', 'Relative humidity'),
        ('temperature', 'Temperature'),
        ('checksum', 'Checksum'),
    )
    annotation_rows = (
        ('bits', 'Bits', (0, 1, 2, 3)),
        ('bytes', 'Bytes', (4,)),
        ('results', 'Results', (5, 6, 7)),
    )

    def putfs(self, data):
        self.put(self.fall, self.samplenum, self.out_ann, data)

    def putb(self, data):
        self.put(self.bytepos[-1], self.samplenum, self.out_ann, data)

    def putv(self, data):
        self.put(self.bytepos[-2], self.samplenum, self.out_ann, data)

    def reset_variables(self):
        self.state = 'WAIT FOR START LOW'
        self.fall = 0
        self.rise = 0
        self.bits = []
        self.bytepos = []

    def is_valid(self, name):
        dt = 0
        if name.endswith('LOW'):
            dt = self.samplenum - self.fall
        elif name.endswith('HIGH'):
            dt = self.samplenum - self.rise
        if dt >= self.cnt[name]['min'] and dt <= self.cnt[name]['max']:
            return True
        return False

    def bits2num(self, bitlist):
        number = 0
        for i in range(len(bitlist)):
            number += bitlist[-1 - i] * 2**i
        return number

    def calculate_humidity(self, bitlist):
        h = 0
        if self.options['device'] == 'dht11':
            h = self.bits2num(bitlist[0:8])
        else:
            h = self.bits2num(bitlist) / 10
        return h

    def calculate_temperature(self, bitlist):
        t = 0
        if self.options['device'] == 'dht11':
            t = self.bits2num(bitlist[0:8])
        else:
            t = self.bits2num(bitlist[1:]) / 10
            if bitlist[0] == 1:
                t = -t
        return t

    def calculate_checksum(self, bitlist):
        checksum = 0
        for i in range(8, len(bitlist) + 1, 8):
            checksum += self.bits2num(bitlist[i-8:i])
        return checksum % 256

    def __init__(self):
        self.reset()

    def reset(self):
        self.samplerate = None
        self.reset_variables()

    def start(self):
        self.out_ann = self.register(srd.OUTPUT_ANN)

    def metadata(self, key, value):
        if key != srd.SRD_CONF_SAMPLERATE:
            return
        self.samplerate = value
        # Convert microseconds to sample counts.
        self.cnt = {}
        for e in timing:
            self.cnt[e] = {}
            for t in timing[e]:
                self.cnt[e][t] = timing[e][t] * self.samplerate / 1000000

    def handle_byte(self, bit):
        self.bits.append(bit)
        self.putfs([2, ['Bit: %d' % bit, '%d' % bit]])
        self.fall = self.samplenum
        self.state = 'WAIT FOR BIT HIGH'
        if len(self.bits) % 8 == 0:
            byte = self.bits2num(self.bits[-8:])
            self.putb([4, ['Byte: %#04x' % byte, '%#04x' % byte]])
            if len(self.bits) == 16:
                h = self.calculate_humidity(self.bits[-16:])
                self.putv([5, ['Humidity: %.1f %%' % h, 'RH = %.1f %%' % h]])
            elif len(self.bits) == 32:
                t = self.calculate_temperature(self.bits[-16:])
                self.putv([6, ['Temperature: %.1f °C' % t, 'T = %.1f °C' % t]])
            elif len(self.bits) == 40:
                parity = self.bits2num(self.bits[-8:])
                if parity == self.calculate_checksum(self.bits[0:32]):
                    self.putb([7, ['Checksum: OK', 'OK']])
                else:
                    self.putb([7, ['Checksum: not OK', 'NOK']])
                self.state = 'WAIT FOR END'
            self.bytepos.append(self.samplenum)

    def decode(self):
        if not self.samplerate:
            raise SamplerateError('Cannot decode without samplerate.')
        while True:
            # State machine.
            if self.state == 'WAIT FOR START LOW':
                self.wait({0: 'f'})
                self.fall = self.samplenum
                self.state = 'WAIT FOR START HIGH'
            elif self.state == 'WAIT FOR START HIGH':
                self.wait({0: 'r'})
                if self.is_valid('START LOW'):
                    self.rise = self.samplenum
                    self.state = 'WAIT FOR RESPONSE LOW'
                else:
                    self.reset_variables()
            elif self.state == 'WAIT FOR RESPONSE LOW':
                self.wait({0: 'f'})
                if self.is_valid('START HIGH'):
                    self.putfs([0, ['Start', 'S']])
                    self.fall = self.samplenum
                    self.state = 'WAIT FOR RESPONSE HIGH'
                else:
                    self.reset_variables()
            elif self.state == 'WAIT FOR RESPONSE HIGH':
                self.wait({0: 'r'})
                if self.is_valid('RESPONSE LOW'):
                    self.rise = self.samplenum
                    self.state = 'WAIT FOR FIRST BIT'
                else:
                    self.reset_variables()
            elif self.state == 'WAIT FOR FIRST BIT':
                self.wait({0: 'f'})
                if self.is_valid('RESPONSE HIGH'):
                    self.putfs([1, ['Response', 'R']])
                    self.fall = self.samplenum
                    self.bytepos.append(self.samplenum)
                    self.state = 'WAIT FOR BIT HIGH'
                else:
                    self.reset_variables()
            elif self.state == 'WAIT FOR BIT HIGH':
                self.wait({0: 'r'})
                if self.is_valid('BIT LOW'):
                    self.rise = self.samplenum
                    self.state = 'WAIT FOR BIT LOW'
                else:
                    self.reset_variables()
            elif self.state == 'WAIT FOR BIT LOW':
                self.wait({0: 'f'})
                if self.is_valid('BIT 0 HIGH'):
                    bit = 0
                elif self.is_valid('BIT 1 HIGH'):
                    bit = 1
                else:
                    self.reset_variables()
                    continue
                self.handle_byte(bit)
            elif self.state == 'WAIT FOR END':
                self.wait({0: 'r'})
                self.putfs([3, ['End', 'E']])
                self.reset_variables()
