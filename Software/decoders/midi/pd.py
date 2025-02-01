##
## This file is part of the libsigrokdecode project.
##
## Copyright (C) 2013-2016 Uwe Hermann <uwe@hermann-uwe.de>
## Copyright (C) 2016 Chris Dreher <chrisdreher@hotmail.com>
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
from .lists import *

RX = 0
TX = 1

class Decoder(srd.Decoder):
    api_version = 3
    id = 'midi'
    name = 'MIDI'
    longname = 'Musical Instrument Digital Interface'
    desc = 'Musical Instrument Digital Interface (MIDI) protocol.'
    license = 'gplv2+'
    inputs = ['uart']
    outputs = []
    tags = ['Audio', 'PC']
    annotations = (
        ('text-verbose', 'Text (verbose)'),
        ('text-sysreal-verbose', 'SysReal text (verbose)'),
        ('text-error', 'Error text'),
    )
    annotation_rows = (
        ('normal', 'Normal', (0, 2)),
        ('sys-real', 'SysReal', (1,)),
    )

    def __init__(self):
        self.reset()

    def reset(self):
        self.state = 'IDLE'
        self.status_byte = 0
        self.explicit_status_byte = False
        self.cmd = []
        self.ss = None
        self.es = None
        self.ss_block = None
        self.es_block = None

    def start(self):
        self.out_ann = self.register(srd.OUTPUT_ANN)

    def putx(self, data):
        self.put(self.ss_block, self.es_block, self.out_ann, data)

    def get_note_name(self, channel, note):
        if channel != 10:
            return chromatic_notes[note]
        else:
            return 'assuming ' + percussion_notes.get(note, 'undefined')

    def check_for_garbage_flush(self, is_flushed):
        if is_flushed:
            if self.explicit_status_byte:
                self.cmd.insert(0, self.status_byte)
            self.handle_garbage_msg(None)

    def soft_clear_status_byte(self):
        self.explicit_status_byte = False

    def hard_clear_status_byte(self):
        self.status_byte = 0
        self.explicit_status_byte = False

    def set_status_byte(self, newbyte):
        self.status_byte = newbyte
        self.explicit_status_byte = True

    def handle_channel_msg_0x80(self, is_flushed):
        # Note off: 8n kk vv
        # n = channel, kk = note, vv = velocity
        c = self.cmd
        if len(c) < 2:
            self.check_for_garbage_flush(is_flushed)
            return
        self.es_block = self.es
        msg, chan = self.status_byte & 0xf0, (self.status_byte & 0x0f) + 1
        note, velocity = c[0], c[1]
        note_name = self.get_note_name(chan, note)
        self.putx([0, ['Channel %d: %s (note = %d \'%s\', velocity = %d)' % \
                  (chan, status_bytes[msg][0], note, note_name, velocity),
                  'ch %d: %s %d, velocity = %d' % \
                  (chan, status_bytes[msg][1], note, velocity),
                  '%d: %s %d, vel %d' % \
                  (chan, status_bytes[msg][2], note, velocity)]])
        self.cmd, self.state = [], 'IDLE'
        self.soft_clear_status_byte()

    def handle_channel_msg_0x90(self, is_flushed):
        # Note on: 9n kk vv
        # n = channel, kk = note, vv = velocity
        # If velocity == 0 that actually means 'note off', though.
        c = self.cmd
        if len(c) < 2:
            self.check_for_garbage_flush(is_flushed)
            return
        self.es_block = self.es
        msg, chan = self.status_byte & 0xf0, (self.status_byte & 0x0f) + 1
        note, velocity = c[0], c[1]
        s = status_bytes[0x80] if (velocity == 0) else status_bytes[msg]
        note_name = self.get_note_name(chan, note)
        self.putx([0, ['Channel %d: %s (note = %d \'%s\', velocity = %d)' % \
                  (chan, s[0], note, note_name, velocity),
                  'ch %d: %s %d, velocity = %d' % \
                  (chan, s[1], note, velocity),
                  '%d: %s %d, vel %d' % \
                  (chan, s[2], note, velocity)]])
        self.cmd, self.state = [], 'IDLE'
        self.soft_clear_status_byte()

    def handle_channel_msg_0xa0(self, is_flushed):
        # Polyphonic key pressure / aftertouch: An kk vv
        # n = channel, kk = polyphonic key pressure, vv = pressure value
        c = self.cmd
        if len(c) < 2:
            self.check_for_garbage_flush(is_flushed)
            return
        self.es_block = self.es
        msg, chan = self.status_byte & 0xf0, (self.status_byte & 0x0f) + 1
        note, pressure = c[0], c[1]
        note_name = self.get_note_name(chan, note)
        self.putx([0, ['Channel %d: %s of %d for note = %d \'%s\'' % \
                  (chan, status_bytes[msg][0], pressure, note, note_name),
                  'ch %d: %s %d for note %d' % \
                  (chan, status_bytes[msg][1], pressure, note),
                  '%d: %s %d, N %d' % \
                  (chan, status_bytes[msg][2], pressure, note)]])
        self.cmd, self.state = [], 'IDLE'
        self.soft_clear_status_byte()

    def handle_controller_0x44(self):
        # Legato footswitch: Bn 44 vv
        # n = channel, vv = value (<= 0x3f: normal, > 0x3f: legato)
        c = self.cmd
        msg, chan = self.status_byte & 0xf0, (self.status_byte & 0x0f) + 1
        vv = c[1]
        t = ('normal', 'no') if vv <= 0x3f else ('legato', 'yes')
        self.putx([0, ['Channel %d: %s \'%s\' = %s' % \
                  (chan, status_bytes[msg][0],
                  control_functions[0x44][0], t[0]),
                  'ch %d: %s \'%s\' = %s' % \
                  (chan, status_bytes[msg][1],
                  control_functions[0x44][1], t[0]),
                  '%d: %s \'%s\' = %s' % \
                  (chan, status_bytes[msg][2],
                  control_functions[0x44][2], t[1])]])

    def handle_controller_0x54(self):
        # Portamento control (PTC): Bn 54 kk
        # n = channel, kk = source note for pitch reference
        c = self.cmd
        msg, chan = self.status_byte & 0xf0, (self.status_byte & 0x0f) + 1
        kk = c[1]
        kk_name = self.get_note_name(chan, kk)
        self.putx([0, ['Channel %d: %s \'%s\' (source note = %d / %s)' % \
                  (chan, status_bytes[msg][0],
                  control_functions[0x54][0], kk, kk_name),
                  'ch %d: %s \'%s\' (source note = %d)' % \
                  (chan, status_bytes[msg][1],
                  control_functions[0x54][1], kk),
                  '%d: %s \'%s\' (src N %d)' % \
                  (chan, status_bytes[msg][2],
                  control_functions[0x54][2], kk)]])

    def handle_controller_generic(self):
        c = self.cmd
        msg, chan = self.status_byte & 0xf0, (self.status_byte & 0x0f) + 1
        fn, param = c[0], c[1]
        default_name = 'undefined'
        ctrl_fn = control_functions.get(fn, default_name)
        if ctrl_fn == default_name:
            ctrl_fn = ('undefined 0x%02x' % fn, 'undef 0x%02x' % fn, '0x%02x' % fn)
        self.putx([0, ['Channel %d: %s \'%s\' (param = 0x%02x)' % \
                  (chan, status_bytes[msg][0], ctrl_fn[0], param),
                  'ch %d: %s \'%s\' (param = 0x%02x)' % \
                  (chan, status_bytes[msg][1], ctrl_fn[1], param),
                  '%d: %s \'%s\' is 0x%02x' % \
                  (chan, status_bytes[msg][2], ctrl_fn[2], param)]])

    def handle_channel_mode(self):
        # Channel Mode: Bn mm vv
        # n = channel, mm = mode number (120 - 127), vv = value
        c = self.cmd
        msg, chan = self.status_byte & 0xf0, (self.status_byte & 0x0f) + 1
        mm, vv = c[0], c[1]
        mode_fn = control_functions.get(mm, ('undefined', 'undef', 'undef'))
        # Decode the value based on the mode number.
        vv_string = ('', '')
        if mm == 122:           # mode = local control?
            if vv == 0:
                vv_string = ('off', 'off')
            elif vv == 127:     # mode = poly mode on?
                vv_string = ('on', 'on')
            else:
                vv_string = ('(non-standard param value of 0x%02x)' % vv,
                            '0x%02x' % vv)
        elif mm == 126:         # mode = mono mode on?
            if vv != 0:
                vv_string = ('(%d channels)' % vv, '(%d ch)' % vv)
            else:
                vv_string = ('(channels \'basic\' through 16)',
                            '(ch \'basic\' thru 16)')
        elif vv != 0: # All other channel mode messages expect vv == 0.
            vv_string = ('(non-standard param value of 0x%02x)' % vv,
                        '0x%02x' % vv)
        self.putx([0, ['Channel %d: %s \'%s\' %s' % \
                      (chan, status_bytes[msg][0], mode_fn[0], vv_string[0]),
                      'ch %d: %s \'%s\' %s' % \
                      (chan, status_bytes[msg][1], mode_fn[1], vv_string[1]),
                      '%d: %s \'%s\' %s' % \
                      (chan, status_bytes[msg][2], mode_fn[2], vv_string[1])]])
        self.cmd, self.state = [], 'IDLE'
        self.soft_clear_status_byte()

    def handle_channel_msg_0xb0(self, is_flushed):
        # Control change (or channel mode messages): Bn cc vv
        # n = channel, cc = control number (0 - 119), vv = control value
        c = self.cmd
        if len(c) < 2:
            self.check_for_garbage_flush(is_flushed)
            return
        self.es_block = self.es
        if c[0] in range(0x78, 0x7f + 1):
            self.handle_channel_mode()
            return
        handle_ctrl = getattr(self, 'handle_controller_0x%02x' % c[0],
                              self.handle_controller_generic)
        handle_ctrl()
        self.cmd, self.state = [], 'IDLE'
        self.soft_clear_status_byte()

    def handle_channel_msg_0xc0(self, is_flushed):
        # Program change: Cn pp
        # n = channel, pp = program number (0 - 127)
        c = self.cmd
        if len(c) < 1:
            self.check_for_garbage_flush(is_flushed)
            return
        self.es_block = self.es
        msg, chan = self.status_byte & 0xf0, (self.status_byte & 0x0f) + 1
        pp = self.cmd[0] + 1
        change_type = 'instrument'
        name = ''
        if chan != 10:  # channel != percussion
            name = gm_instruments.get(pp, 'undefined')
        else:
            change_type = 'drum kit'
            name = drum_kit.get(pp, 'undefined')
        self.putx([0, ['Channel %d: %s to %s %d (assuming %s)' % \
            (chan, status_bytes[msg][0], change_type, pp, name),
            'ch %d: %s to %s %d' % \
            (chan, status_bytes[msg][1], change_type, pp),
            '%d: %s %d' % \
            (chan, status_bytes[msg][2], pp)]])
        self.cmd, self.state = [], 'IDLE'
        self.soft_clear_status_byte()

    def handle_channel_msg_0xd0(self, is_flushed):
        # Channel pressure / aftertouch: Dn vv
        # n = channel, vv = pressure value
        c = self.cmd
        if len(c) < 1:
            self.check_for_garbage_flush(is_flushed)
            return
        self.es_block = self.es
        msg, chan = self.status_byte & 0xf0, (self.status_byte & 0x0f) + 1
        vv = self.cmd[0]
        self.putx([0, ['Channel %d: %s %d' % (chan, status_bytes[msg][0], vv),
                      'ch %d: %s %d' % (chan, status_bytes[msg][1], vv),
                      '%d: %s %d' % (chan, status_bytes[msg][2], vv)]])
        self.cmd, self.state = [], 'IDLE'
        self.soft_clear_status_byte()

    def handle_channel_msg_0xe0(self, is_flushed):
        # Pitch bend change: En ll mm
        # n = channel, ll = pitch bend change LSB, mm = pitch bend change MSB
        c = self.cmd
        if len(c) < 2:
            self.check_for_garbage_flush(is_flushed)
            return
        self.es_block = self.es
        msg, chan = self.status_byte & 0xf0, (self.status_byte & 0x0f) + 1
        ll, mm = self.cmd[0], self.cmd[1]
        decimal = (mm << 7) + ll
        self.putx([0, ['Channel %d: %s 0x%02x 0x%02x (%d)' % \
                      (chan, status_bytes[msg][0], ll, mm, decimal),
                      'ch %d: %s 0x%02x 0x%02x (%d)' % \
                      (chan, status_bytes[msg][1], ll, mm, decimal),
                      '%d: %s (%d)' % \
                      (chan, status_bytes[msg][2], decimal)]])
        self.cmd, self.state = [], 'IDLE'
        self.soft_clear_status_byte()

    def handle_channel_msg_generic(self, is_flushed):
        # TODO: It should not be possible to hit this code.
        # It currently can not be unit tested.
        msg_type = self.status_byte & 0xf0
        self.es_block = self.es
        self.putx([2, ['Unknown channel message type: 0x%02x' % msg_type]])
        self.cmd, self.state = [], 'IDLE'
        self.soft_clear_status_byte()

    def handle_channel_msg(self, newbyte):
        if newbyte is not None:
            if newbyte >= 0x80:
                self.set_status_byte(newbyte)
            else:
                self.cmd.append(newbyte)
        msg_type = self.status_byte & 0xf0
        handle_msg = getattr(self, 'handle_channel_msg_0x%02x' % msg_type,
                             self.handle_channel_msg_generic)
        handle_msg(newbyte is None)

    def handle_sysex_msg(self, newbyte):
        # SysEx message: 1 status byte, 1-3 manuf. bytes, x data bytes, EOX byte
        #
        # SysEx messages are variable length, can be terminated by EOX or
        # by any non-SysReal status byte, and it clears self.status_byte.
        #
        # Note: All System message codes don't utilize self.status_byte.
        self.hard_clear_status_byte()
        if newbyte != 0xf7 and newbyte is not None: # EOX
            self.cmd.append(newbyte)
            return
        self.es_block = self.es
        # Note: Unlike other methods, this code pops bytes out of self.cmd
        # to isolate the data.
        msg = self.cmd.pop(0)
        if len(self.cmd) < 1:
            self.putx([2, ['%s: truncated manufacturer code (<1 bytes)' % \
                          status_bytes[msg][0],
                          '%s: truncated manufacturer (<1 bytes)' % \
                          status_bytes[msg][1],
                          '%s: trunc. manu.' % status_bytes[msg][2]]])
            self.cmd, self.state = [], 'IDLE'
            return
        # Extract the manufacturer name (or SysEx realtime or non-realtime).
        m1 = self.cmd.pop(0)
        manu = (m1,)
        if m1 == 0x00:  # If byte == 0, then 2 more manufacturer bytes follow.
            if len(self.cmd) < 2:
                self.putx([2, ['%s: truncated manufacturer code (<3 bytes)' % \
                          status_bytes[msg][0],
                          '%s: truncated manufacturer (<3 bytes)' % \
                          status_bytes[msg][1],
                          '%s: trunc. manu.' % status_bytes[msg][2]]])
                self.cmd, self.state = [], 'IDLE'
                return
            manu = (m1, self.cmd.pop(0), self.cmd.pop(0))
        default_name = 'undefined'
        manu_name = sysex_manufacturer_ids.get(manu, default_name)
        if manu_name == default_name:
            if len(manu) == 3:
                manu_name = ('%s (0x%02x 0x%02x 0x%02x)' % \
                            (default_name, manu[0], manu[1], manu[2]),
                            default_name)
            else:
                manu_name = ('%s (0x%02x)' % (default_name, manu[0]),
                            default_name)
        else:
            manu_name = (manu_name, manu_name)
        # Extract the payload, display in 1 of 2 formats
        # TODO: Write methods to decode SysEx realtime & non-realtime payloads.
        payload0 = ''
        payload1 = ''
        while len(self.cmd) > 0:
            byte = self.cmd.pop(0)
            payload0 += '0x%02x ' % (byte)
            payload1 += '%02x ' % (byte)
        if payload0 == '':
            payload0 = '<empty>'
            payload1 = '<>'
        payload = (payload0, payload1)
        self.putx([0, ['%s: for \'%s\' with payload %s' % \
                      (status_bytes[msg][0], manu_name[0], payload[0]),
                      '%s: \'%s\', payload %s' % \
                      (status_bytes[msg][1], manu_name[1], payload[1]),
                      '%s: \'%s\', payload %s' % \
                      (status_bytes[msg][2], manu_name[1], payload[1])]])
        self.cmd, self.state = [], 'IDLE'

    def handle_syscommon_midi_time_code_quarter_frame_msg(self, newbyte):
        # MIDI time code quarter frame: F1 nd
        # n = message type
        # d = values
        #
        # Note: All System message codes don't utilize self.status_byte,
        # and System Exclusive and System Common clear it.
        c = self.cmd
        if len(c) < 2:
            if newbyte is None:
                self.handle_garbage_msg(None)
            return
        msg = c[0]
        nn, dd = (c[1] & 0x70) >> 4, c[1] & 0x0f
        group = ('System Common', 'SysCom', 'SC')
        self.es_block = self.es
        if nn != 7: # If message type does not contain SMPTE type.
            self.putx([0, ['%s: %s of %s, value 0x%01x' % \
                          (group[0], status_bytes[msg][0],
                          quarter_frame_type[nn][0], dd),
                          '%s: %s of %s, value 0x%01x' % \
                          (group[1], status_bytes[msg][1],
                          quarter_frame_type[nn][1], dd),
                          '%s: %s of %s, value 0x%01x' % \
                          (group[2], status_bytes[msg][2],
                          quarter_frame_type[nn][1], dd)]])
            self.cmd, self.state = [], 'IDLE'
            return
        tt = (dd & 0x6) >> 1
        self.putx([0, ['%s: %s of %s, value 0x%01x for %s' % \
                      (group[0], status_bytes[msg][0], \
                      quarter_frame_type[nn][0], dd, smpte_type[tt]),
                      '%s: %s of %s, value 0x%01x for %s' % \
                      (group[1], status_bytes[msg][1], \
                      quarter_frame_type[nn][1], dd, smpte_type[tt]),
                      '%s: %s of %s, value 0x%01x for %s' % \
                      (group[2], status_bytes[msg][2], \
                      quarter_frame_type[nn][1], dd, smpte_type[tt])]])
        self.cmd, self.state = [], 'IDLE'

    def handle_syscommon_msg(self, newbyte):
        # System common messages
        #
        # There are 5 simple formats (which are directly handled here) and
        # 1 complex one called MIDI time code quarter frame.
        #
        # Note: While the MIDI lists 0xf7 as a "system common" message, it
        # is actually only used with SysEx messages so it is processed there.
        #
        # Note: All System message codes don't utilize self.status_byte.
        self.hard_clear_status_byte()
        if newbyte is not None:
            self.cmd.append(newbyte)
        c = self.cmd
        msg = c[0]
        group = ('System Common', 'SysCom', 'SC')
        if msg == 0xf1:
            # MIDI time code quarter frame
            self.handle_syscommon_midi_time_code_quarter_frame_msg(newbyte)
            return
        elif msg == 0xf2:
            # Song position pointer: F2 ll mm
            # ll = LSB position, mm = MSB position
            if len(c) < 3:
                if newbyte is None:
                    self.handle_garbage_msg(None)
                return
            ll, mm = c[1], c[2]
            decimal = (mm << 7) + ll
            self.es_block = self.es
            self.putx([0, ['%s: %s 0x%02x 0x%02x (%d)' % \
                          (group[0], status_bytes[msg][0], ll, mm, decimal),
                          '%s: %s 0x%02x 0x%02x (%d)' % \
                          (group[1], status_bytes[msg][1], ll, mm, decimal),
                          '%s: %s (%d)' % \
                          (group[2], status_bytes[msg][2], decimal)]])
        elif msg == 0xf3:
            # Song select: F3 ss
            # ss = song selection number
            if len(c) < 2:
                if newbyte is None:
                    self.handle_garbage_msg(None)
                return
            ss = c[1]
            self.es_block = self.es
            self.putx([0, ['%s: %s number %d' % \
                          (group[0], status_bytes[msg][0], ss),
                          '%s: %s number %d' % \
                          (group[1], status_bytes[msg][1], ss),
                          '%s: %s # %d' % \
                          (group[2], status_bytes[msg][2], ss)]])
        elif msg == 0xf4 or msg == 0xf5 or msg == 0xf6:
            # Undefined 0xf4, Undefined 0xf5, and Tune Request (respectively).
            # All are only 1 byte long with no data bytes.
            self.es_block = self.es
            self.putx([0, ['%s: %s' % (group[0], status_bytes[msg][0]),
                          '%s: %s' % (group[1], status_bytes[msg][1]),
                          '%s: %s' % (group[2], status_bytes[msg][2])]])
        self.cmd, self.state = [], 'IDLE'

    def handle_sysrealtime_msg(self, newbyte):
        # System realtime message: 0b11111ttt (t = message type)
        #
        # Important: These messages are handled differently from all others
        # because they are allowed to temporarily interrupt other messages.
        # The interrupted messages resume after the realtime message is done.
        # Thus, they mostly leave 'self' the way it was found.
        #
        # Note: All System message codes don't utilize self.status_byte.
        old_ss_block, old_es_block = self.ss_block, self.es_block
        self.ss_block, self.es_block = self.ss, self.es
        group = ('System Realtime', 'SysReal', 'SR')
        self.putx([1, ['%s: %s' % (group[0], status_bytes[newbyte][0]),
                      '%s: %s' % (group[1], status_bytes[newbyte][1]),
                      '%s: %s' % (group[2], status_bytes[newbyte][2])]])
        self.ss_block, self.es_block = old_ss_block, old_es_block
        # Deliberately not resetting self.cmd or self.state.

    def handle_garbage_msg(self, newbyte):
        # Handle messages that are either not handled or are corrupt.
        self.es_block = self.es
        if newbyte is not None:
            self.cmd.append(newbyte)
            return
        payload = '<empty>'
        max_bytes = 16 # Put a limit on the length on the hex dump.
        for index in range(len(self.cmd)):
            if index == max_bytes:
                payload += ' ...'
                break
            if index == 0:
                payload = '0x%02x' % self.cmd[index]
            else:
                payload += ' 0x%02x' % self.cmd[index]
        self.putx([2, ['UNHANDLED DATA: %s' % payload,
                      'UNHANDLED', '???', '?']])
        self.cmd, self.state = [], 'IDLE'
        self.hard_clear_status_byte()

    def handle_state(self, state, newbyte):
        # 'newbyte' can either be:
        # 1. Value between 0x00-0xff, deal with the byte normally.
        # 2. Value of 'None' which means "flush any buffered data".
        if state == 'HANDLE CHANNEL MSG':
            self.handle_channel_msg(newbyte)
        elif state == 'HANDLE SYSEX MSG':
            self.handle_sysex_msg(newbyte)
        elif state == 'HANDLE SYSCOMMON MSG':
            self.handle_syscommon_msg(newbyte)
        elif state == 'HANDLE SYSREALTIME MSG':
            self.handle_sysrealtime_msg(newbyte)
        elif state == 'BUFFER GARBAGE MSG':
            self.handle_garbage_msg(newbyte)

    def get_next_state(self, newbyte):
        # 'newbyte' must be a valid byte between 0x00 and 0xff.
        #
        # Try to determine the state based off of the 'newbyte' parameter.
        if newbyte in range(0x80, 0xef + 1):
            return 'HANDLE CHANNEL MSG'
        if newbyte == 0xf0:
            return 'HANDLE SYSEX MSG'
        if newbyte in range(0xf1, 0xf7):
            return'HANDLE SYSCOMMON MSG'
        if newbyte in range(0xf8, 0xff + 1):
            return 'HANDLE SYSREALTIME MSG'
        # Passing 0xf7 is an error; messages don't start with 0xf7.
        if newbyte == 0xf7:
            return 'BUFFER GARBAGE MSG'
        # Next, base the state off of self.status_byte.
        if self.status_byte < 0x80:
            return 'BUFFER GARBAGE MSG'
        return self.get_next_state(self.status_byte)

    def decode(self, ss, es, data):
        ptype, rxtx, pdata = data
        state = 'IDLE'

        # For now, ignore all UART packets except the actual data packets.
        if ptype != 'DATA':
            return

        # We're only interested in the byte value (not individual bits).
        pdata = pdata[0]

        # Short MIDI overview:
        #  - Status bytes are 0x80-0xff, data bytes are 0x00-0x7f.
        #  - Most messages: 1 status byte, 1-2 data bytes.
        #  - Real-time system messages: always 1 byte.
        #  - SysEx messages: 1 status byte, n data bytes, EOX byte.
        #
        # Aspects of the MIDI protocol that complicate decoding:
        #  - MIDI System Realtime messages can briefly interrupt other
        #    messages already in progress.
        #  - "Running Status" allows for omitting the status byte in most
        #    scenarios if sequential messages have the same status byte.
        #  - System Exclusive (SysEx) messages can be terminated by ANY
        #    status byte (not limited to EOX byte).

        # State machine.
        if pdata >= 0x80 and pdata != 0xf7:
            state = self.get_next_state(pdata)
            if state != 'HANDLE SYSREALTIME MSG' and self.state != 'IDLE':
                # Flush the previous data since a new message is starting.
                self.handle_state(self.state, None)
            # Cache ss and es -after- flushing previous data.
            self.ss, self.es = ss, es
            # This is a status byte, remember the start sample.
            if state != 'HANDLE SYSREALTIME MSG':
                self.ss_block = ss
        elif self.state == 'IDLE' or self.state == 'BUFFER GARBAGE MSG':
            # Deal with "running status" or that we're buffering garbage.
            self.ss, self.es = ss, es
            if self.state == 'IDLE':
                self.ss_block = ss
            state = self.get_next_state(pdata)
        else:
            self.ss, self.es = ss, es
            state = self.state

        # Yes, this is intentionally _not_ an 'elif' here.
        if state != 'HANDLE SYSREALTIME MSG':
            self.state = state
        if state == 'BUFFER GARBAGE MSG':
            self.status_byte = 0
        self.handle_state(state, pdata)
