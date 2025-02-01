##
## This file is part of the libsigrokdecode project.
##
## Copyright (C) 2012 Iztok Jeras <iztok.jeras@gmail.com>
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
    # Scratchpad
    0x4e: 'Write scratchpad',
    0xbe: 'Read scratchpad',
    0x48: 'Copy scratchpad',
    # Thermometer
    0x44: 'Convert temperature',
    0xb4: 'Read power mode',
    0xb8: 'Recall EEPROM',
    0xf5: 'PIO access read',
    0xA5: 'PIO access write',
    0x99: 'Chain',
}

class Decoder(srd.Decoder):
    api_version = 3
    id = 'ds28ea00'
    name = 'DS28EA00'
    longname = 'Maxim DS28EA00 1-Wire digital thermometer'
    desc = '1-Wire digital thermometer with Sequence Detect and PIO.'
    license = 'gplv2+'
    inputs = ['onewire_network']
    outputs = []
    tags = ['IC', 'Sensor']
    annotations = (
        ('text', 'Text'),
    )

    def __init__(self):
        self.reset()

    def reset(self):
        self.trn_beg = 0
        self.trn_end = 0
        self.state = 'ROM'
        self.rom = 0x0000000000000000

    def start(self):
        self.out_ann = self.register(srd.OUTPUT_ANN)

    def putx(self, data):
        self.put(self.ss, self.es, self.out_ann, data)

    def decode(self, ss, es, data):
        code, val = data

        self.ss, self.es = ss, es

        # State machine.
        if code == 'RESET/PRESENCE':
            self.putx([0, ['Reset/presence: %s'
                           % ('true' if val else 'false')]])
            self.state = 'ROM'
        elif code == 'ROM':
            self.rom = val
            self.putx([0, ['ROM: 0x%016x' % (val)]])
            self.state = 'COMMAND'
        elif code == 'DATA':
            if self.state == 'COMMAND':
                if val not in command:
                    self.putx([0, ['Unrecognized command: 0x%02x' % val]])
                    return
                self.putx([0, ['Function command: 0x%02x \'%s\''
                          % (val, command[val])]])
                self.state = command[val].upper()
            elif self.state == 'READ SCRATCHPAD':
                self.putx([0, ['Scratchpad data: 0x%02x' % val]])
            elif self.state == 'CONVERT TEMPERATURE':
                self.putx([0, ['Temperature conversion status: 0x%02x' % val]])
            elif self.state in [s.upper() for s in command.values()]:
                self.putx([0, ['TODO \'%s\': 0x%02x' % (self.state, val)]])
