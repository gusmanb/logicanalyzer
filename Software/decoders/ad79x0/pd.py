##
## This file is part of the libsigrokdecode project.
##
## Copyright (C) 2020 Analog Devices Inc.
##
## This program is free software; you can redistribute it and/or modify
## it under the terms of the GNU General Public License as published by
## the Free Software Foundation; either version 3 of the License, or
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

modes = {
    0: ['Normal Mode', 'Normal', 'Norm', 'N'],
    1: ['Power Down Mode', 'Power Down', 'PD'],
    2: ['Power Up Mode', 'Power Up', 'PU'],
}

input_voltage_format = ['%.6fV', '%.2fV']

validation = {
    'invalid': ['Invalid data', 'Invalid', 'N/A'],
    'incomplete': ['Incomplete conversion', 'Incomplete', 'I'],
    'complete': ['Complete conversion', 'Complete', 'C'],
}

class Decoder(srd.Decoder):
    api_version = 3
    id = 'ad79x0'
    name = 'AD79x0'
    longname = 'Analog Devices AD79x0'
    desc = 'Analog Devices AD7910/AD7920 12-bit ADC.'
    license = 'gplv2+'
    inputs = ['spi']
    outputs = []
    tags = ['IC', 'Analog/digital']
    annotations = (
        ('mode', 'Mode'),
        ('voltage', 'Voltage'),
        ('validation', 'Validation'),
    )
    annotation_rows = (
        ('modes', 'Modes', (0,)),
        ('voltages', 'Voltages', (1,)),
        ('data_validation', 'Data validation', (2,)),
    )
    options = (
        {'id': 'vref', 'desc': 'Reference voltage (V)', 'default': 1.5},
    )

    def __init__(self,):
        self.reset()

    def reset(self):
        self.samplerate = 0
        self.samples_bit = -1
        self.ss = -1
        self.start_sample = 0
        self.previous_state = 0
        self.data = 0

    def metadata(self, key, value):
        if key == srd.SRD_CONF_SAMPLERATE:
            self.samplerate = value

    def start(self):
        self.out_ann = self.register(srd.OUTPUT_ANN)

    def put_validation(self, pos, msg):
        self.put(pos[0], pos[1], self.out_ann, [2, validation[msg]])

    def put_data(self, pos, input_voltage):
        ann = []
        for format in input_voltage_format:
            ann.append(format % input_voltage)
        self.put(pos[0], pos[1], self.out_ann, [1, ann])

    def put_mode(self, pos, msg):
        self.put(pos[0], pos[1], self.out_ann, [0, modes[msg]])

    def decode(self, ss, es, data):
        ptype = data[0]

        if ptype == 'CS-CHANGE':
            cs_old, cs_new = data[1:]
            if cs_old is not None and cs_old == 0 and cs_new == 1:
                if self.samples_bit == -1:
                    return
                self.data >>= 1
                nb_bits = (ss - self.ss) // self.samples_bit
                if nb_bits >= 10:
                    if self.data == 0xFFF:
                        self.put_mode([self.start_sample, es], 2)
                        self.previous_state = 0
                        self.put_validation([self.start_sample, es], 'invalid')
                    else:
                        self.put_mode([self.start_sample, es], 0)
                        if nb_bits == 16:
                            self.put_validation([self.start_sample, es], 'complete')
                        elif nb_bits < 16:
                            self.put_validation([self.start_sample, es], 'incomplete')
                        vin = (self.data / ((2**12) - 1)) * self.options['vref']
                        self.put_data([self.start_sample, es], vin)
                elif nb_bits < 10:
                    self.put_mode([self.start_sample, es], 1)
                    self.previous_state = 1
                    self.put_validation([self.start_sample, es], 'invalid')

                self.ss = -1
                self.samples_bit = -1
                self.data = 0
            elif cs_old is not None and cs_old == 1 and cs_new == 0:
                self.start_sample = ss
                self.samples_bit = -1

        elif ptype == 'BITS':
            if data[2] is None:
                return
            miso = data[2]
            if self.samples_bit == -1:
                self.samples_bit = miso[0][2] - miso[0][1]

            if self.ss == -1:
                self.ss = ss

            for bit in reversed(miso):
                self.data = self.data | bit[0]
                self.data <<= 1
