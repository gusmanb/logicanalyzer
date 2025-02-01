##
## This file is part of the libsigrokdecode project.
##
## Copyright (C) 2019 Comlab AG
## Copyright (C) 2020 Gerhard Sittig <gerhard.sittig@gmx.net>
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

# This implementation started as a "vector slicer", then turned into the
# "numbers and states" decoder, because users always had the freedom to
# connect any logic signal to either of the decoder inputs. That's when
# slicing vectors took second seat, and just was not needed any longer
# in the strict sense.
#
# TODO
# - Find an appropriate number of input channels, and maximum enum slots.
# - Re-check correctness of signed integers. Signed fixed point is based
#   on integers and transparently benefits from fixes and improvements.
# - Local formatting in individual decoders becomes obsolete when common
#   support for user selected formatting gets introduced.
# - There is overlap with the 'parallel' decoder. Ideally the numbers
#   decoder could stack on top of parallel, but parallel currently is
#   severely limited in its number of input channels, and dramatically
#   widening the parallel decoder may be undesirable.

from common.srdhelper import bitpack
import json
import sigrokdecode as srd
import struct

'''
OUTPUT_PYTHON format:

Packet:
[<ptype>, <pdata>]

This is a list of <ptype>s and their respective <pdata> values:
 - 'RAW': The data is a tuple of bit count and bit pattern (a number,
   assuming unsigned integer presentation of the input data bit pattern).
 - 'NUMBER': The data is the conversion result of the bit pattern.
 - 'ENUM': The data is a tuple of the raw number and its mapped text.
'''

# TODO Better raise the number of channels to 32. This allows access to
# IEEE754 single precision numbers, and shall cover most busses, _and_
# remains within most logic analyzers' capabilities, and keeps the UI
# dialog somewhat managable. What's a good default for the number of
# enum slots (which translate to annotation rows)? Notice that 2 to the
# power of the channel count is way out of the question. :)
_max_channels = 16
_max_enum_slots = 32

class ChannelError(Exception):
    pass

class Pin:
    CLK, BIT_0 = range(2)
    BIT_N = BIT_0 + _max_channels

class Ann:
    RAW, NUM = range(2)
    ENUM_0 = NUM + 1
    ENUM_OVR = ENUM_0 + _max_enum_slots
    ENUMS = range(ENUM_0, ENUM_OVR)
    WARN = ENUM_OVR + 1

    @staticmethod
    def enum_indices():
        return [i for i in range(Ann.ENUMS)]

    @staticmethod
    def get_enum_idx(code):
        if code in range(_max_enum_slots):
            return Ann.ENUM_0 + code
        return Ann.ENUM_OVR

def _channel_decl(count):
    return tuple([
        {'id': 'bit{}'.format(i), 'name': 'Bit{}'.format(i), 'desc': 'Bit position {}'.format(i)}
        for i in range(count)
    ])

def _enum_cls_decl(count):
    return tuple([
        ('enum{}'.format(i), 'Enumeration slot {}'.format(i))
        for i in range(count)
    ] + [('enumovr', 'Enumeration overflow')])

def _enum_rows_decl(count):
    return tuple([
        ('enums{}'.format(i), 'Enumeration slots {}'.format(i), (Ann.ENUM_0 + i,))
        for i in range(count)
    ] + [('enumsovr', 'Enumeration overflows', (Ann.ENUM_OVR,))])

class Decoder(srd.Decoder):
    api_version = 3
    id = 'numbers_and_state'
    name = 'Numbers and State'
    longname = 'Interpret bit patters as numbers or state enums'
    desc = 'Interpret bit patterns as different kinds of numbers (integer, float, enum).'
    license = 'gplv2+'
    inputs = ['logic']
    outputs = ['numbers_and_state']
    tags = ['Encoding', 'Util']
    optional_channels = (
        {'id': 'clk', 'name': 'Clock', 'desc': 'Clock'},
    ) + _channel_decl(_max_channels)
    options = (
        {'id': 'clkedge', 'desc': 'Clock edge', 'default': 'rising',
            'values': ('rising', 'falling', 'either')},
        {'id': 'count', 'desc': 'Total bits count', 'default': 0},
        {'id': 'interp', 'desc': 'Interpretation', 'default': 'unsigned',
            'values': ('unsigned', 'signed', 'fixpoint', 'fixsigned', 'ieee754', 'enum')},
        {'id': 'fracbits', 'desc': 'Fraction bits count', 'default': 0},
        {'id': 'mapping', 'desc': 'Enum to text map file',
            'default': 'enumtext.json'},
        {'id': 'format', 'desc': 'Number format', 'default': '-',
            'values': ('-', 'bin', 'oct', 'dec', 'hex')},
    )
    annotations = (
        ('raw', 'Raw pattern'),
        ('number', 'Number'),
    ) + _enum_cls_decl(_max_enum_slots) + (
        ('warning', 'Warning'),
    )
    annotation_rows = (
        ('raws', 'Raw bits', (Ann.RAW,)),
        ('numbers', 'Numbers', (Ann.NUM,)),
    ) + _enum_rows_decl(_max_enum_slots) + (
        ('warnings', 'Warnings', (Ann.WARN,)),
    )

    def __init__(self):
        self.reset()

    def reset(self):
        pass

    def start(self):
        self.out_ann = self.register(srd.OUTPUT_ANN)
        self.out_python = self.register(srd.OUTPUT_PYTHON)

    def putg(self, ss, es, cls, data):
        self.put(ss, es, self.out_ann, [cls, data])

    def putpy(self, ss, es, ptype, pdata):
        self.put(ss, es, self.out_python, (ptype, pdata))

    def grab_pattern(self, pins):
        '''Get a bit pattern from potentially incomplete probes' values.'''

        # Pad and trim the input data, to achieve the user specified
        # total number of bits. Map all unassigned signals to 0 (low).
        # Return raw number (unsigned integer interpreation).
        bits = pins + (None,) * self.bitcount
        bits = bits[:self.bitcount]
        bits = [b if b in (0, 1) else 0 for b in bits]
        pattern = bitpack(bits)
        return pattern

    def handle_pattern(self, ss, es, pattern):
        fmt = '{{:0{}b}}'.format(self.bitcount)
        txt = fmt.format(pattern)
        self.putg(ss, es, Ann.RAW, [txt])
        self.putpy(ss, es, 'RAW', (self.bitcount, pattern))

        try:
            value = self.interpreter(ss, es, pattern)
        except:
            value = None
        if value is None:
            return
        self.putpy(ss, es, 'NUMBER', value)
        try:
            formatted = self.formatter(ss, es, value)
        except:
            formatted = None
        if formatted:
            self.putg(ss, es, Ann.NUM, formatted)
            if self.interpreter == self.interp_enum:
                cls = Ann.get_enum_idx(pattern)
                self.putg(ss, es, cls, formatted)
                self.putpy(ss, es, 'ENUM', (value, formatted))

    def interp_unsigned(self, ss, es, pattern):
        value = pattern
        return value

    def interp_signed(self, ss, es, pattern):
        if not 'signmask' in self.interp_state:
            self.interp_state.update({
                'signmask': 1 << (self.bitcount - 1),
                'signfull': 1 << self.bitcount,
            })
        is_neg = pattern & self.interp_state['signmask']
        if is_neg:
            value = -(self.interp_state['signfull'] - pattern)
        else:
            value = pattern
        return value

    def interp_fixpoint(self, ss, es, pattern):
        if not 'fixdiv' in self.interp_state:
            self.interp_state.update({
                'fixsign': self.options['interp'] == 'fixsigned',
                'fixdiv': 2 ** self.options['fracbits'],
            })
        if self.interp_state['fixsign']:
            value = self.interp_signed(ss, es, pattern)
        else:
            value = self.interp_unsigned(ss, es, pattern)
        value /= self.interp_state['fixdiv']
        return value

    def interp_ieee754(self, ss, es, pattern):
        if not 'ieee_has_16bit' in self.interp_state:
            self.interp_state.update({
                'ieee_fmt_int_16': '=H',
                'ieee_fmt_flt_16': '=e',
                'ieee_fmt_int_32': '=L',
                'ieee_fmt_flt_32': '=f',
                'ieee_fmt_int_64': '=Q',
                'ieee_fmt_flt_64': '=d',
            })
            try:
                fmt = self.interp_state.update['ieee_fmt_flt_16']
                has_16bit_support = 8 * struct.calcsize(fmt) == 16
            except:
                has_16bit_support = False
            self.interp_state['ieee_has_16bit'] = has_16bit_support
        if self.bitcount == 16:
            if not self.interp_state['ieee_has_16bit']:
                return None
            buff = struct.pack(self.interp_state['ieee_fmt_int_16'], pattern)
            value, = struct.unpack(self.interp_state['ieee_fmt_flt_16'], buff)
            return value
        if self.bitcount == 32:
            buff = struct.pack(self.interp_state['ieee_fmt_int_32'], pattern)
            value, = struct.unpack(self.interp_state['ieee_fmt_flt_32'], buff)
            return value
        if self.bitcount == 64:
            buff = struct.pack(self.interp_state['ieee_fmt_int_64'], pattern)
            value, = struct.unpack(self.interp_state['ieee_fmt_flt_64'], buff)
            return value
        return None

    def interp_enum(self, ss, es, pattern):
        if not 'enum_map' in self.interp_state:
            self.interp_state.update({
                'enum_fn': self.options['mapping'],
                'enum_map': {},
                'enum_have_map': False,
            })
            try:
                fn = self.interp_state['enum_fn']
                # TODO Optionally try in several locations? Next to the
                # decoder implementation? Where else? Expect users to
                # enter absolute paths?
                with open(fn, 'r') as f:
                    maptext = f.read()
                maptable = {}
                if fn.endswith('.js') or fn.endswith('.json'):
                    # JSON requires string literals on the LHS, so the
                    # table is written "in reverse order".
                    js_table = json.loads(maptext)
                    for k, v in js_table.items():
                        maptable[v] = k
                elif fn.endswith('.py'):
                    # Expect a specific identifier at the Python module
                    # level, and assume that it's a dictionary.
                    py_table = {}
                    exec(maptext, py_table)
                    maptable.update(py_table['enumtext'])
                self.interp_state['enum_map'].update(maptable)
                self.interp_state['enum_have_map'] = True
            except:
                # Silently ignore failure. This happens while the user
                # is typing the filename, and is non-fatal. If the file
                # exists and is not readable or not valid or of unknown
                # format, the worst thing that can happen is that the
                # decoder implementation keeps using "anonymous" phrases
                # until a mapping has become available. No harm is done.
                # This decoder cannot tell intermediate from final file
                # read attempts, so we cannot raise severity here.
                pass
        value = self.interp_state['enum_map'].get(pattern, None)
        if value is None:
            value = pattern
        return value

    def format_native(self, ss, es, value):
        return ['{}'.format(value),]

    def format_bin(self, ss, es, value):
        if not self.format_string:
            self.format_string = '{{:0{}b}}'.format(self.bitcount)
        return [self.format_string.format(value)]

    def format_oct(self, ss, es, value):
        if not self.format_string:
            self.format_string = '{{:0{}o}}'.format((self.bitcount + 3 - 1) // 3)
        return [self.format_string.format(value)]

    def format_dec(self, ss, es, value):
        if not self.format_string:
            self.format_string = '{:d}'
        return [self.format_string.format(value)]

    def format_hex(self, ss, es, value):
        if not self.format_string:
            self.format_string = '{{:0{}x}}'.format((self.bitcount + 4 - 1) // 4)
        return [self.format_string.format(value)]

    def decode(self):
        channels = [ch for ch in range(_max_channels) if self.has_channel(ch)]
        have_clk = Pin.CLK in channels
        if have_clk:
            channels.remove(Pin.CLK)
        if not channels:
            raise ChannelError("Need at least one bit channel.")
        if have_clk:
            clkedge = {
                'rising': 'r',
                'falling': 'f',
                'either': 'e',
            }.get(self.options['clkedge'])
            wait_cond = {Pin.CLK: clkedge}
        else:
            wait_cond = [{ch: 'e'} for ch in channels]

        bitcount = self.options['count']
        if not bitcount:
            bitcount = channels[-1] - Pin.BIT_0 + 1
        self.bitcount = bitcount

        self.interpreter = {
            'unsigned': self.interp_unsigned,
            'signed': self.interp_signed,
            'fixpoint': self.interp_fixpoint,
            'fixsigned': self.interp_fixpoint,
            'ieee754': self.interp_ieee754,
            'enum': self.interp_enum,
        }.get(self.options['interp'])
        self.interp_state = {}
        self.formatter = {
            '-': self.format_native,
            'bin': self.format_bin,
            'oct': self.format_oct,
            'dec': self.format_dec,
            'hex': self.format_hex,
        }.get(self.options['format'])
        self.format_string = None

        pins = self.wait()
        ss = self.samplenum
        prev_pattern = self.grab_pattern(pins[Pin.BIT_0:])
        while True:
            pins = self.wait(wait_cond)
            es = self.samplenum
            pattern = self.grab_pattern(pins[Pin.BIT_0:])
            if pattern == prev_pattern:
                continue
            self.handle_pattern(ss, es, prev_pattern)
            ss = es
            prev_pattern = pattern
