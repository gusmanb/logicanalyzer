##
## This file is part of the libsigrokdecode project.
##
## Copyright (C) 2018 Steve R <steversig@virginmedia.com>
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
from common.srdhelper import bcd2int

class Decoder(srd.Decoder):
    api_version = 3
    id = 'ook_vis'
    name = 'OOK visualisation'
    longname = 'On-off keying visualisation'
    desc = 'OOK visualisation in various formats.'
    license = 'gplv2+'
    inputs = ['ook']
    outputs = ['ook']
    tags = ['Encoding']
    annotations = (
        ('bit', 'Bit'),
        ('ref', 'Reference'),
        ('field', 'Field'),
        ('ref_field', 'Ref field'),
        ('level2', 'L2'),
        ('ref_level2', 'Ref L2'),
    )
    annotation_rows = (
        ('bits', 'Bits', (0,)),
        ('compare', 'Compare', (1,)),
        ('fields', 'Fields', (2,)),
        ('ref_fields', 'Ref fields', (3,)),
        ('level2_vals', 'L2', (4,)),
        ('ref_level2_vals', 'Ref L2', (5,)),
    )
    options = (
        {'id': 'displayas', 'desc': 'Display as', 'default': 'Nibble - Hex',
         'values': ('Byte - Hex', 'Byte - Hex rev', 'Byte - BCD',
         'Byte - BCD rev', 'Nibble - Hex', 'Nibble - Hex rev', 'Nibble - BCD',
         'Nibble - BCD rev')},
        {'id': 'synclen', 'desc': 'Sync length', 'default': '4',
         'values': ('0', '1', '2', '3', '4', '5', '6', '7', '8', '9', '10')},
        {'id': 'syncoffset', 'desc': 'Sync offset', 'default': '0',
         'values': ('-4', '-3', '-2', '-1', '0', '1', '2', '3', '4')},
        {'id': 'refsample', 'desc': 'Compare', 'default': 'off', 'values':
        ('off', 'show numbers', '1', '2', '3', '4', '5', '6', '7', '8', '9',
         '10', '11', '12', '13', '14', '15', '16', '17', '18', '19', '20',
         '21', '22', '23', '24', '25', '26', '27', '28', '29', '30')},
    )

    def __init__(self):
        self.reset()

    def reset(self):
        self.decoded = [] # Local cache of decoded OOK.
        self.ookstring = ''
        self.ookcache = []
        self.trace_num = 0

    def start(self):
        self.out_ann = self.register(srd.OUTPUT_ANN)
        self.out_python = self.register(srd.OUTPUT_PYTHON)
        self.displayas = self.options['displayas']
        self.sync_length = self.options['synclen']
        self.sync_offset = self.options['syncoffset']
        self.ref = self.options['refsample']

    def putx(self, data):
        self.put(self.ss, self.es, self.out_ann, data)

    def putp(self, data):
        self.put(self.ss, self.es, self.out_python, data)

    def display_level2(self, bits, line):
        self.decode_pos = 0
        ook = self.decoded
        # Find the end of the preamble which could be 1010 or 1111.
        if len(ook) > 1:
            preamble_end = len(ook) + 1
            char_first = ook[0][2]
            char_second = ook[1][2]
            if char_first == char_second: # 1111
                preamble = '1111'
                char_last = char_first
            else:
                preamble = '1010'
                char_last = char_second
            for i in range(len(ook)):
                if preamble == '1111':
                    if ook[i][2] != char_last:
                        preamble_end = i
                        break
                    else:
                        char_last = ook[i][2]
                else:
                    if ook[i][2] != char_last:
                        char_last = ook[i][2]
                    else:
                        preamble_end = i
                        break

            if len(ook) >= preamble_end:
                preamble_end += int(self.sync_offset) - 1
                self.ss, self.es = ook[0][0], ook[preamble_end][1]
                self.putx([line, ['Preamble', 'Pre', 'P']])
                self.decode_pos += preamble_end

                if len(ook) > self.decode_pos + int(self.sync_length):
                    self.ss = self.es
                    self.es = ook[self.decode_pos + int(self.sync_length)][1]
                    self.putx([line, ['Sync', 'Syn', 'S']])
                    self.decode_pos += int(self.sync_length) + 1

                ookstring = self.ookstring[self.decode_pos:]
                rem_nibbles = len(ookstring) // bits
                for i in range(rem_nibbles): # Display the rest of nibbles.
                    self.ss = ook[self.decode_pos][0]
                    self.es = ook[self.decode_pos + bits - 1][1]
                    self.put_field(bits, line)

    def put_field(self, numbits, line):
        param = self.ookstring[self.decode_pos:self.decode_pos + numbits]
        if 'rev' in self.displayas:
            param = param[::-1]     # Reversed from right.
        if not 'E' in param:        # Format if no errors.
            if 'Hex' in self.displayas:
                param = hex(int(param, 2))[2:]
            elif 'BCD' in self.displayas:
                param = bcd2int(int(param, 2))
        self.putx([line, [str(param)]])
        self.decode_pos += numbits

    def display_all(self):
        ookstring = ''
        self.decode_pos = 0
        ook = self.decoded
        for i in range(len(ook)):
            self.ookstring += ook[i][2]
        bits = 4 if 'Nibble' in self.displayas else 8
        rem_nibbles = len(self.ookstring) // bits
        for i in range(rem_nibbles): # Display the rest of the nibbles.
            self.ss = ook[self.decode_pos][0]
            self.es = ook[self.decode_pos + bits - 1][1]
            self.put_field(bits, 2)

        self.display_level2(bits, 4) # Display L2 decode.

        if (self.ref != 'off' and self.ref != 'show numbers' and
            len(self.ookcache) >= int(self.ref)): # Compare traces.
            ref = int(self.ref) - 1
            self.display_ref(self.trace_num, ref)
            if len(self.ookcache) == int(self.ref): # Backfill.
                for i in range(0, ref):
                    self.display_ref(i, ref)
        elif self.ref == 'show numbers': # Display ref numbers.
            self.ss = self.ookcache[self.trace_num][0][0]
            end_sig = len(self.ookcache[self.trace_num]) - 1
            self.es = self.ookcache[self.trace_num][end_sig][1]
            self.putx([1, [str(self.trace_num + 1)]])

    def display_ref(self, t_num, ref):
        display_len = len(self.ookcache[ref])
        if len(self.ookcache[t_num]) < len(self.ookcache[ref]):
            display_len = len(self.ookcache[t_num])
        for i in range(display_len):
            self.ss = self.ookcache[t_num][i][0]
            self.es = self.ookcache[t_num][i][1]
            self.putx([1, [self.ookcache[ref][i][2]]])

    def add_to_cache(self): # Cache the OOK so it can be used as a reference.
        self.ookcache.append(self.decoded)

    def decode(self, ss, es, data):
        self.decoded = data
        self.add_to_cache()
        self.display_all()
        self.ookstring = ''
        self.trace_num += 1
        self.ss = ss
        self.es = es
        self.putp(data) # Send data up the stack.
