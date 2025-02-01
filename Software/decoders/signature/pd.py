##
## This file is part of the libsigrokdecode project.
##
## Copyright (C) 2019 Shirow Miura <shirowmiura@gmail.com>
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

symbol_map = {
    0b0000: '0',
    0b1000: '1',
    0b0100: '2',
    0b1100: '3',
    0b0010: '4',
    0b1010: '5',
    0b0110: '6',
    0b1110: '7',
    0b0001: '8',
    0b1001: '9',
    0b0101: 'A',
    0b1101: 'C',
    0b0011: 'F',
    0b1011: 'H',
    0b0111: 'P',
    0b1111: 'U',
}

START, STOP, CLOCK, DATA = range(4)

class Decoder(srd.Decoder):
    api_version = 3
    id = 'signature'
    name = 'Signature'
    longname = 'Signature analysis'
    desc = 'Annotate signature of logic patterns.'
    license = 'gplv2+'
    inputs = ['logic']
    outputs = []
    tags = ['Debug/trace', 'Util', 'Encoding']
    channels = (
        {'id': 'start', 'name': 'START', 'desc': 'START channel'},
        {'id': 'stop', 'name': 'STOP', 'desc': 'STOP channel'},
        {'id': 'clk', 'name': 'CLOCK', 'desc': 'CLOCK channel'},
        {'id': 'data', 'name': 'DATA', 'desc': 'DATA channel'},
    )
    options = (
        {'id': 'start_edge', 'desc': 'START edge polarity',
            'default': 'rising', 'values': ('rising', 'falling')},
        {'id': 'stop_edge', 'desc': 'STOP edge polarity',
            'default': 'rising', 'values': ('rising', 'falling')},
        {'id': 'clk_edge', 'desc': 'CLOCK edge polarity',
            'default': 'falling', 'values': ('rising', 'falling')},
        {'id': 'annbits', 'desc': 'Enable bit level annotations',
            'default': 'no', 'values': ('yes', 'no')},
    )
    annotations = (
        ('bit0', 'Bit0'),
        ('bit1', 'Bit1'),
        ('start', 'START'),
        ('stop', 'STOP'),
        ('signature', 'Signature')
    )
    annotation_rows = (
        ('bits', 'Bits', (0, 1, 2, 3)),
        ('signatures', 'Signatures', (4,))
    )

    def __init__(self):
        self.reset()

    def reset(self):
        pass

    def start(self):
        self.out_ann = self.register(srd.OUTPUT_ANN)

    def putsig(self, ss, es, signature):
        s = ''.join([symbol_map[(signature >>  0) & 0x0f],
                     symbol_map[(signature >>  4) & 0x0f],
                     symbol_map[(signature >>  8) & 0x0f],
                     symbol_map[(signature >> 12) & 0x0f]])
        self.put(ss, es, self.out_ann, [4, [s]])

    def putb(self, ss, ann):
        self.put(ss, self.samplenum, self.out_ann, ann)

    def decode(self):
        opt = self.options
        start_edge_mode_rising = opt['start_edge'] == 'rising'
        stop_edge_mode_rising = opt['stop_edge'] == 'rising'
        annbits = opt['annbits'] == 'yes'
        gate_is_open = False
        sample_start = None
        started = False
        last_samplenum = 0
        prev_start = 0 if start_edge_mode_rising else 1
        prev_stop = 0 if stop_edge_mode_rising else 1
        shiftreg = 0

        while True:
            start, stop, _, data = self.wait({CLOCK: opt['clk_edge']})
            if start != prev_start and not gate_is_open:
                gate_is_open = (start == 1) if start_edge_mode_rising else (start == 0)
                if gate_is_open:
                    # Start sampling.
                    sample_start = self.samplenum
                    started = True
            elif stop != prev_stop and gate_is_open:
                gate_is_open = not ((stop == 1) if stop_edge_mode_rising else (stop == 0))
                if not gate_is_open:
                    # Stop sampling.
                    if annbits:
                        self.putb(last_samplenum, [3, ['STOP', 'STP', 'P']])
                    self.putsig(sample_start, self.samplenum, shiftreg)
                    shiftreg = 0
                    sample_start = None
            if gate_is_open:
                if annbits:
                    if started:
                        s = '<{}>'.format(data)
                        self.putb(last_samplenum, [2, ['START' + s, 'STR' + s, 'S' + s]])
                        started = False
                    else:
                        self.putb(last_samplenum, [data, [str(data)]])
                incoming = (bin(shiftreg & 0x0291).count('1') + data) & 1
                shiftreg = (incoming << 15) | (shiftreg >> 1)
            prev_start = start
            prev_stop = stop
            last_samplenum = self.samplenum
