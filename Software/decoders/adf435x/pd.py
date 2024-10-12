##
## This file is part of the libsigrokdecode project.
##
## Copyright (C) 2017 Joel Holdsworth <joel@airwebreathe.org.uk>
##
## This program is free software; you can redistribute it and/or modify
## it under the terms of the GNU General Public License as published by
## the Free Software Foundation; either version 3 of the License, or
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
from common.srdhelper import bitpack_lsb

def disabled_enabled(v):
    return ['Disabled', 'Enabled'][v]

def output_power(v):
    return '{:+d}dBm'.format([-4, -1, 2, 5][v])

# Notes on the implementation:
# - A register's description is an iterable of tuples which contain:
#   The starting bit position, the bit count, the name of a field, and
#   an optional parser which interprets the field's content. Parser are
#   expected to yield a single text string when they exist. Other types
#   of output are passed to Python's .format() routine as is.
# - Bit fields' width in registers determines the range of indices in
#   table/tuple lookups. Keep the implementation as robust as possible
#   during future maintenance. Avoid Python runtime errors when adjusting
#   the decoder.
regs = {
    # Register description fields:
    # offset, width, name, parser.
    0: (
        ( 3, 12, 'FRAC'),
        (15, 16, 'INT',
            None, lambda v: 'Not Allowed' if v < 23 else None,
        ),
    ),
    1: (
        ( 3, 12, 'MOD'),
        (15, 12, 'Phase'),
        (27,  1, 'Prescalar', lambda v: ('4/5', '8/9',)[v]),
        (28,  1, 'Phase Adjust', lambda v: ('Off', 'On',)[v]),
    ),
    2: (
        ( 3,  1, 'Counter Reset', disabled_enabled),
        ( 4,  1, 'Charge Pump Three-State', disabled_enabled),
        ( 5,  1, 'Power-Down', disabled_enabled),
        ( 6,  1, 'PD Polarity', lambda v: ('Negative', 'Positive',)[v]),
        ( 7,  1, 'LDP', lambda v: ('10ns', '6ns',)[v]),
        ( 8,  1, 'LDF', lambda v: ('FRAC-N', 'INT-N',)[v]),
        ( 9,  4, 'Charge Pump Current Setting',
            lambda v: '{curr:0.2f}mA @ 5.1kΩ'.format(curr = (
                0.31, 0.63, 0.94, 1.25, 1.56, 1.88, 2.19, 2.50,
                2.81, 3.13, 3.44, 3.75, 4.06, 4.38, 4.69, 5.00,
            )[v])),
        (13,  1, 'Double Buffer', disabled_enabled),
        (14, 10, 'R Counter'),
        (24,  1, 'RDIV2', disabled_enabled),
        (25,  1, 'Reference Doubler', disabled_enabled),
        (26,  3, 'MUXOUT',
            lambda v: '{text}'.format(text = (
                'Three-State Output', 'DVdd', 'DGND',
                'R Counter Output', 'N Divider Output',
                'Analog Lock Detect', 'Digital Lock Detect',
                'Reserved',
            )[v])),
        (29,  2, 'Low Noise and Low Spur Modes',
            lambda v: '{text}'.format(text = (
                'Low Noise Mode', 'Reserved', 'Reserved', 'Low Spur Mode',
            )[v])),
    ),
    3: (
        ( 3, 12, 'Clock Divider'),
        (15,  2, 'Clock Divider Mode',
            lambda v: '{text}'.format(text = (
                'Clock Divider Off', 'Fast Lock Enable',
                'Resync Enable', 'Reserved',
            )[v])),
        (18,  1, 'CSR Enable', disabled_enabled),
        (21,  1, 'Charge Cancellation', disabled_enabled),
        (22,  1, 'ABP', lambda v: ('6ns (FRAC-N)', '3ns (INT-N)',)[v]),
        (23,  1, 'Band Select Clock Mode', lambda v: ('Low', 'High',)[v]),
    ),
    4: (
        ( 3,  2, 'Output Power', output_power),
        ( 5,  1, 'Output Enable', disabled_enabled),
        ( 6,  2, 'AUX Output Power', output_power),
        ( 8,  1, 'AUX Output Select',
            lambda v: ('Divided Output', 'Fundamental',)[v]),
        ( 9,  1, 'AUX Output Enable', disabled_enabled),
        (10,  1, 'MTLD', disabled_enabled),
        (11,  1, 'VCO Power-Down',
            lambda v: 'VCO Powered {ud}'.format(ud = 'Down' if v else 'Up')),
        (12,  8, 'Band Select Clock Divider'),
        (20,  3, 'RF Divider Select', lambda v: '÷{:d}'.format(2 ** v)),
        (23,  1, 'Feedback Select', lambda v: ('Divided', 'Fundamental',)[v]),
    ),
    5: (
        (22,  2, 'LD Pin Mode',
            lambda v: '{text}'.format(text = (
                'Low', 'Digital Lock Detect', 'Low', 'High',
            )[v])),
    ),
}

( ANN_REG, ANN_WARN, ) = range(2)

class Decoder(srd.Decoder):
    api_version = 3
    id = 'adf435x'
    name = 'ADF435x'
    longname = 'Analog Devices ADF4350/1'
    desc = 'Wideband synthesizer with integrated VCO.'
    license = 'gplv3+'
    inputs = ['spi']
    outputs = []
    tags = ['Clock/timing', 'IC', 'Wireless/RF']
    annotations = (
        # Sent from the host to the chip.
        ('write', 'Register write'),
        ('warning', "Warnings"),
    )
    annotation_rows = (
        ('writes', 'Register writes', (ANN_REG,)),
        ('warnings', 'Warnings', (ANN_WARN,)),
    )

    def __init__(self):
        self.reset()

    def reset(self):
        self.bits = []

    def start(self):
        self.out_ann = self.register(srd.OUTPUT_ANN)

    def putg(self, ss, es, cls, data):
        self.put(ss, es, self.out_ann, [ cls, data, ])

    def decode_bits(self, offset, width):
        '''Extract a bit field. Expects LSB input data.'''
        bits = self.bits[offset:][:width]
        ss, es = bits[-1][1], bits[0][2]
        value = bitpack_lsb(bits, 0)
        return ( value, ( ss, es, ))

    def decode_field(self, name, offset, width, parser = None, checker = None):
        '''Interpret a bit field. Emits an annotation.'''
        # Get the register field's content and position.
        val, ( ss, es, ) = self.decode_bits(offset, width)
        # Have the field's content formatted, emit an annotation.
        formatted = parser(val) if parser else '{}'.format(val)
        if formatted is not None:
            text = ['{name}: {val}'.format(name = name, val = formatted)]
        else:
            text = ['{name}'.format(name = name)]
        if text:
            self.putg(ss, es, ANN_REG, text)
        # Have the field's content checked, emit an optional warning.
        warn = checker(val) if checker else None
        if warn:
            text = ['{}'.format(warn)]
            self.putg(ss, es, ANN_WARN, text)

    def decode_word(self, ss, es, bits):
        '''Interpret a 32bit word after accumulation completes.'''
        # SPI transfer content must be exactly one 32bit word.
        count = len(self.bits)
        if count != 32:
            text = [
                'Frame error: Bit count: want 32, got {}'.format(count),
                'Frame error: Bit count',
                'Frame error',
            ]
            self.putg(ss, es, ANN_WARN, text)
            return
        # Holding bits in LSB order during interpretation simplifies
        # bit field extraction. And annotation emitting routines expect
        # this reverse order of bits' timestamps.
        self.bits.reverse()
        # Determine which register was accessed.
        reg_addr, ( reg_ss, reg_es, ) = self.decode_bits(0, 3)
        text = [
            'Register: {addr}'.format(addr = reg_addr),
            'Reg: {addr}'.format(addr = reg_addr),
            '[{addr}]'.format(addr = reg_addr),
        ]
        self.putg(reg_ss, reg_es, ANN_REG, text)
        # Interpret the register's content (when parsers are available).
        field_descs = regs.get(reg_addr, None)
        if not field_descs:
            return
        for field_desc in field_descs:
            parser = None
            checker = None
            if len(field_desc) == 3:
                start, count, name, = field_desc
            elif len(field_desc) == 4:
                start, count, name, parser = field_desc
            elif len(field_desc) == 5:
                start, count, name, parser, checker = field_desc
            else:
                # Unsupported regs{} syntax, programmer's error.
                return
            self.decode_field(name, start, count, parser, checker)

    def decode(self, ss, es, data):
        ptype, _, _ = data

        if ptype == 'TRANSFER':
            # Process accumulated bits after completion of a transfer.
            self.decode_word(ss, es, self.bits)
            self.bits.clear()

        if ptype == 'BITS':
            _, mosi_bits, miso_bits = data
            # Accumulate bits in MSB order as they are seen in SPI frames.
            msb_bits = mosi_bits.copy()
            msb_bits.reverse()
            self.bits.extend(msb_bits)
