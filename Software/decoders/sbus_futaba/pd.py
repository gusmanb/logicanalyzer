##
## This file is part of the libsigrokdecode project.
##
## Copyright (C) 2022 Gerhard Sittig <gerhard.sittig@gmx.net>
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

"""
OUTPUT_PYTHON format:

Packet:
(<ptype>, <pdata>)

This is the list of <ptype> codes and their respective <pdata> values:
 - 'HEADER': The data is the header byte's value.
 - 'PROPORTIONAL': The data is a tuple of the channel number (1-based)
   and the channel's value.
 - 'DIGITAL': The data is a tuple of the channel number (1-based)
   and the channel's value.
 - 'FLAG': The data is a tuple of the flag's name, and the flag's value.
 - 'FOOTER': The data is the footer byte's value.
"""

import sigrokdecode as srd
from common.srdhelper import bitpack_lsb

class Ann:
    HEADER, PROPORTIONAL, DIGITAL, FRAME_LOST, FAILSAFE, FOOTER, \
    WARN = range(7)
    FLAG_LSB = FRAME_LOST

class Decoder(srd.Decoder):
    api_version = 3
    id = 'sbus_futaba'
    name = 'SBUS (Futaba)'
    longname = 'Futaba SBUS (Serial bus)'
    desc = 'Serial bus for hobby remote control by Futaba'
    license = 'gplv2+'
    inputs = ['uart']
    outputs = ['sbus_futaba']
    tags = ['Remote Control']
    options = (
        {'id': 'prop_val_min', 'desc': 'Proportional value lower boundary', 'default': 0},
        {'id': 'prop_val_max', 'desc': 'Proportional value upper boundary', 'default': 2047},
    )
    annotations = (
        ('header', 'Header'),
        ('proportional', 'Proportional'),
        ('digital', 'Digital'),
        ('framelost', 'Frame Lost'),
        ('failsafe', 'Failsafe'),
        ('footer', 'Footer'),
        ('warning', 'Warning'),
    )
    annotation_rows = (
        ('framing', 'Framing', (Ann.HEADER, Ann.FOOTER,
            Ann.FRAME_LOST, Ann.FAILSAFE)),
        ('channels', 'Channels', (Ann.PROPORTIONAL, Ann.DIGITAL)),
        ('warnings', 'Warnings', (Ann.WARN,)),
    )

    def __init__(self):
        self.bits_accum = []
        self.sent_fields = None
        self.msg_complete = None
        self.failed = None
        self.reset()

    def reset(self):
        self.bits_accum.clear()
        self.sent_fields = 0
        self.msg_complete = False
        self.failed = None

    def start(self):
        self.out_ann = self.register(srd.OUTPUT_ANN)
        self.out_py = self.register(srd.OUTPUT_PYTHON)

    def putg(self, ss, es, data):
        # Put a graphical annotation.
        self.put(ss, es, self.out_ann, data)

    def putpy(self, ss, es, data):
        # Pass Python to upper layers.
        self.put(ss, es, self.out_py, data)

    def get_ss_es_bits(self, bitcount):
        # Get start/end times, and bit values of given length.
        # Gets all remaining data when 'bitcount' is None.
        if bitcount is None:
            bitcount = len(self.bits_accum)
        if len(self.bits_accum) < bitcount:
            return None, None, None
        bits = self.bits_accum[:bitcount]
        self.bits_accum = self.bits_accum[bitcount:]
        ss, es = bits[0][1], bits[-1][2]
        bits = [b[0] for b in bits]
        return ss, es, bits

    def flush_accum_bits(self):
        # Valid data was queued. See if we got full SBUS fields so far.
        # Annotate them early, cease inspection of failed messages. The
        # implementation is phrased to reduce the potential for clipboard
        # errors: 'upto' is the next supported field count, 'want' is one
        # field's bit count. Grab as many as we find in an invocation.
        upto = 0
        if self.failed:
            return
        # Annotate the header byte. Not seeing the expected bit pattern
        # emits a warning annotation, but by design won't fail the SBUS
        # message. It's considered more useful to present the channels'
        # values instead. The warning still raises awareness.
        upto += 1
        want = 8
        while self.sent_fields < upto:
            if len(self.bits_accum) < want:
                return
            ss, es, bits = self.get_ss_es_bits(want)
            value = bitpack_lsb(bits)
            text = ['0x{:02x}'.format(value)]
            self.putg(ss, es, [Ann.HEADER, text])
            if value != 0x0f:
                text = ['Unexpected header', 'Header']
                self.putg(ss, es, [Ann.WARN, text])
            self.putpy(ss, es, ['HEADER', value])
            self.sent_fields += 1
        # Annotate the proportional channels' data. Check for user
        # provided value range violations. Channel numbers are in
        # the 1..18 range (1-based).
        upto += 16
        want = 11
        while self.sent_fields < upto:
            if len(self.bits_accum) < want:
                return
            ss, es, bits = self.get_ss_es_bits(want)
            value = bitpack_lsb(bits)
            text = ['{:d}'.format(value)]
            self.putg(ss, es, [Ann.PROPORTIONAL, text])
            if value < self.options['prop_val_min']:
                text = ['Low proportional value', 'Low value', 'Low']
                self.putg(ss, es, [Ann.WARN, text])
            if value > self.options['prop_val_max']:
                text = ['High proportional value', 'High value', 'High']
                self.putg(ss, es, [Ann.WARN, text])
            idx = self.sent_fields - (upto - 16)
            ch_nr = 1 + idx
            self.putpy(ss, es, ['PROPORTIONAL', (ch_nr, value)])
            self.sent_fields += 1
        # Annotate the digital channels' data.
        upto += 2
        want = 1
        while self.sent_fields < upto:
            if len(self.bits_accum) < want:
                return
            ss, es, bits = self.get_ss_es_bits(want)
            value = bitpack_lsb(bits)
            text = ['{:d}'.format(value)]
            self.putg(ss, es, [Ann.DIGITAL, text])
            idx = self.sent_fields - (upto - 2)
            ch_nr = 17 + idx
            self.putpy(ss, es, ['DIGITAL', (ch_nr, value)])
            self.sent_fields += 1
        # Annotate the flags' state. Index starts from LSB.
        flag_names = ['framelost', 'failsafe', 'msb']
        upto += 2
        want = 1
        while self.sent_fields < upto:
            if len(self.bits_accum) < want:
                return
            ss, es, bits = self.get_ss_es_bits(want)
            value = bitpack_lsb(bits)
            text = ['{:d}'.format(value)]
            idx = self.sent_fields - (upto - 2)
            cls = Ann.FLAG_LSB + idx
            self.putg(ss, es, [cls, text])
            flg_name = flag_names[idx]
            self.putpy(ss, es, ['FLAG', (flg_name, value)])
            self.sent_fields += 1
        # Warn when flags' padding (bits [7:4]) is unexpexted.
        upto += 1
        want = 4
        while self.sent_fields < upto:
            if len(self.bits_accum) < want:
                return
            ss, es, bits = self.get_ss_es_bits(want)
            value = bitpack_lsb(bits)
            if value != 0x0:
                text = ['Unexpected MSB flags', 'Flags']
                self.putg(ss, es, [Ann.WARN, text])
            flg_name = flag_names[-1]
            self.putpy(ss, es, ['FLAG', (flg_name, value)])
            self.sent_fields += 1
        # Annotate the footer byte. Warn when unexpected.
        upto += 1
        want = 8
        while self.sent_fields < upto:
            if len(self.bits_accum) < want:
                return
            ss, es, bits = self.get_ss_es_bits(want)
            value = bitpack_lsb(bits)
            text = ['0x{:02x}'.format(value)]
            self.putg(ss, es, [Ann.FOOTER, text])
            if value != 0x00:
                text = ['Unexpected footer', 'Footer']
                self.putg(ss, es, [Ann.WARN, text])
            self.putpy(ss, es, ['FOOTER', value])
            self.sent_fields += 1
        # Check for the completion of an SBUS message. Warn when more
        # UART data is seen after the message. Defer the warning until
        # more bits were collected, flush at next IDLE or BREAK, which
        # spans all unprocessed data, and improves perception.
        if self.sent_fields >= upto:
            self.msg_complete = True
        if self.msg_complete and self.bits_accum:
            self.failed = ['Excess data bits', 'Excess']

    def handle_bits(self, ss, es, bits):
        # UART data bits were seen. Store them, validity is yet unknown.
        self.bits_accum.extend(bits)

    def handle_frame(self, ss, es, value, valid):
        # A UART frame became complete. Get its validity. Process its bits.
        if not valid:
            self.failed = ['Invalid data', 'Invalid']
        self.flush_accum_bits()

    def handle_idle(self, ss, es):
        # An IDLE period was seen in the UART level. Flush, reset state.
        if self.bits_accum and not self.failed:
            self.failed = ['Unprocessed data bits', 'Unprocessed']
        if self.bits_accum and self.failed:
            ss, es, _ = self.get_ss_es_bits(None)
            self.putg(ss, es, [Ann.WARN, self.failed])
        self.reset()

    def handle_break(self, ss, es):
        # A BREAK period was seen in the UART level. Warn, reset state.
        break_ss, break_es = ss, es
        if not self.failed:
            self.failed = ['BREAK condition', 'Break']
        # Re-use logic for "annotated bits warning".
        self.handle_idle(None, None)
        # Unconditionally annotate BREAK as warning.
        text = ['BREAK condition', 'Break']
        self.putg(ss, es, [Ann.WARN, text])
        self.reset()

    def decode(self, ss, es, data):
        # Implementor's note: Expects DATA bits to arrive before FRAME
        # validity. Either of IDLE or BREAK terminates an SBUS message.
        ptype, rxtx, pdata = data
        if ptype == 'DATA':
            _, bits = pdata
            self.handle_bits(ss, es, bits)
        elif ptype == 'FRAME':
            value, valid = pdata
            self.handle_frame(ss, es, value, valid)
        elif ptype == 'IDLE':
            self.handle_idle(ss, es)
        elif ptype == 'BREAK':
            self.handle_break(ss, es)
