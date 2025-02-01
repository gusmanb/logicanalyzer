##
## This file is part of the libsigrokdecode project.
##
## Copyright (C) 2015 Petteri Aimonen <jpa@sigrok.mail.kapsi.fi>
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
    id = 'arm_tpiu'
    name = 'ARM TPIU'
    longname = 'ARM Trace Port Interface Unit'
    desc = 'Filter TPIU formatted trace data into separate streams.'
    license = 'gplv2+'
    inputs = ['uart']
    outputs = ['uart'] # Emulate uart output so that arm_itm/arm_etm can stack.
    tags = ['Debug/trace']
    options = (
        {'id': 'stream', 'desc': 'Stream index', 'default': 1},
        {'id': 'sync_offset', 'desc': 'Initial sync offset', 'default': 0},
    )
    annotations = (
        ('stream', 'Current stream'),
        ('data', 'Stream data'),
    )
    annotation_rows = (
        ('streams', 'Current streams', (0,)),
        ('data-vals', 'Stream data', (1,)),
    )

    def __init__(self):
        self.reset()

    def reset(self):
        self.buf = []
        self.syncbuf = []
        self.prevsample = 0
        self.stream = 0
        self.ss_stream = None
        self.bytenum = 0

    def start(self):
        self.out_ann = self.register(srd.OUTPUT_ANN)
        self.out_python = self.register(srd.OUTPUT_PYTHON)

    def stream_changed(self, ss, stream):
        if self.stream != stream:
            if self.stream != 0:
                self.put(self.ss_stream, ss, self.out_ann,
                         [0, ['Stream %d' % self.stream, 'S%d' % self.stream]])
            self.stream = stream
            self.ss_stream = ss

    def emit_byte(self, ss, es, byte):
        if self.stream == self.options['stream']:
            self.put(ss, es, self.out_ann, [1, ['0x%02x' % byte]])
            self.put(ss, es, self.out_python, ['DATA', 0, (byte, [])])

    def process_frame(self, buf):
        # Byte 15 contains the lowest bits of bytes 0, 2, ... 14.
        lowbits = buf[15][2]

        for i in range(0, 15, 2):
            # Odd bytes can be stream ID or data.
            delayed_stream_change = None
            lowbit = (lowbits >> (i // 2)) & 0x01
            if buf[i][2] & 0x01 != 0:
                if lowbit:
                    delayed_stream_change = buf[i][2] >> 1
                else:
                    self.stream_changed(buf[i][0], buf[i][2] >> 1)
            else:
                byte = buf[i][2] | lowbit
                self.emit_byte(buf[i][0], buf[i][1], byte)

            # Even bytes are always data.
            if i < 14:
                self.emit_byte(buf[i+1][0], buf[i+1][1], buf[i+1][2])

            # The stream change can be delayed to occur after the data byte.
            if delayed_stream_change is not None:
                self.stream_changed(buf[i+1][1], delayed_stream_change)

    def decode(self, ss, es, data):
        ptype, rxtx, pdata = data

        if ptype != 'DATA':
            return

        # Reset packet if there is a long pause between bytes.
        self.byte_len = es - ss
        if ss - self.prevsample > self.byte_len:
            self.buf = []
        self.prevsample = es

        self.buf.append((ss, es, pdata[0]))
        self.bytenum += 1

        # Allow skipping N first bytes of the data. By adjusting the sync
        # value, one can get initial synchronization as soon as the trace
        # starts.
        if self.bytenum < self.options['sync_offset']:
            self.buf = []
            return

        # Keep separate buffer for detection of sync packets.
        # Sync packets override everything else, so that we can regain sync
        # even if some packets are corrupted.
        self.syncbuf = self.syncbuf[-3:] + [pdata[0]]
        if self.syncbuf == [0xFF, 0xFF, 0xFF, 0x7F]:
            self.buf = []
            self.syncbuf = []
            return

        if len(self.buf) == 16:
            self.process_frame(self.buf)
            self.buf = []
