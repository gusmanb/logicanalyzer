##
## This file is part of the libsigrokdecode project.
##
## Copyright (C) 2016 fenugrec <fenugrec users.sourceforge.net>
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

# TODO:
#  - Annotations are very crude and could be improved.
#  - Annotate every nibble? Would give insight on interrupted shifts.
#  - Annotate invalid "command" nibbles while SYNC==1?

import sigrokdecode as srd

class Decoder(srd.Decoder):
    api_version = 3
    id = 'aud'
    name = 'AUD'
    longname = 'Advanced User Debugger'
    desc = 'Renesas/Hitachi Advanced User Debugger (AUD) protocol.'
    license = 'gplv2+'
    inputs = ['logic']
    outputs = []
    tags = ['Debug/trace']
    channels = (
        {'id': 'audck', 'name': 'AUDCK', 'desc': 'AUD clock'},
        {'id': 'naudsync', 'name': 'nAUDSYNC', 'desc': 'AUD sync'},
        {'id': 'audata3', 'name': 'AUDATA3', 'desc': 'AUD data line 3'},
        {'id': 'audata2', 'name': 'AUDATA2', 'desc': 'AUD data line 2'},
        {'id': 'audata1', 'name': 'AUDATA1', 'desc': 'AUD data line 1'},
        {'id': 'audata0', 'name': 'AUDATA0', 'desc': 'AUD data line 0'},
    )
    annotations = (
        ('dest', 'Destination address'),
    )

    def __init__(self):
        self.reset()

    def reset(self):
        self.ncnt = 0
        self.nmax = 0
        self.addr = 0
        self.lastaddr = 0
        self.ss = 0

    def start(self):
        self.out_ann = self.register(srd.OUTPUT_ANN)

    def putx(self, data):
        self.put(self.ss, self.samplenum, self.out_ann, data)

    def handle_clk_edge(self, clk, sync, datapins):
        # Reconstruct nibble.
        nib = 0
        for i in range(4):
            nib |= datapins[3-i] << i

        # sync == 1: annotate if finished; update cmd.
        # TODO: Annotate idle level (nibble = 0x03 && SYNC=1).
        if sync == 1:
            if (self.ncnt == self.nmax) and (self.nmax != 0):
                # Done shifting an address: annotate.
                self.putx([0, ['0x%08X' % self.addr]])
                self.lastaddr = self.addr

            self.ncnt = 0
            self.addr = self.lastaddr
            self.ss = self.samplenum
            if nib == 0x08:
                self.nmax = 1
            elif nib == 0x09:
                self.nmax = 2
            elif nib == 0x0a:
                self.nmax = 4
            elif nib == 0x0b:
                self.nmax = 8
            else:
                # Undefined or idle.
                self.nmax = 0
        else:
            # sync == 0, valid cmd: start or continue shifting in nibbles.
            if (self.nmax > 0):
                # Clear tgt nibble.
                self.addr &= ~(0x0F << (self.ncnt * 4))
                # Set nibble.
                self.addr |= nib << (self.ncnt * 4)
                self.ncnt += 1

    def decode(self):
        while True:
            pins = self.wait({0: 'r'})
            clk = pins[0]
            sync = pins[1]
            d = pins[2:]
            self.handle_clk_edge(clk, sync, d)
