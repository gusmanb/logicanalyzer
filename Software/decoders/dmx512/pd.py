##
## This file is part of the libsigrokdecode project.
##
## Copyright (C) 2016 Fabian J. Stumpf <sigrok@fabianstumpf.de>
## Copyright (C) 2019-2020 Gerhard Sittig <gerhard.sittig@gmx.net>
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

'''
OUTPUT_PYTHON format:

Packet:
[<ptype>, <pdata>]

This is the list of <ptype> codes and their respective <pdata> values:
 - 'PACKET': The data is a list of tuples with the bytes' start and end
   positions as well as a byte value and a validity flag. This output
   represents a DMX packet. The sample numbers span the range beginning
   at the start of the start code and ending at the end of the last data
   byte in the packet. The start code value resides at index 0.

Developer notes on the DMX512 protocol:

See Wikipedia for an overview:
  https://en.wikipedia.org/wiki/DMX512#Electrical (physics, transport)
  https://en.wikipedia.org/wiki/DMX512#Protocol (UART frames, DMX frames)
  RS-485 transport, differential thus either polarity (needs user spec)
  8n2 UART frames at 250kbps, BREAK to start a new DMX frame
  slot 0 carries start code, slot 1 up to 512 max carry data for peripherals
  start code 0 for "boring lights", non-zero start code for extensions.

TODO
- Cover more DMX packet types beyond start code 0x00 (standard). See
  https://en.wikipedia.org/wiki/DMX512#Protocol for a list (0x17 text,
  0xcc RDM, 0xcf sysinfo) and a reference to the ESTA database. These
  can either get added here or can get implemented in a stacked decoder.
- Run on more captures as these become available. Verify the min/max
  BREAK, MARK, and RESET to RESET period checks. Add more conditions that
  are worth checking to determine the health of the bus, see the (German)
  http://www.soundlight.de/techtips/dmx512/dmx2000a.htm article for ideas.
- Is there a more user friendly way of having the DMX512 decoder configure
  the UART decoder's parameters? Currently users need to setup the polarity
  (which is acceptable, and an essential feature), but also the bitrate and
  frame format (which may or may not be considered acceptable).
- (Not a DMX512 decoder TODO item) Current UART decoder implementation does
  not handle two STOP bits, but DMX512 will transparently benefit when UART
  gets adjusted. Until then the second STOP bit will be mistaken for a MARK
  but that's just cosmetics, available data gets interpreted correctly.
'''

import sigrokdecode as srd

class Ann:
    BREAK, MAB, INTERFRAME, INTERPACKET, STARTCODE, DATABYTE, CHANNEL_DATA, \
    SLOT_DATA, RESET, WARN, ERROR = range(11)

class Decoder(srd.Decoder):
    api_version = 3
    id = 'dmx512'
    name = 'DMX512'
    longname = 'Digital MultipleX 512'
    desc = 'Digital MultipleX 512 (DMX512) lighting protocol.'
    license = 'gplv2+'
    inputs = ['uart']
    outputs = ['dmx512']
    tags = ['Embedded/industrial', 'Lighting']
    options = (
        {'id': 'min_break', 'desc': 'Minimum BREAK length (us)', 'default': 88},
        {'id': 'max_mark', 'desc': 'Maximum MARK length (us)', 'default': 1000000},
        {'id': 'min_break_break', 'desc': 'Minimum BREAK to BREAK interval (us)',
            'default': 1196},
        {'id': 'max_reset_reset', 'desc': 'Maximum RESET to RESET interval (us)',
         'default': 1250000},
        {'id': 'show_zero', 'desc': 'Display all-zero set-point values',
            'default': 'no', 'values': ('yes', 'no')},
        {'id': 'format', 'desc': 'Data format', 'default': 'dec',
            'values': ('dec', 'hex', 'bin')},
    )
    annotations = (
        # Lowest layer (above UART): BREAK MARK ( FRAME [MARK] )*
        # with MARK being after-break or inter-frame or inter-packet.
        ('break', 'Break'),
        ('mab', 'Mark after break'),
        ('interframe', 'Interframe'),
        ('interpacket', 'Interpacket'),
        # Next layer: STARTCODE ( DATABYTE )*
        ('startcode', 'Start code'),
        ('databyte', 'Data byte'),
        # Next layer: CHANNEL or SLOT values
        ('chan_data', 'Channel data'),
        ('slot_data', 'Slot data'),
        # Next layer: RESET
        ('reset', 'Reset sequence'),
        # Warnings and errors.
        ('warning', 'Warning'),
        ('error', 'Error'),
    )
    annotation_rows = (
        ('dmx_fields', 'Fields', (Ann.BREAK, Ann.MAB,
            Ann.STARTCODE, Ann.INTERFRAME,
            Ann.DATABYTE, Ann.INTERPACKET)),
        ('chans_data', 'Channels data', (Ann.CHANNEL_DATA,)),
        ('slots_data', 'Slots data', (Ann.SLOT_DATA,)),
        ('resets', 'Reset sequences', (Ann.RESET,)),
        ('warnings', 'Warnings', (Ann.WARN,)),
        ('errors', 'Errors', (Ann.ERROR,)),
    )

    def __init__(self):
        self.reset()

    def reset(self):
        self.samplerate = None
        self.samples_per_usec = None
        self.last_reset = None
        self.last_break = None
        self.packet = None
        self.last_es = None
        self.last_frame = None
        self.start_code = None

    def start(self):
        self.out_ann = self.register(srd.OUTPUT_ANN)
        self.out_python = self.register(srd.OUTPUT_PYTHON)

    def metadata(self, key, value):
        if key == srd.SRD_CONF_SAMPLERATE:
            self.samplerate = value
            self.samples_per_usec = value / 1000000

    def have_samplerate(self):
        return bool(self.samplerate)

    def samples_to_usecs(self, count):
        return count / self.samples_per_usec

    def putg(self, ss, es, data):
        self.put(ss, es, self.out_ann, data)

    def putpy(self, ss, es, data):
        self.put(ss, es, self.out_python, data)

    def format_value(self, v):
        fmt = self.options['format']
        if fmt == 'dec':
            return '{:d}'.format(v)
        if fmt == 'hex':
            return '{:02X}'.format(v)
        if fmt == 'bin':
            return '{:08b}'.format(v)
        return '{}'.format(v)

    def flush_packet(self):
        if self.packet:
            ss, es = self.packet[0][0], self.packet[-1][1]
            self.putpy(ss, es, ['PACKET', self.packet])
        self.packet = None

    def flush_reset(self, ss, es):
        if ss is not None and es is not None:
            self.putg(ss, es, [Ann.RESET, ['RESET SEQUENCE', 'RESET', 'R']])
            if self.last_reset and self.have_samplerate():
                duration = self.samples_to_usecs(es - self.last_reset)
                if duration > self.options['max_reset_reset']:
                    txts = ['Excessive RESET to RESET interval', 'RESET to RESET', 'RESET']
                    self.putg(self.last_reset, es, [Ann.WARN, txts])
        self.last_reset = es

    def flush_break(self, ss, es):
        self.putg(ss, es, [Ann.BREAK, ['BREAK', 'B']])
        if self.have_samplerate():
            duration = self.samples_to_usecs(es - ss)
            if duration < self.options['min_break']:
                txts = ['Short BREAK period', 'Short BREAK', 'BREAK']
                self.putg(ss, es, [Ann.WARN, txts])
            if self.last_break:
                duration = self.samples_to_usecs(ss - self.last_break)
                if duration < self.options['min_break_break']:
                    txts = ['Short BREAK to BREAK interval', 'Short BREAK to BREAK', 'BREAK']
                    self.putg(ss, es, [Ann.WARN, txts])
        self.last_break = ss
        self.last_es = es

    def flush_mark(self, ss, es, is_mab = False, is_if = False, is_ip = False):
        '''Handle several kinds of MARK conditions.'''

        if ss is None or es is None or ss >= es:
            return

        if is_mab:
            ann = Ann.MAB
            txts = ['MARK AFTER BREAK', 'MAB']
        elif is_if:
            ann = Ann.INTERFRAME
            txts = ['INTER FRAME', 'IF']
        elif is_ip:
            ann = Ann.INTERPACKET
            txts = ['INTER PACKET', 'IP']
        else:
            return
        self.putg(ss, es, [ann, txts])

        if self.have_samplerate():
            duration = self.samples_to_usecs(es - ss)
            if duration > self.options['max_mark']:
                txts = ['Excessive MARK length', 'MARK length', 'MARK']
                self.putg(ss, es, [Ann.ERROR, txts])

    def flush_frame(self, ss, es, value, valid):
        '''Handle UART frame content. Accumulate DMX packet.'''

        if not valid:
            txts = ['Invalid frame', 'Frame']
            self.putg(ss, es, [Ann.ERROR, txts])

        self.last_es = es

        # Cease packet inspection before first BREAK.
        if not self.last_break:
            return

        # Accumulate the sequence of bytes for the current DMX frame.
        # Emit the annotation at the "DMX fields" level.
        is_start = self.packet is None
        if is_start:
            self.packet = []
        slot_nr = len(self.packet)
        item = (ss, es, value, valid)
        self.packet.append(item)
        if is_start:
            # Slot 0, the start code. Determines the DMX frame type.
            self.start_code = value
            ann = Ann.STARTCODE
            val_text = self.format_value(value)
            txts = [
                'STARTCODE {}'.format(val_text),
                'START {}'.format(val_text),
                '{}'.format(val_text),
            ]
        else:
            # Slot 1+, the payload bytes.
            ann = Ann.DATABYTE
            val_text = self.format_value(value)
            txts = [
                'DATABYTE {:d}: {}'.format(slot_nr, val_text),
                'DATA {:d}: {}'.format(slot_nr, val_text),
                'DATA {}'.format(val_text),
                '{}'.format(val_text),
            ]
        self.putg(ss, es, [ann, txts])

        # Tell channel data for peripherals from arbitrary slot values.
        # Can get extended for other start code types in case protocol
        # extensions are handled here and not in stacked decoders.
        if is_start:
            ann = None
        elif self.start_code == 0:
            # Start code was 0. Slots carry values for channels.
            # Optionally suppress zero-values to make used channels
            # stand out, to help users focus their attention.
            ann = Ann.CHANNEL_DATA
            if value == 0 and self.options['show_zero'] == 'no':
                ann = None
            else:
                val_text = self.format_value(value)
                txts = [
                    'CHANNEL {:d}: {}'.format(slot_nr, val_text),
                    'CH {:d}: {}'.format(slot_nr, val_text),
                    'CH {}'.format(val_text),
                    '{}'.format(val_text),
                ]
        else:
            # Unhandled start code. Provide "anonymous" values.
            ann = Ann.SLOT_DATA
            val_text = self.format_value(value)
            txts = [
                'SLOT {:d}: {}'.format(slot_nr, val_text),
                'SL {:d}: {}'.format(slot_nr, val_text),
                'SL {}'.format(val_text),
                '{}'.format(val_text),
            ]
        if ann is not None:
            self.putg(ss, es, [ann, txts])

        if is_start and value == 0:
            self.flush_reset(self.last_break, es)

    def handle_break(self, ss, es):
        '''Handle UART BREAK conditions.'''

        # Check the last frame before BREAK if one was queued. It could
        # have been "invalid" since the STOP bit check failed. If there
        # is an invalid frame which happens to start at the start of the
        # BREAK condition, then discard it. Otherwise flush its output.
        last_frame = self.last_frame
        self.last_frame = None
        frame_invalid = last_frame and not last_frame[3]
        frame_zero_data = last_frame and last_frame[2] == 0
        frame_is_break = last_frame and last_frame[0] == ss
        if frame_invalid and frame_zero_data and frame_is_break:
            last_frame = None
        if last_frame is not None:
            self.flush_frame(*last_frame)

        # Handle inter-packet MARK (works for zero length, too).
        self.flush_mark(self.last_es, ss, is_ip = True)

        # Handle accumulated packets.
        self.flush_packet()
        self.packet = None

        # Annotate the BREAK condition. Start accumulation of a packet.
        self.flush_break(ss, es)

    def handle_frame(self, ss, es, value, valid):
        '''Handle UART data frames.'''

        # Flush previously deferred frame (if available). Can't have been
        # BREAK if another data frame follows.
        last_frame = self.last_frame
        self.last_frame = None
        if last_frame:
            self.flush_frame(*last_frame)

        # Handle inter-frame MARK (works for zero length, too).
        is_mab = self.last_break and self.packet is None
        is_if = self.packet
        self.flush_mark(self.last_es, ss, is_mab = is_mab, is_if = is_if)

        # Defer handling of invalid frames, because they may start a new
        # BREAK which we will only learn about much later. Immediately
        # annotate valid frames.
        if valid:
            self.flush_frame(ss, es, value, valid)
        else:
            self.last_frame = (ss, es, value, valid)

    def decode(self, ss, es, data):
        # Lack of a sample rate in the input capture only disables the
        # optional warnings about exceeded timespans here at the DMX512
        # decoder level. That the lower layer UART decoder depends on a
        # sample rate is handled there, and is not relevant here.

        ptype, rxtx, pdata = data
        if ptype == 'BREAK':
            self.handle_break(ss, es)
        elif ptype == 'FRAME':
            value, valid = pdata
            self.handle_frame(ss, es, value, valid)
