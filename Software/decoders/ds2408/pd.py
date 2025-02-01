##
## This file is part of the libsigrokdecode project.
##
## Copyright (C) 2019 Mariusz Bialonczyk <manio@skyboo.net>
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

# Dictionary of FUNCTION commands and their names.
command = {
    0xf0: 'Read PIO Registers',
    0xf5: 'Channel Access Read',
    0x5a: 'Channel Access Write',
    0xcc: 'Write Conditional Search Register',
    0xc3: 'Reset Activity Latches',
    0x3c: 'Disable Test Mode',
}

class Decoder(srd.Decoder):
    api_version = 3
    id = 'ds2408'
    name = 'DS2408'
    longname = 'Maxim DS2408'
    desc = '1-Wire 8-channel addressable switch.'
    license = 'gplv2+'
    inputs = ['onewire_network']
    outputs = []
    tags = ['Embedded/industrial', 'IC']
    annotations = (
        ('text', 'Text'),
    )

    def __init__(self):
        self.reset()

    def reset(self):
        # Bytes for function command.
        self.bytes = []

    def start(self):
        self.out_ann = self.register(srd.OUTPUT_ANN)

    def putx(self, data):
        self.put(self.ss, self.es, self.out_ann, data)

    def decode(self, ss, es, data):
        code, val = data

        if code == 'RESET/PRESENCE':
            self.ss, self.es = ss, es
            self.putx([0, ['Reset/presence: %s'
                           % ('true' if val else 'false')]])
            self.bytes = []
        elif code == 'ROM':
            self.ss, self.es = ss, es
            family_code = val & 0xff
            self.putx([0, ['ROM: 0x%016x (family code 0x%02x)' % (val, family_code)]])
            self.bytes = []
        elif code == 'DATA':
            self.bytes.append(val)
            if 1 == len(self.bytes):
                self.ss, self.es = ss, es
                if val not in command:
                    self.putx([0, ['Unrecognized command: 0x%02x' % val]])
                else:
                    self.putx([0, ['%s (0x%02x)' % (command[val], val)]])
            elif 0xf0 == self.bytes[0]: # Read PIO Registers
                if 2 == len(self.bytes):
                    self.ss = ss
                elif 3 == len(self.bytes):
                    self.es = es
                    self.putx([0, ['Target address: 0x%04x'
                                   % ((self.bytes[2] << 8) + self.bytes[1])]])
                elif 3 < len(self.bytes):
                    self.ss, self.es = ss, es
                    self.putx([0, ['Data: 0x%02x' % self.bytes[-1]]])
            elif 0xf5 == self.bytes[0]: # Channel Access Read
                if 2 == len(self.bytes):
                    self.ss = ss
                elif 2 < len(self.bytes):
                    self.ss, self.es = ss, es
                    self.putx([0, ['PIO sample: 0x%02x' % self.bytes[-1]]])
            elif 0x5a == self.bytes[0]: # Channel Access Write
                if 2 == len(self.bytes):
                    self.ss = ss
                elif 3 == len(self.bytes):
                    self.es = es
                    if (self.bytes[-1] == (self.bytes[-2] ^ 0xff)):
                      self.putx([0, ['Data: 0x%02x (bit-inversion correct: 0x%02x)' % (self.bytes[-2], self.bytes[-1])]])
                    else:
                      self.putx([0, ['Data error: second byte (0x%02x) is not bit-inverse of first (0x%02x)' % (self.bytes[-1], self.bytes[-2])]])
                elif 3 < len(self.bytes):
                    self.ss, self.es = ss, es
                    if 0xaa == self.bytes[-1]:
                      self.putx([0, ['Success']])
                    elif 0xff == self.bytes[-1]:
                      self.putx([0, ['Fail New State']])
            elif 0xcc == self.bytes[0]: # Write Conditional Search Register
                if 2 == len(self.bytes):
                    self.ss = ss
                elif 3 == len(self.bytes):
                    self.es = es
                    self.putx([0, ['Target address: 0x%04x'
                                   % ((self.bytes[2] << 8) + self.bytes[1])]])
                elif 3 < len(self.bytes):
                    self.ss, self.es = ss, es
                    self.putx([0, ['Data: 0x%02x' % self.bytes[-1]]])
            elif 0xc3 == self.bytes[0]: # Reset Activity Latches
                if 2 == len(self.bytes):
                    self.ss = ss
                elif 2 < len(self.bytes):
                    self.ss, self.es = ss, es
                    if 0xaa == self.bytes[-1]:
                      self.putx([0, ['Success']])
                    else:
                      self.putx([0, ['Invalid byte']])
