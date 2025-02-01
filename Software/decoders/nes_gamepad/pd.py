##
## This file is part of the libsigrokdecode project.
##
## Copyright (C) 2019 Stephan Thiele <stephan.thiele@mailbox.org>
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

class Decoder(srd.Decoder):
    api_version = 3
    id = 'nes_gamepad'
    name = 'NES gamepad'
    longname = 'Nintendo Entertainment System gamepad'
    desc = 'NES gamepad button states.'
    license = 'gplv2+'
    inputs = ['spi']
    outputs = []
    tags = ['Retro computing']
    options = (
        # Currently only the standard controller is supported. This might be
        # extended by special controllers like the Nintendo Zapper light gun.
        {'id': 'variant', 'desc': 'Gamepad variant',
            'default': 'Standard gamepad', 'values': ('Standard gamepad',)},
    )
    annotations = (
        ('button', 'Button state'),
        ('no-press', 'No button press'),
        ('not-connected', 'Gamepad unconnected')
    )
    annotation_rows = (
        ('buttons', 'Button states', (0,)),
        ('no-presses', 'No button presses', (1,)),
        ('not-connected-vals', 'Gamepad unconnected', (2,)),
    )

    def __init__(self):
        self.reset()

    def reset(self):
        self.variant = None

    def start(self):
        self.out_ann = self.register(srd.OUTPUT_ANN)
        self.variant = self.options['variant']

    def putg(self, ss, es, cls, text):
        self.put(ss, es, self.out_ann, [cls, [text]])

    def handle_data(self, ss, es, value):
        if value == 0xff:
            self.putg(ss, es, 1, 'No button is pressed')
            return

        if value == 0x00:
            self.putg(ss, es, 2, 'Gamepad is not connected')
            return

        buttons = [
            'A',
            'B',
            'Select',
            'Start',
            'North',
            'South',
            'West',
            'East',
        ]

        bits = '{:08b}'.format(value)
        text = [buttons[i] for i, b in enumerate(bits) if b == '0']
        text = ' + '.join(text)
        self.putg(ss, es, 0, text)

    def decode(self, ss, es, data):
        ptype, _, _ = data
        if ptype == 'DATA':
            _, _, miso = data
            self.handle_data(ss, es, miso)
            return
