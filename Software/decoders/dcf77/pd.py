##
## This file is part of the libsigrokdecode project.
##
## Copyright (C) 2012-2016 Uwe Hermann <uwe@hermann-uwe.de>
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
import calendar
from common.srdhelper import bcd2int

class SamplerateError(Exception):
    pass

class Decoder(srd.Decoder):
    api_version = 3
    id = 'dcf77'
    name = 'DCF77'
    longname = 'DCF77 time protocol'
    desc = 'European longwave time signal (77.5kHz carrier signal).'
    license = 'gplv2+'
    inputs = ['logic']
    outputs = []
    tags = ['Clock/timing']
    channels = (
        {'id': 'data', 'name': 'DATA', 'desc': 'DATA line'},
    )
    annotations = (
        ('start-of-minute', 'Start of minute'),
        ('special-bit', 'Special bit (civil warnings, weather forecast)'),
        ('call-bit', 'Call bit'),
        ('summer-time', 'Summer time announcement'),
        ('cest', 'CEST bit'),
        ('cet', 'CET bit'),
        ('leap-second', 'Leap second bit'),
        ('start-of-time', 'Start of encoded time'),
        ('minute', 'Minute'),
        ('minute-parity', 'Minute parity bit'),
        ('hour', 'Hour'),
        ('hour-parity', 'Hour parity bit'),
        ('day', 'Day of month'),
        ('day-of-week', 'Day of week'),
        ('month', 'Month'),
        ('year', 'Year'),
        ('date-parity', 'Date parity bit'),
        ('raw-bit', 'Raw bit'),
        ('unknown-bit', 'Unknown bit'),
        ('warning', 'Warning'),
    )
    annotation_rows = (
        ('bits', 'Bits', (17, 18)),
        ('fields', 'Fields', tuple(range(0, 16 + 1))),
        ('warnings', 'Warnings', (19,)),
    )

    def __init__(self):
        self.reset()

    def reset(self):
        self.samplerate = None
        self.state = 'WAIT FOR RISING EDGE'
        self.ss_bit = self.ss_bit_old = self.es_bit = self.ss_block = 0
        self.datebits = []
        self.bitcount = 0 # Counter for the DCF77 bits (0..58)
        self.dcf77_bitnumber_is_known = 0

    def start(self):
        self.out_ann = self.register(srd.OUTPUT_ANN)

    def metadata(self, key, value):
        if key == srd.SRD_CONF_SAMPLERATE:
            self.samplerate = value

    def putx(self, data):
        # Annotation for a single DCF77 bit.
        self.put(self.ss_bit, self.es_bit, self.out_ann, data)

    def putb(self, data):
        # Annotation for a multi-bit DCF77 field.
        self.put(self.ss_block, self.samplenum, self.out_ann, data)

    # TODO: Which range to use? Only the 100ms/200ms or full second?
    def handle_dcf77_bit(self, bit):
        c = self.bitcount

        # Create one annotation for each DCF77 bit (containing the 0/1 value).
        # Use 'Unknown DCF77 bit x: val' if we're not sure yet which of the
        # 0..58 bits it is (because we haven't seen a 'new minute' marker yet).
        # Otherwise, use 'DCF77 bit x: val'.
        s = 'B' if self.dcf77_bitnumber_is_known else 'Unknown b'
        ann = 17 if self.dcf77_bitnumber_is_known else 18
        self.putx([ann, ['%sit %d: %d' % (s, c, bit), '%d' % bit]])

        # If we're not sure yet which of the 0..58 DCF77 bits we have, return.
        # We don't want to decode bogus data.
        if not self.dcf77_bitnumber_is_known:
            return

        # Collect bits 36-58, we'll need them for a parity check later.
        if c in range(36, 58 + 1):
            self.datebits.append(bit)

        # Output specific "decoded" annotations for the respective DCF77 bits.
        if c == 0:
            # Start of minute: DCF bit 0.
            if bit == 0:
                self.putx([0, ['Start of minute (always 0)',
                               'Start of minute', 'SoM']])
            else:
                self.putx([19, ['Start of minute != 0', 'SoM != 0']])
        elif c in range(1, 14 + 1):
            # Special bits (civil warnings, weather forecast): DCF77 bits 1-14.
            if c == 1:
                self.tmp = bit
                self.ss_block = self.ss_bit
            else:
                self.tmp |= (bit << (c - 1))
            if c == 14:
                s = '{:014b}'.format(self.tmp)
                self.putb([1, ['Special bits: %s' % s, 'SB: %s' % s]])
        elif c == 15:
            s = '' if (bit == 1) else 'not '
            self.putx([2, ['Call bit: %sset' % s, 'CB: %sset' % s]])
            # TODO: Previously this bit indicated use of the backup antenna.
        elif c == 16:
            s = '' if (bit == 1) else 'not '
            x = 'yes' if (bit == 1) else 'no'
            self.putx([3, ['Summer time announcement: %sactive' % s,
                           'Summer time: %sactive' % s,
                           'Summer time: %s' % x, 'ST: %s' % x]])
        elif c == 17:
            s = '' if (bit == 1) else 'not '
            x = 'yes' if (bit == 1) else 'no'
            self.putx([4, ['CEST: %sin effect' % s, 'CEST: %s' % x]])
        elif c == 18:
            s = '' if (bit == 1) else 'not '
            x = 'yes' if (bit == 1) else 'no'
            self.putx([5, ['CET: %sin effect' % s, 'CET: %s' % x]])
        elif c == 19:
            s = '' if (bit == 1) else 'not '
            x = 'yes' if (bit == 1) else 'no'
            self.putx([6, ['Leap second announcement: %sactive' % s,
                           'Leap second: %sactive' % s,
                           'Leap second: %s' % x, 'LS: %s' % x]])
        elif c == 20:
            # Start of encoded time: DCF bit 20.
            if bit == 1:
                self.putx([7, ['Start of encoded time (always 1)',
                               'Start of encoded time', 'SoeT']])
            else:
                self.putx([19, ['Start of encoded time != 1', 'SoeT != 1']])
        elif c in range(21, 27 + 1):
            # Minutes (0-59): DCF77 bits 21-27 (BCD format).
            if c == 21:
                self.tmp = bit
                self.ss_block = self.ss_bit
            else:
                self.tmp |= (bit << (c - 21))
            if c == 27:
                m = bcd2int(self.tmp)
                self.putb([8, ['Minutes: %d' % m, 'Min: %d' % m]])
        elif c == 28:
            # Even parity over minute bits (21-28): DCF77 bit 28.
            self.tmp |= (bit << (c - 21))
            parity = bin(self.tmp).count('1')
            s = 'OK' if ((parity % 2) == 0) else 'INVALID!'
            self.putx([9, ['Minute parity: %s' % s, 'Min parity: %s' % s]])
        elif c in range(29, 34 + 1):
            # Hours (0-23): DCF77 bits 29-34 (BCD format).
            if c == 29:
                self.tmp = bit
                self.ss_block = self.ss_bit
            else:
                self.tmp |= (bit << (c - 29))
            if c == 34:
                self.putb([10, ['Hours: %d' % bcd2int(self.tmp)]])
        elif c == 35:
            # Even parity over hour bits (29-35): DCF77 bit 35.
            self.tmp |= (bit << (c - 29))
            parity = bin(self.tmp).count('1')
            s = 'OK' if ((parity % 2) == 0) else 'INVALID!'
            self.putx([11, ['Hour parity: %s' % s]])
        elif c in range(36, 41 + 1):
            # Day of month (1-31): DCF77 bits 36-41 (BCD format).
            if c == 36:
                self.tmp = bit
                self.ss_block = self.ss_bit
            else:
                self.tmp |= (bit << (c - 36))
            if c == 41:
                self.putb([12, ['Day: %d' % bcd2int(self.tmp)]])
        elif c in range(42, 44 + 1):
            # Day of week (1-7): DCF77 bits 42-44 (BCD format).
            # A value of 1 means Monday, 7 means Sunday.
            if c == 42:
                self.tmp = bit
                self.ss_block = self.ss_bit
            else:
                self.tmp |= (bit << (c - 42))
            if c == 44:
                d = bcd2int(self.tmp)
                try:
                    dn = calendar.day_name[d - 1] # day_name[0] == Monday
                    self.putb([13, ['Day of week: %d (%s)' % (d, dn),
                                    'DoW: %d (%s)' % (d, dn)]])
                except IndexError:
                    self.putb([19, ['Day of week: %d (%s)' % (d, 'invalid'),
                                    'DoW: %d (%s)' % (d, 'inv')]])
        elif c in range(45, 49 + 1):
            # Month (1-12): DCF77 bits 45-49 (BCD format).
            if c == 45:
                self.tmp = bit
                self.ss_block = self.ss_bit
            else:
                self.tmp |= (bit << (c - 45))
            if c == 49:
                m = bcd2int(self.tmp)
                try:
                    mn = calendar.month_name[m] # month_name[1] == January
                    self.putb([14, ['Month: %d (%s)' % (m, mn),
                                    'Mon: %d (%s)' % (m, mn)]])
                except IndexError:
                    self.putb([19, ['Month: %d (%s)' % (m, 'invalid'),
                                    'Mon: %d (%s)' % (m, 'inv')]])
        elif c in range(50, 57 + 1):
            # Year (0-99): DCF77 bits 50-57 (BCD format).
            if c == 50:
                self.tmp = bit
                self.ss_block = self.ss_bit
            else:
                self.tmp |= (bit << (c - 50))
            if c == 57:
                self.putb([15, ['Year: %d' % bcd2int(self.tmp)]])
        elif c == 58:
            # Even parity over date bits (36-58): DCF77 bit 58.
            parity = self.datebits.count(1)
            s = 'OK' if ((parity % 2) == 0) else 'INVALID!'
            self.putx([16, ['Date parity: %s' % s, 'DP: %s' % s]])
            self.datebits = []
        else:
            self.putx([19, ['Invalid DCF77 bit: %d' % c,
                            'Invalid bit: %d' % c, 'Inv: %d' % c]])

    def decode(self):
        if not self.samplerate:
            raise SamplerateError('Cannot decode without samplerate.')
        while True:
            if self.state == 'WAIT FOR RISING EDGE':
                # Wait until the next rising edge occurs.
                self.wait({0: 'r'})

                # Save the sample number where the DCF77 bit begins.
                self.ss_bit = self.samplenum

                # Calculate the length (in ms) between two rising edges.
                len_edges = self.ss_bit - self.ss_bit_old
                len_edges_ms = int((len_edges / self.samplerate) * 1000)

                # The time between two rising edges is usually around 1000ms.
                # For DCF77 bit 59, there is no rising edge at all, i.e. the
                # time between DCF77 bit 59 and DCF77 bit 0 (of the next
                # minute) is around 2000ms. Thus, if we see an edge with a
                # 2000ms distance to the last one, this edge marks the
                # beginning of a new minute (and DCF77 bit 0 of that minute).
                if len_edges_ms in range(1600, 2400 + 1):
                    self.bitcount = 0
                    self.ss_bit_old = self.ss_bit
                    self.dcf77_bitnumber_is_known = 1

                self.ss_bit_old = self.ss_bit
                self.state = 'GET BIT'

            elif self.state == 'GET BIT':
                # Wait until the next falling edge occurs.
                self.wait({0: 'f'})

                # Save the sample number where the DCF77 bit ends.
                self.es_bit = self.samplenum

                # Calculate the length (in ms) of the current high period.
                len_high = self.samplenum - self.ss_bit
                len_high_ms = int((len_high / self.samplerate) * 1000)

                # If the high signal was 100ms long, that encodes a 0 bit.
                # If it was 200ms long, that encodes a 1 bit.
                if len_high_ms in range(40, 160 + 1):
                    bit = 0
                elif len_high_ms in range(161, 260 + 1):
                    bit = 1
                else:
                    bit = -1

                if bit in (0, 1):
                    self.handle_dcf77_bit(bit)
                    self.bitcount += 1
                else:
                    self.putx([19, ['Invalid bit timing', 'Inv timing', 'Inv']])

                self.state = 'WAIT FOR RISING EDGE'
