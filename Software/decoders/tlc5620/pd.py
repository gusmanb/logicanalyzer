##
## This file is part of the libsigrokdecode project.
##
## Copyright (C) 2012-2015 Uwe Hermann <uwe@hermann-uwe.de>
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
from common.srdhelper import SrdIntEnum

Pin = SrdIntEnum.from_str('Pin', 'CLK DATA LOAD LDAC')

dacs = {
    0: 'DACA',
    1: 'DACB',
    2: 'DACC',
    3: 'DACD',
}

class Decoder(srd.Decoder):
    api_version = 3
    id = 'tlc5620'
    name = 'TI TLC5620'
    longname = 'Texas Instruments TLC5620'
    desc = 'Texas Instruments TLC5620 8-bit quad DAC.'
    license = 'gplv2+'
    inputs = ['logic']
    outputs = []
    tags = ['IC', 'Analog/digital']
    channels = (
        {'id': 'clk', 'name': 'CLK', 'desc': 'Serial interface clock'},
        {'id': 'data', 'name': 'DATA', 'desc': 'Serial interface data'},
    )
    optional_channels = (
        {'id': 'load', 'name': 'LOAD', 'desc': 'Serial interface load control'},
        {'id': 'ldac', 'name': 'LDAC', 'desc': 'Load DAC'},
    )
    options = (
        {'id': 'vref_a', 'desc': 'Reference voltage DACA (V)', 'default': 3.3},
        {'id': 'vref_b', 'desc': 'Reference voltage DACB (V)', 'default': 3.3},
        {'id': 'vref_c', 'desc': 'Reference voltage DACC (V)', 'default': 3.3},
        {'id': 'vref_d', 'desc': 'Reference voltage DACD (V)', 'default': 3.3},
    )
    annotations = (
        ('dac-select', 'DAC select'),
        ('gain', 'Gain'),
        ('value', 'DAC value'),
        ('data-latch', 'Data latch point'),
        ('ldac-fall', 'LDAC falling edge'),
        ('bit', 'Bit'),
        ('reg-write', 'Register write'),
        ('voltage-update', 'Voltage update'),
        ('voltage-update-all', 'Voltage update (all DACs)'),
        ('invalid-cmd', 'Invalid command'),
    )
    annotation_rows = (
        ('bits', 'Bits', (5,)),
        ('fields', 'Fields', (0, 1, 2)),
        ('registers', 'Registers', (6, 7)),
        ('voltage-updates', 'Voltage updates', (8,)),
        ('events', 'Events', (3, 4)),
        ('errors', 'Errors', (9,)),
    )

    def __init__(self):
        self.reset()

    def reset(self):
        self.bits = []
        self.ss_dac_first = None
        self.ss_dac = self.es_dac = 0
        self.ss_gain = self.es_gain = 0
        self.ss_value = self.es_value = 0
        self.dac_select = self.gain = self.dac_value = None
        self.dacval = {'A': '?', 'B': '?', 'C': '?', 'D': '?'}
        self.gains = {'A': '?', 'B': '?', 'C': '?', 'D': '?'}

    def start(self):
        self.out_ann = self.register(srd.OUTPUT_ANN)

    def handle_11bits(self):
        # Only look at the last 11 bits, the rest is ignored by the TLC5620.
        if len(self.bits) > 11:
            self.bits = self.bits[-11:]

        # If there are less than 11 bits, something is probably wrong.
        if len(self.bits) < 11:
            ss, es = self.samplenum, self.samplenum
            if len(self.bits) >= 2:
                ss = self.bits[0][1]
                es = self.bits[-1][1] + (self.bits[1][1] - self.bits[0][1])
            self.put(ss, es, self.out_ann, [9, ['Command too short']])
            self.bits = []
            return False

        self.ss_dac = self.bits[0][1]
        self.es_dac = self.ss_gain = self.bits[2][1]
        self.es_gain = self.ss_value = self.bits[3][1]
        self.clock_width = self.es_gain - self.ss_gain
        self.es_value = self.bits[10][1] + self.clock_width # Guessed.

        if self.ss_dac_first is None:
            self.ss_dac_first = self.ss_dac

        s = ''.join(str(i[0]) for i in self.bits[:2])
        self.dac_select = s = dacs[int(s, 2)]
        self.put(self.ss_dac, self.es_dac, self.out_ann,
                 [0, ['DAC select: %s' % s, 'DAC sel: %s' % s,
                      'DAC: %s' % s, 'D: %s' % s, s, s[3]]])

        self.gain = g = 1 + self.bits[2][0]
        self.put(self.ss_gain, self.es_gain, self.out_ann,
                 [1, ['Gain: x%d' % g, 'G: x%d' % g, 'x%d' % g]])

        s = ''.join(str(i[0]) for i in self.bits[3:])
        self.dac_value = v = int(s, 2)
        self.put(self.ss_value, self.es_value, self.out_ann,
                 [2, ['DAC value: %d' % v, 'Value: %d' % v, 'Val: %d' % v,
                      'V: %d' % v, '%d' % v]])

        # Emit an annotation for each bit.
        for i in range(1, 11):
            self.put(self.bits[i - 1][1], self.bits[i][1], self.out_ann,
                     [5, [str(self.bits[i - 1][0])]])
        self.put(self.bits[10][1], self.bits[10][1] + self.clock_width,
                 self.out_ann, [5, [str(self.bits[10][0])]])

        self.bits = []

        return True

    def handle_falling_edge_load(self):
        if not self.handle_11bits():
            return
        s, v, g = self.dac_select, self.dac_value, self.gain
        self.put(self.samplenum, self.samplenum, self.out_ann,
                 [3, ['Falling edge on LOAD', 'LOAD fall', 'F']])
        vref = self.options['vref_%s' % self.dac_select[3].lower()]
        v = '%.2fV' % (vref * (v / 256) * self.gain)
        if self.ldac == 0:
            # If LDAC is low, the voltage is set immediately.
            self.put(self.ss_dac, self.es_value, self.out_ann,
                     [7, ['Setting %s voltage to %s' % (s, v),
                          '%s=%s' % (s, v)]])
        else:
            # If LDAC is high, the voltage is not set immediately, but rather
            # stored in a register. When LDAC goes low all four DAC voltages
            # (DAC A/B/C/D) will be set at the same time.
            self.put(self.ss_dac, self.es_value, self.out_ann,
                     [6, ['Setting %s register value to %s' % \
                          (s, v), '%s=%s' % (s, v)]])
        # Save the last value the respective DAC was set to.
        self.dacval[self.dac_select[-1]] = str(self.dac_value)
        self.gains[self.dac_select[-1]] = self.gain

    def handle_falling_edge_ldac(self):
        self.put(self.samplenum, self.samplenum, self.out_ann,
                 [4, ['Falling edge on LDAC', 'LDAC fall', 'LDAC', 'L']])

        # Don't emit any annotations if we didn't see any register writes.
        if self.ss_dac_first is None:
            return

        # Calculate voltages based on Vref and the per-DAC gain.
        dacval = {}
        for key, val in self.dacval.items():
            if val == '?':
                dacval[key] = '?'
            else:
                vref = self.options['vref_%s' % key.lower()]
                v = vref * (int(val) / 256) * self.gains[key]
                dacval[key] = '%.2fV' % v

        s = ''.join(['DAC%s=%s ' % (d, dacval[d]) for d in 'ABCD']).strip()
        self.put(self.ss_dac_first, self.samplenum, self.out_ann,
                 [8, ['Updating voltages: %s' % s, s, s.replace('DAC', '')]])
        self.ss_dac_first = None

    def handle_new_dac_bit(self, datapin):
        self.bits.append([datapin, self.samplenum])

    def decode(self):
        while True:
            # DATA is shifted in the DAC on the falling CLK edge (MSB-first).
            # A falling edge of LOAD will latch the data.

            # Wait for one (or multiple) of the following conditions:
            #   a) Falling edge on CLK, and/or
            #   b) Falling edge on LOAD, and/or
            #   b) Falling edge on LDAC
            pins = self.wait([{Pin.CLK: 'f'}, {Pin.LOAD: 'f'}, {Pin.LDAC: 'f'}])
            self.ldac = pins[3]

            # Handle those conditions (one or more) that matched this time.
            if self.matched[0]:
                self.handle_new_dac_bit(pins[1])
            if self.matched[1]:
                self.handle_falling_edge_load()
            if self.matched[2]:
                self.handle_falling_edge_ldac()
