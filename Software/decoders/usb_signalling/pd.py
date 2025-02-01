##
## This file is part of the libsigrokdecode project.
##
## Copyright (C) 2011 Gareth McMullin <gareth@blacksphere.co.nz>
## Copyright (C) 2012-2020 Uwe Hermann <uwe@hermann-uwe.de>
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
from common.srdhelper import SrdIntEnum

'''
OUTPUT_PYTHON format:

Packet:
[<ptype>, <pdata>]

<ptype>, <pdata>:
 - 'SOP', None
 - 'SYM', <sym>
 - 'BIT', <bit>
 - 'STUFF BIT', None
 - 'EOP', None
 - 'ERR', None
 - 'KEEP ALIVE', None
 - 'RESET', None

<sym>:
 - 'J', 'K', 'SE0', or 'SE1'

<bit>:
 - '0' or '1'
 - Note: Symbols like SE0, SE1, and the J that's part of EOP don't yield 'BIT'.
'''

# Low-/full-speed symbols.
# Note: Low-speed J and K are inverted compared to the full-speed J and K!
symbols = {
    'low-speed': {
        # (<dp>, <dm>): <symbol/state>
        (0, 0): 'SE0',
        (1, 0): 'K',
        (0, 1): 'J',
        (1, 1): 'SE1',
    },
    'full-speed': {
        # (<dp>, <dm>): <symbol/state>
        (0, 0): 'SE0',
        (1, 0): 'J',
        (0, 1): 'K',
        (1, 1): 'SE1',
    },
    'automatic': {
        # (<dp>, <dm>): <symbol/state>
        (0, 0): 'SE0',
        (1, 0): 'FS_J',
        (0, 1): 'LS_J',
        (1, 1): 'SE1',
    },
    # After a PREamble PID, the bus segment between Host and Hub uses LS
    # signalling rate and FS signalling polarity (USB 2.0 spec, 11.8.4: "For
    # both upstream and downstream low-speed data, the hub is responsible for
    # inverting the polarity of the data before transmitting to/from a
    # low-speed port.").
    'low-speed-rp': {
        # (<dp>, <dm>): <symbol/state>
        (0, 0): 'SE0',
        (1, 0): 'J',
        (0, 1): 'K',
        (1, 1): 'SE1',
    },
}

bitrates = {
    'low-speed': 1500000, # 1.5Mb/s (+/- 1.5%)
    'low-speed-rp': 1500000, # 1.5Mb/s (+/- 1.5%)
    'full-speed': 12000000, # 12Mb/s (+/- 0.25%)
    'automatic': None
}

sym_annotation = {
    'J': [0, ['J']],
    'K': [1, ['K']],
    'SE0': [2, ['SE0', '0']],
    'SE1': [3, ['SE1', '1']],
}

St = SrdIntEnum.from_str('St', 'IDLE GET_BIT GET_EOP WAIT_IDLE')

class SamplerateError(Exception):
    pass

class Decoder(srd.Decoder):
    api_version = 3
    id = 'usb_signalling'
    name = 'USB signalling'
    longname = 'Universal Serial Bus (LS/FS) signalling'
    desc = 'USB (low-speed/full-speed) signalling protocol.'
    license = 'gplv2+'
    inputs = ['logic']
    outputs = ['usb_signalling']
    tags = ['PC']
    channels = (
        {'id': 'dp', 'name': 'D+', 'desc': 'USB D+ signal'},
        {'id': 'dm', 'name': 'D-', 'desc': 'USB D- signal'},
    )
    options = (
        {'id': 'signalling', 'desc': 'Signalling',
            'default': 'automatic', 'values': ('automatic', 'full-speed', 'low-speed')},
    )
    annotations = (
        ('sym-j', 'J symbol'),
        ('sym-k', 'K symbol'),
        ('sym-se0', 'SE0 symbol'),
        ('sym-se1', 'SE1 symbol'),
        ('sop', 'Start of packet (SOP)'),
        ('eop', 'End of packet (EOP)'),
        ('bit', 'Bit'),
        ('stuffbit', 'Stuff bit'),
        ('error', 'Error'),
        ('keep-alive', 'Low-speed keep-alive'),
        ('reset', 'Reset'),
    )
    annotation_rows = (
        ('bits', 'Bits', (4, 5, 6, 7, 8, 9, 10)),
        ('symbols', 'Symbols', (0, 1, 2, 3)),
    )

    def __init__(self):
        self.reset()

    def reset(self):
        self.samplerate = None
        self.oldsym = 'J' # The "idle" state is J.
        self.ss_block = None
        self.bitrate = None
        self.bitwidth = None
        self.samplepos = None
        self.samplenum_target = None
        self.samplenum_edge = None
        self.samplenum_lastedge = 0
        self.edgepins = None
        self.consecutive_ones = 0
        self.bits = None
        self.state = St.IDLE

    def start(self):
        self.out_python = self.register(srd.OUTPUT_PYTHON)
        self.out_ann = self.register(srd.OUTPUT_ANN)

    def metadata(self, key, value):
        if key == srd.SRD_CONF_SAMPLERATE:
            self.samplerate = value
            self.signalling = self.options['signalling']
            if self.signalling != 'automatic':
                self.update_bitrate()

    def update_bitrate(self):
        self.bitrate = bitrates[self.signalling]
        self.bitwidth = float(self.samplerate) / float(self.bitrate)

    def putpx(self, data):
        s = self.samplenum_edge
        self.put(s, s, self.out_python, data)

    def putx(self, data):
        s = self.samplenum_edge
        self.put(s, s, self.out_ann, data)

    def putpm(self, data):
        e = self.samplenum_edge
        self.put(self.ss_block, e, self.out_python, data)

    def putm(self, data):
        e = self.samplenum_edge
        self.put(self.ss_block, e, self.out_ann, data)

    def putpb(self, data):
        s, e = self.samplenum_lastedge, self.samplenum_edge
        self.put(s, e, self.out_python, data)

    def putb(self, data):
        s, e = self.samplenum_lastedge, self.samplenum_edge
        self.put(s, e, self.out_ann, data)

    def set_new_target_samplenum(self):
        self.samplepos += self.bitwidth
        self.samplenum_target = int(self.samplepos)
        self.samplenum_lastedge = self.samplenum_edge
        self.samplenum_edge = int(self.samplepos - (self.bitwidth / 2))

    def wait_for_sop(self, sym):
        # Wait for a Start of Packet (SOP), i.e. a J->K symbol change.
        if sym != 'K' or self.oldsym != 'J':
            return
        self.consecutive_ones = 0
        self.bits = ''
        self.update_bitrate()
        self.samplepos = self.samplenum - (self.bitwidth / 2) + 0.5
        self.set_new_target_samplenum()
        self.putpx(['SOP', None])
        self.putx([4, ['SOP', 'S']])
        self.state = St.GET_BIT

    def handle_bit(self, b):
        if self.consecutive_ones == 6:
            if b == '0':
                # Stuff bit.
                self.putpb(['STUFF BIT', None])
                self.putb([7, ['Stuff bit: 0', 'SB: 0', '0']])
                self.consecutive_ones = 0
            else:
                self.putpb(['ERR', None])
                self.putb([8, ['Bit stuff error', 'BS ERR', 'B']])
                self.state = St.IDLE
        else:
            # Normal bit (not a stuff bit).
            self.putpb(['BIT', b])
            self.putb([6, ['%s' % b]])
            if b == '1':
                self.consecutive_ones += 1
            else:
                self.consecutive_ones = 0

    def get_eop(self, sym):
        # EOP: SE0 for >= 1 bittime (usually 2 bittimes), then J.
        self.set_new_target_samplenum()
        self.putpb(['SYM', sym])
        self.putb(sym_annotation[sym])
        self.oldsym = sym
        if sym == 'SE0':
            pass
        elif sym == 'J':
            # Got an EOP.
            self.putpm(['EOP', None])
            self.putm([5, ['EOP', 'E']])
            self.state = St.WAIT_IDLE
        else:
            self.putpm(['ERR', None])
            self.putm([8, ['EOP Error', 'EErr', 'E']])
            self.state = St.IDLE

    def get_bit(self, sym):
        self.set_new_target_samplenum()
        b = '0' if self.oldsym != sym else '1'
        self.oldsym = sym
        if sym == 'SE0':
            # Start of an EOP. Change state, save edge
            self.state = St.GET_EOP
            self.ss_block = self.samplenum_lastedge
        else:
            self.handle_bit(b)
        self.putpb(['SYM', sym])
        self.putb(sym_annotation[sym])
        if len(self.bits) <= 16:
            self.bits += b
        if len(self.bits) == 16 and self.bits == '0000000100111100':
            # Sync and low-speed PREamble seen
            self.putpx(['EOP', None])
            self.state = St.IDLE
            self.signalling = 'low-speed-rp'
            self.update_bitrate()
            self.oldsym = 'J'
        if b == '0':
            edgesym = symbols[self.signalling][tuple(self.edgepins)]
            if edgesym not in ('SE0', 'SE1'):
                if edgesym == sym:
                    self.bitwidth = self.bitwidth - (0.001 * self.bitwidth)
                    self.samplepos = self.samplepos - (0.01 * self.bitwidth)
                else:
                    self.bitwidth = self.bitwidth + (0.001 * self.bitwidth)
                    self.samplepos = self.samplepos + (0.01 * self.bitwidth)

    def handle_idle(self, sym):
        self.samplenum_edge = self.samplenum
        se0_length = float(self.samplenum - self.samplenum_lastedge) / self.samplerate
        if se0_length > 2.5e-6: # 2.5us
            self.putpb(['RESET', None])
            self.putb([10, ['Reset', 'Res', 'R']])
            self.signalling = self.options['signalling']
        elif se0_length > 1.2e-6 and self.signalling == 'low-speed':
            self.putpb(['KEEP ALIVE', None])
            self.putb([9, ['Keep-alive', 'KA', 'A']])

        if sym == 'FS_J':
            self.signalling = 'full-speed'
            self.update_bitrate()
        elif sym == 'LS_J':
            self.signalling = 'low-speed'
            self.update_bitrate()
        self.oldsym = 'J'
        self.state = St.IDLE

    def decode(self):
        if not self.samplerate:
            raise SamplerateError('Cannot decode without samplerate.')

        # Seed internal state from the very first sample.
        pins = self.wait()
        sym = symbols[self.options['signalling']][pins]
        self.handle_idle(sym)

        while True:
            # State machine.
            if self.state == St.IDLE:
                # Wait for any edge on either DP and/or DM.
                pins = self.wait([{0: 'e'}, {1: 'e'}])
                sym = symbols[self.signalling][pins]
                if sym == 'SE0':
                    self.samplenum_lastedge = self.samplenum
                    self.state = St.WAIT_IDLE
                else:
                    self.wait_for_sop(sym)
                self.edgepins = pins
            elif self.state in (St.GET_BIT, St.GET_EOP):
                # Wait until we're in the middle of the desired bit.
                self.edgepins = self.wait([{'skip': self.samplenum_edge - self.samplenum}])
                pins = self.wait([{'skip': self.samplenum_target - self.samplenum}])

                sym = symbols[self.signalling][pins]
                if self.state == St.GET_BIT:
                    self.get_bit(sym)
                elif self.state == St.GET_EOP:
                    self.get_eop(sym)
            elif self.state == St.WAIT_IDLE:
                # Skip "all-low" input. Wait for high level on either DP or DM.
                pins = self.wait()
                while not pins[0] and not pins[1]:
                    pins = self.wait([{0: 'h'}, {1: 'h'}])
                if self.samplenum - self.samplenum_lastedge > 1:
                    sym = symbols[self.options['signalling']][pins]
                    self.handle_idle(sym)
                else:
                    sym = symbols[self.signalling][pins]
                    self.wait_for_sop(sym)
                self.edgepins = pins
