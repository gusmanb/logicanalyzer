##
## This file is part of the libsigrokdecode project.
##
## Copyright (C) 2018 Stefan Brüns <stefan.bruens@rwth-aachen.de>
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

PIN_DATA, PIN_RESET = range(2)
ROW_EDGE, ROW_WORD, ROW_RESET = range(3)

class Decoder(srd.Decoder):
    api_version = 3
    id = 'counter'
    name = 'Counter'
    longname = 'Edge counter'
    desc = 'Count the number of edges in a signal.'
    license = 'gplv2+'
    inputs = ['logic']
    outputs = []
    tags = ['Util']
    channels = (
        {'id': 'data', 'name': 'Data', 'desc': 'Data line'},
    )
    optional_channels = (
        {'id': 'reset', 'name': 'Reset', 'desc': 'Reset line'},
    )
    annotations = (
        ('edge_count', 'Edge count'),
        ('word_count', 'Word count'),
        ('word_reset', 'Word reset'),
    )
    annotation_rows = (
        ('edge_counts', 'Edges', (ROW_EDGE,)),
        ('word_counts', 'Words', (ROW_WORD,)),
        ('word_resets', 'Word resets', (ROW_RESET,)),
    )
    options = (
        {'id': 'data_edge', 'desc': 'Edges to count (data)', 'default': 'any',
            'values': ('any', 'rising', 'falling')},
        {'id': 'divider', 'desc': 'Count divider (word width)', 'default': 0},
        {'id': 'reset_edge', 'desc': 'Edge which clears counters (reset)',
            'default': 'falling', 'values': ('any', 'rising', 'falling')},
        {'id': 'edge_off', 'desc': 'Edge counter value after start/reset', 'default': 0},
        {'id': 'word_off', 'desc': 'Word counter value after start/reset', 'default': 0},
        {'id': 'dead_cycles', 'desc': 'Ignore this many edges after reset', 'default': 0},
        {'id': 'start_with_reset', 'desc': 'Assume decode starts with reset',
            'default': 'no', 'values': ('no', 'yes')},
    )

    def __init__(self):
        self.reset()

    def reset(self):
        pass

    def metadata(self, key, value):
        if key == srd.SRD_CONF_SAMPLERATE:
            self.samplerate = value

    def start(self):
        self.out_ann = self.register(srd.OUTPUT_ANN)

    def putc(self, cls, ss, annlist):
        self.put(ss, self.samplenum, self.out_ann, [cls, annlist])

    def decode(self):
        opt_edge_map = {'rising': 'r', 'falling': 'f', 'any': 'e'}

        data_edge = self.options['data_edge']
        divider = self.options['divider']
        if divider < 0:
            divider = 0
        reset_edge = self.options['reset_edge']

        condition = [{PIN_DATA: opt_edge_map[data_edge]}]
        have_reset = self.has_channel(PIN_RESET)
        if have_reset:
            cond_reset = len(condition)
            condition.append({PIN_RESET: opt_edge_map[reset_edge]})

        edge_count = int(self.options['edge_off'])
        edge_start = None
        word_count = int(self.options['word_off'])
        word_start = None

        if self.options['start_with_reset'] == 'yes':
            dead_count = int(self.options['dead_cycles'])
        else:
            dead_count = 0

        while True:
            self.wait(condition)
            now = self.samplenum

            if have_reset and self.matched[cond_reset]:
                edge_count = int(self.options['edge_off'])
                edge_start = now
                word_count = int(self.options['word_off'])
                word_start = now
                self.putc(ROW_RESET, now, ['Word reset', 'Reset', 'Rst', 'R'])
                dead_count = int(self.options['dead_cycles'])
                continue

            if dead_count:
                dead_count -= 1
                edge_start = now
                word_start = now
                continue

            # Implementation note: In the absence of a RESET condition
            # before the first data edge, any arbitrary choice of where
            # to start the annotation is valid. One may choose to emit a
            # narrow annotation (where ss=es), or assume that the cycle
            # which corresponds to the counter value started at sample
            # number 0. We decided to go with the latter here, to avoid
            # narrow annotations (see bug #1210). None of this matters in
            # the presence of a RESET condition in the input stream.
            if edge_start is None:
                edge_start = 0
            if word_start is None:
                word_start = 0

            edge_count += 1
            self.putc(ROW_EDGE, edge_start, ["{:d}".format(edge_count)])
            edge_start = now

            word_edge_count = edge_count - int(self.options['edge_off'])
            if divider and (word_edge_count % divider) == 0:
                word_count += 1
                self.putc(ROW_WORD, word_start, ["{:d}".format(word_count)])
                word_start = now
