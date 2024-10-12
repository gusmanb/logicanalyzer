##
## This file is part of the libsigrokdecode project.
##
## Copyright (C) 2014 Gump Yang <gump.yang@gmail.com>
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

from common.srdhelper import bitpack
from .lists import *
import sigrokdecode as srd

# Concentrate all timing constraints of the IR protocol here in a single
# location at the top of the source, to raise awareness and to simplify
# review and adjustment. The tolerance is an arbitrary choice, available
# literature does not mention any. The inter-frame timeout is not a part
# of the protocol, but an implementation detail of this sigrok decoder.
_TIME_TOL  =  8     # tolerance, in percent
_TIME_IDLE = 20.0   # inter-frame timeout, in ms
_TIME_LC   = 13.5   # leader code, in ms
_TIME_RC   = 11.25  # repeat code, in ms
_TIME_ONE  =  2.25  # one data bit, in ms
_TIME_ZERO =  1.125 # zero data bit, in ms
_TIME_STOP =  0.562 # stop bit, in ms

class SamplerateError(Exception):
    pass

class Pin:
    IR, = range(1)

class Ann:
    BIT, AGC, LONG_PAUSE, SHORT_PAUSE, STOP_BIT, \
    LEADER_CODE, ADDR, ADDR_INV, CMD, CMD_INV, REPEAT_CODE, \
    REMOTE, WARN = range(13)

class Decoder(srd.Decoder):
    api_version = 3
    id = 'ir_nec'
    name = 'IR NEC'
    longname = 'IR NEC'
    desc = 'NEC infrared remote control protocol.'
    license = 'gplv2+'
    inputs = ['logic']
    outputs = []
    tags = ['IR']
    channels = (
        {'id': 'ir', 'name': 'IR', 'desc': 'Data line'},
    )
    options = (
        {'id': 'polarity', 'desc': 'Polarity', 'default': 'active-low',
            'values': ('auto', 'active-low', 'active-high')},
        {'id': 'cd_freq', 'desc': 'Carrier Frequency', 'default': 0},
        {'id': 'extended', 'desc': 'Extended NEC Protocol',
            'default': 'no', 'values': ('yes', 'no')},
    )
    annotations = (
        ('bit', 'Bit'),
        ('agc-pulse', 'AGC pulse'),
        ('longpause', 'Long pause'),
        ('shortpause', 'Short pause'),
        ('stop-bit', 'Stop bit'),
        ('leader-code', 'Leader code'),
        ('addr', 'Address'),
        ('addr-inv', 'Address#'),
        ('cmd', 'Command'),
        ('cmd-inv', 'Command#'),
        ('repeat-code', 'Repeat code'),
        ('remote', 'Remote'),
        ('warning', 'Warning'),
    )
    annotation_rows = (
        ('bits', 'Bits', (Ann.BIT, Ann.AGC, Ann.LONG_PAUSE, Ann.SHORT_PAUSE, Ann.STOP_BIT)),
        ('fields', 'Fields', (Ann.LEADER_CODE, Ann.ADDR, Ann.ADDR_INV, Ann.CMD, Ann.CMD_INV, Ann.REPEAT_CODE)),
        ('remote-vals', 'Remote', (Ann.REMOTE,)),
        ('warnings', 'Warnings', (Ann.WARN,)),
    )

    def putx(self, data):
        self.put(self.ss_start, self.samplenum, self.out_ann, data)

    def putb(self, data):
        self.put(self.ss_bit, self.samplenum, self.out_ann, data)

    def putd(self, data, bit_count):
        name = self.state.title()
        d = {'ADDRESS': Ann.ADDR, 'ADDRESS#': Ann.ADDR_INV,
             'COMMAND': Ann.CMD, 'COMMAND#': Ann.CMD_INV}
        s = {'ADDRESS': ['ADDR', 'A'], 'ADDRESS#': ['ADDR#', 'A#'],
             'COMMAND': ['CMD', 'C'], 'COMMAND#': ['CMD#', 'C#']}
        fmt = '{{}}: 0x{{:0{}X}}'.format(bit_count // 4)
        self.putx([d[self.state], [
            fmt.format(name, data),
            fmt.format(s[self.state][0], data),
            fmt.format(s[self.state][1], data),
            s[self.state][1],
        ]])

    def putstop(self, ss):
        self.put(ss, ss + self.stop, self.out_ann,
                 [Ann.STOP_BIT, ['Stop bit', 'Stop', 'St', 'S']])

    def putpause(self, p):
        self.put(self.ss_start, self.ss_other_edge, self.out_ann,
                 [Ann.AGC, ['AGC pulse', 'AGC', 'A']])
        idx = Ann.LONG_PAUSE if p == 'Long' else Ann.SHORT_PAUSE
        self.put(self.ss_other_edge, self.samplenum, self.out_ann, [idx, [
            '{} pause'.format(p),
            '{}-pause'.format(p[0]),
            '{}P'.format(p[0]),
            'P',
        ]])

    def putremote(self):
        dev = address.get(self.addr, 'Unknown device')
        buttons = command.get(self.addr, {})
        btn = buttons.get(self.cmd, ['Unknown', 'Unk'])
        self.put(self.ss_remote, self.ss_bit + self.stop, self.out_ann, [Ann.REMOTE, [
            '{}: {}'.format(dev, btn[0]),
            '{}: {}'.format(dev, btn[1]),
            '{}'.format(btn[1]),
        ]])

    def __init__(self):
        self.reset()

    def reset(self):
        self.state = 'IDLE'
        self.ss_bit = self.ss_start = self.ss_other_edge = self.ss_remote = 0
        self.data = []
        self.addr = self.cmd = None

    def start(self):
        self.out_ann = self.register(srd.OUTPUT_ANN)

    def metadata(self, key, value):
        if key == srd.SRD_CONF_SAMPLERATE:
            self.samplerate = value

    def calc_rate(self):
        self.tolerance = _TIME_TOL / 100
        self.lc = int(self.samplerate * _TIME_LC / 1000) - 1
        self.rc = int(self.samplerate * _TIME_RC / 1000) - 1
        self.dazero = int(self.samplerate * _TIME_ZERO / 1000) - 1
        self.daone = int(self.samplerate * _TIME_ONE / 1000) - 1
        self.stop = int(self.samplerate * _TIME_STOP / 1000) - 1
        self.idle_to = int(self.samplerate * _TIME_IDLE / 1000) - 1

    def compare_with_tolerance(self, measured, base):
        return (measured >= base * (1 - self.tolerance)
                and measured <= base * (1 + self.tolerance))

    def handle_bit(self, tick):
        ret = None
        if self.compare_with_tolerance(tick, self.dazero):
            ret = 0
        elif self.compare_with_tolerance(tick, self.daone):
            ret = 1
        if ret in (0, 1):
            self.putb([Ann.BIT, ['{:d}'.format(ret)]])
            self.data.append(ret)
        self.ss_bit = self.samplenum

    def data_ok(self, check, want_len):
        name = self.state.title()
        normal, inverted = bitpack(self.data[:8]), bitpack(self.data[8:])
        valid = (normal ^ inverted) == 0xff
        show = inverted if self.state.endswith('#') else normal
        is_ext_addr = self.is_extended and self.state == 'ADDRESS'
        if is_ext_addr:
            normal = bitpack(self.data)
            show = normal
            valid = True
        if len(self.data) == want_len:
            if self.state == 'ADDRESS':
                self.addr = normal
            if self.state == 'COMMAND':
                self.cmd = normal
            self.putd(show, want_len)
            self.ss_start = self.samplenum
            if is_ext_addr:
                self.data = []
                self.ss_bit = self.ss_start = self.samplenum
            return True
        self.putd(show, want_len)
        if check and not valid:
            warn_show = bitpack(self.data)
            self.putx([Ann.WARN, ['{} error: 0x{:04X}'.format(name, warn_show)]])
        self.data = []
        self.ss_bit = self.ss_start = self.samplenum
        return valid

    def decode(self):
        if not self.samplerate:
            raise SamplerateError('Cannot decode without samplerate.')
        self.calc_rate()

        cd_count = None
        if self.options['cd_freq']:
            cd_count = int(self.samplerate / self.options['cd_freq']) + 1
        prev_ir = None

        if self.options['polarity'] == 'auto':
            # Take sample 0 as reference.
            curr_level, = self.wait({'skip': 0})
            active = 1 - curr_level
        else:
            active = 0 if self.options['polarity'] == 'active-low' else 1
        self.is_extended = self.options['extended'] == 'yes'
        want_addr_len = 16 if self.is_extended else 8

        while True:
            # Detect changes in the presence of an active input signal.
            # The decoder can either be fed an already filtered RX signal
            # or optionally can detect the presence of a carrier. Periods
            # of inactivity (signal changes slower than the carrier freq,
            # if specified) pass on the most recently sampled level. This
            # approach works for filtered and unfiltered input alike, and
            # only slightly extends the active phase of input signals with
            # carriers included by one period of the carrier frequency.
            # IR based communication protocols can cope with this slight
            # inaccuracy just fine by design. Enabling carrier detection
            # on already filtered signals will keep the length of their
            # active period, but will shift their signal changes by one
            # carrier period before they get passed to decoding logic.
            if cd_count:
                (cur_ir,) = self.wait([{Pin.IR: 'e'}, {'skip': cd_count}])
                if self.matched[0]:
                    cur_ir = active
                if cur_ir == prev_ir:
                    continue
                prev_ir = cur_ir
                self.ir = cur_ir
            else:
                (self.ir,) = self.wait({Pin.IR: 'e'})

            if self.ir != active:
                # Save the location of the non-active edge (recessive),
                # then wait for the next edge. Immediately process the
                # end of the STOP bit which completes an IR frame.
                self.ss_other_edge = self.samplenum
                if self.state != 'STOP':
                    continue

            # Reset internal state for long periods of idle level.
            width = self.samplenum - self.ss_bit
            if width >= self.idle_to and self.state != 'STOP':
                self.reset()

            # State machine.
            if self.state == 'IDLE':
                if self.compare_with_tolerance(width, self.lc):
                    self.putpause('Long')
                    self.putx([Ann.LEADER_CODE, ['Leader code', 'Leader', 'LC', 'L']])
                    self.ss_remote = self.ss_start
                    self.data = []
                    self.state = 'ADDRESS'
                elif self.compare_with_tolerance(width, self.rc):
                    self.putpause('Short')
                    self.putstop(self.samplenum)
                    self.samplenum += self.stop
                    self.putx([Ann.REPEAT_CODE, ['Repeat code', 'Repeat', 'RC', 'R']])
                    self.data = []
                self.ss_bit = self.ss_start = self.samplenum
            elif self.state == 'ADDRESS':
                self.handle_bit(width)
                if len(self.data) == want_addr_len:
                    self.data_ok(False, want_addr_len)
                    self.state = 'COMMAND' if self.is_extended else 'ADDRESS#'
            elif self.state == 'ADDRESS#':
                self.handle_bit(width)
                if len(self.data) == 16:
                    self.data_ok(True, 8)
                    self.state = 'COMMAND'
            elif self.state == 'COMMAND':
                self.handle_bit(width)
                if len(self.data) == 8:
                    self.data_ok(False, 8)
                    self.state = 'COMMAND#'
            elif self.state == 'COMMAND#':
                self.handle_bit(width)
                if len(self.data) == 16:
                    self.data_ok(True, 8)
                    self.state = 'STOP'
            elif self.state == 'STOP':
                self.putstop(self.ss_bit)
                self.putremote()
                self.ss_bit = self.ss_start = self.samplenum
                self.state = 'IDLE'
