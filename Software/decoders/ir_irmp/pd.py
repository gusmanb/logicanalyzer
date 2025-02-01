##
## This file is part of the libsigrokdecode project.
##
## Copyright (C) 2014 Gump Yang <gump.yang@gmail.com>
## Copyright (C) 2019 Rene Staffen
## Copyright (C) 2020-2021 Gerhard Sittig <gerhard.sittig@gmx.net>
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

from . import irmp_library
import sigrokdecode as srd

class SamplerateError(Exception):
    pass

class LibraryError(Exception):
    pass

class Decoder(srd.Decoder):
    api_version = 3
    id = 'ir_irmp'
    name = 'IR IRMP'
    longname = 'IR IRMP'
    desc = 'IRMP infrared remote control multi protocol.'
    license = 'gplv2+'
    inputs = ['logic']
    outputs = []
    tags = ['IR']
    channels = (
        {'id': 'ir', 'name': 'IR', 'desc': 'Data line'},
    )
    options = (
        {'id': 'polarity', 'desc': 'Polarity', 'default': 'active-low',
            'values': ('active-low', 'active-high')},
    )
    annotations = (
        ('packet', 'Packet'),
    )
    annotation_rows = (
        ('packets', 'IR Packets', (0,)),
    )

    def putframe(self, data):
        '''Emit annotation for an IR frame.'''

        # Cache result data fields in local variables. Get the ss/es
        # timestamps, scaled to sample numbers.
        nr = data['proto_nr']
        name = data['proto_name']
        addr = data['address']
        cmd = data['command']
        repeat = data['repeat']
        release = data['release']
        ss = data['start'] * self.rate_factor
        es = data['end'] * self.rate_factor

        # Prepare display texts for several zoom levels.
        # Implementor's note: Keep list lengths for flags aligned during
        # maintenance. Make sure there are as many flags text variants
        # as are referenced by annotation text variants. Differing list
        # lengths or dynamic refs will severely complicate the logic.
        rep_txts = ['repeat', 'rep', 'r']
        rel_txts = ['release', 'rel', 'R']
        flag_txts = [None,] * len(rep_txts)
        for zoom in range(len(flag_txts)):
            flag_txts[zoom] = []
            if repeat:
                flag_txts[zoom].append(rep_txts[zoom])
            if release:
                flag_txts[zoom].append(rel_txts[zoom])
        flag_txts = [' '.join(t) or '-' for t in flag_txts]
        flg = flag_txts # Short name for .format() references.
        txts = [
            'Protocol: {name} ({nr}), Address 0x{addr:04x}, Command: 0x{cmd:04x}, Flags: {flg[0]}'.format(**locals()),
            'P: {name} ({nr}), Addr: 0x{addr:x}, Cmd: 0x{cmd:x}, Flg: {flg[1]}'.format(**locals()),
            'P: {nr} A: 0x{addr:x} C: 0x{cmd:x} F: {flg[1]}'.format(**locals()),
            'C:{cmd:x} A:{addr:x} {flg[2]}'.format(**locals()),
            'C:{cmd:x}'.format(**locals()),
        ]

        # Emit the annotation from details which were constructed above.
        self.put(ss, es, self.out_ann, [0, txts])

    def __init__(self):
        self.irmp = None
        self.reset()

    def reset(self):
        pass

    def start(self):
        self.out_ann = self.register(srd.OUTPUT_ANN)

    def metadata(self, key, value):
        if key == srd.SRD_CONF_SAMPLERATE:
            self.samplerate = value

    def decode(self):
        if not self.irmp:
            try:
                self.irmp = irmp_library.IrmpLibrary()
            except Exception as e:
                txt = e.args[0]
                raise LibraryError(txt)
        if not self.irmp:
            raise LibraryError('Cannot access IRMP library.')
        if not self.samplerate:
            raise SamplerateError('Cannot decode without samplerate.')
        lib_rate = self.irmp.get_sample_rate()
        if not lib_rate:
            raise LibraryError('Cannot determine IRMP library\'s samplerate.')
        if self.samplerate % lib_rate:
            raise SamplerateError('Capture samplerate must be multiple of library samplerate ({})'.format(lib_rate))

        self.rate_factor = int(self.samplerate / lib_rate)
        active = 0 if self.options['polarity'] == 'active-low' else 1

        ir, = self.wait()
        with self.irmp:
            self.irmp.reset_state()
            while True:
                if active == 1:
                    ir = 1 - ir
                if self.irmp.add_one_sample(ir):
                    data = self.irmp.get_result_data()
                    self.putframe(data)
                ir, = self.wait([{'skip': self.rate_factor}])
