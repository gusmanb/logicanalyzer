##
## This file is part of the libsigrokdecode project.
##
## Copyright (C) 2015 Karl Palsson <karlp@tweak.net.au>
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
from .lists import *

TX, RX = range(2)

class Decoder(srd.Decoder):
    api_version = 3
    id = 'mrf24j40'
    name = 'MRF24J40'
    longname = 'Microchip MRF24J40'
    desc = 'IEEE 802.15.4 2.4 GHz RF tranceiver chip.'
    license = 'gplv2+'
    inputs = ['spi']
    outputs = []
    tags = ['IC', 'Wireless/RF']
    annotations = (
        ('sread', 'Short register read'),
        ('swrite', 'Short register write'),
        ('lread', 'Long register read'),
        ('lwrite', 'Long register write'),
        ('warning', 'Warning'),
        ('tx-frame', 'TX frame'),
        ('rx-frame', 'RX frame'),
        ('tx-retry-1', '1x TX retry'),
        ('tx-retry-2', '2x TX retry'),
        ('tx-retry-3', '3x TX retry'),
        ('tx-fail', 'TX fail (too many retries)'),
        ('ccafail', 'CCAFAIL (channel busy)'),
    )
    annotation_rows = (
        ('reads', 'Reads', (0, 2)),
        ('writes', 'Writes', (1, 3)),
        ('warnings', 'Warnings', (4,)),
        ('tx-frames', 'TX frames', (5,)),
        ('rx-frames', 'RX frames', (6,)),
        ('tx-retries-1', '1x TX retries', (7,)),
        ('tx-retries-2', '2x TX retries', (8,)),
        ('tx-retries-3', '3x TX retries', (9,)),
        ('tx-fails', 'TX fails', (10,)),
        ('ccafails', 'CCAFAILs', (11,)),
    )

    def __init__(self):
        self.reset()

    def reset(self):
        self.ss_cmd, self.es_cmd = 0, 0
        self.ss_frame, self.es_frame = [0, 0], [0, 0]
        self.mosi_bytes, self.miso_bytes = [], []
        self.framecache = [[], []]

    def start(self):
        self.out_ann = self.register(srd.OUTPUT_ANN)

    def putx(self, data):
        self.put(self.ss_cmd, self.es_cmd, self.out_ann, data)

    def putw(self, pos, msg):
        self.put(pos[0], pos[1], self.out_ann, [4, [msg]])

    def reset_data(self):
        self.mosi_bytes = []
        self.miso_bytes = []

    def handle_short(self):
        write = self.mosi_bytes[0] & 0x1
        reg = (self.mosi_bytes[0] >> 1) & 0x3f
        reg_desc = sregs.get(reg, 'illegal')
        for rxtx in (RX, TX):
            if self.framecache[rxtx] == []:
                continue
            bit0 = self.mosi_bytes[1] & (1 << 0)
            if rxtx == TX and not (reg_desc == 'TXNCON' and bit0 == 1):
                continue
            if rxtx == RX and not (reg_desc == 'RXFLUSH' and bit0 == 1):
                continue
            idx = 5 if rxtx == TX else 6
            xmitdir = 'TX' if rxtx == TX else 'RX'
            frame = ' '.join(['%02X' % b for b in self.framecache[rxtx]])
            self.put(self.ss_frame[rxtx], self.es_frame[rxtx], self.out_ann,
                [idx, ['%s frame: %s' % (xmitdir, frame)]])
            self.framecache[rxtx] = []
        if write:
            self.putx([1, ['%s: %#x' % (reg_desc, self.mosi_bytes[1])]])
        else:
            self.putx([0, ['%s: %#x' % (reg_desc, self.miso_bytes[1])]])
            numretries = (self.miso_bytes[1] & 0xc0) >> 6
            if reg_desc == 'TXSTAT' and numretries > 0:
                txfail = 1 if ((self.miso_bytes[1] & (1 << 0)) != 0) else 0
                idx = 6 + numretries + txfail
                if txfail:
                    self.putx([idx, ['TX fail (>= 4 retries)', 'TX fail']])
                else:
                    self.putx([idx, ['TX retries: %d' % numretries]])
            if reg_desc == 'TXSTAT' and (self.miso_bytes[1] & (1 << 5)) != 0:
                self.putx([11, ['CCAFAIL (channel busy)', 'CCAFAIL']])

    def handle_long(self):
        dword = self.mosi_bytes[0] << 8 | self.mosi_bytes[1]
        write = dword & (0x1 << 4)
        reg = dword >> 5 & 0x3ff
        if reg >= 0x0:
            reg_desc = 'TX:%#x' % reg
        if reg >= 0x80:
            reg_desc = 'TX beacon:%#x' % reg
        if reg >= 0x100:
            reg_desc = 'TX GTS1:%#x' % reg
        if reg >= 0x180:
            reg_desc = 'TX GTS2:%#x' % reg
        if reg >= 0x200:
            reg_desc = lregs.get(reg, 'illegal')
        if reg >= 0x280:
            reg_desc = 'Security keys:%#x' % reg
        if reg >= 0x2c0:
            reg_desc = 'Reserved:%#x' % reg
        if reg >= 0x300:
            reg_desc = 'RX:%#x' % reg

        if write:
            self.putx([3, ['%s: %#x' % (reg_desc, self.mosi_bytes[2])]])
        else:
            self.putx([2, ['%s: %#x' % (reg_desc, self.miso_bytes[2])]])

        for rxtx in (RX, TX):
            if rxtx == RX and reg_desc[:3] != 'RX:':
                continue
            if rxtx == TX and reg_desc[:3] != 'TX:':
                continue
            if len(self.framecache[rxtx]) == 0:
                self.ss_frame[rxtx] = self.ss_cmd
            self.es_frame[rxtx] = self.es_cmd
            self.framecache[rxtx] += [self.mosi_bytes[2]] if rxtx == TX else [self.miso_bytes[2]]

    def decode(self, ss, es, data):
        ptype = data[0]
        if ptype == 'CS-CHANGE':
            # If we transition high mid-stream, toss out our data and restart.
            cs_old, cs_new = data[1:]
            if cs_old is not None and cs_old == 0 and cs_new == 1:
                if len(self.mosi_bytes) not in (0, 2, 3):
                    self.putw([self.ss_cmd, es], 'Misplaced CS!')
                    self.reset_data()
            return

        # Don't care about anything else.
        if ptype != 'DATA':
            return
        mosi, miso = data[1:]

        self.ss, self.es = ss, es

        if len(self.mosi_bytes) == 0:
            self.ss_cmd = ss
        self.mosi_bytes.append(mosi)
        self.miso_bytes.append(miso)

        # Everything is either 2 bytes or 3 bytes.
        if len(self.mosi_bytes) < 2:
            return

        if self.mosi_bytes[0] & 0x80:
            if len(self.mosi_bytes) == 3:
                self.es_cmd = es
                self.handle_long()
                self.reset_data()
        else:
            self.es_cmd = es
            self.handle_short()
            self.reset_data()
