##
## This file is part of the libsigrokdecode project.
##
## Copyright (C) 2014 Matt Ranostay <mranostay@gmail.com>
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

( ANN_RGB, ) = range(1)

class Decoder(srd.Decoder):
    api_version = 3
    id = 'rgb_led_spi'
    name = 'RGB LED (SPI)'
    longname = 'RGB LED string decoder (SPI)'
    desc = 'RGB LED string protocol (RGB values clocked over SPI).'
    license = 'gplv2+'
    inputs = ['spi']
    outputs = []
    tags = ['Display']
    annotations = (
        ('rgb', 'RGB value'),
    )

    def __init__(self):
        self.reset()

    def reset(self):
        self.ss_cmd = None
        self.mosi_bytes = []

    def start(self):
        self.out_ann = self.register(srd.OUTPUT_ANN)

    def putg(self, ss, es, cls, text):
        self.put(ss, es, self.out_ann, [cls, text])

    def decode(self, ss, es, data):
        ptype = data[0]

        # Grab the payload of three DATA packets. These hold the
        # RGB values (in this very order).
        if ptype != 'DATA':
            return
        _, mosi, _ = data
        if not self.mosi_bytes:
            self.ss_cmd = ss
        self.mosi_bytes.append(mosi)
        if len(self.mosi_bytes) < 3:
            return

        # Emit annotations. Invalidate accumulated details as soon as
        # they were processed, to prepare the next iteration.
        ss_cmd, es_cmd = self.ss_cmd, es
        self.ss_cmd = None
        red, green, blue = self.mosi_bytes[:3]
        self.mosi_bytes.clear()
        rgb_value = int(red) << 16 | int(green) << 8 | int(blue)
        self.putg(ss_cmd, es_cmd, ANN_RGB, ['#{:06x}'.format(rgb_value)])
