##
## This file is part of the libsigrokdecode project.
##
## Copyright (C) 2014 Jens Steinhauser <jens.steinhauser@gmail.com>
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

class ChannelError(Exception):
    pass

regs = {
#   addr: ('name',        size)
    0x00: ('CONFIG',      1),
    0x01: ('EN_AA',       1),
    0x02: ('EN_RXADDR',   1),
    0x03: ('SETUP_AW',    1),
    0x04: ('SETUP_RETR',  1),
    0x05: ('RF_CH',       1),
    0x06: ('RF_SETUP',    1),
    0x07: ('STATUS',      1),
    0x08: ('OBSERVE_TX',  1),
    0x09: ('RPD',         1),
    0x0a: ('RX_ADDR_P0',  5),
    0x0b: ('RX_ADDR_P1',  5),
    0x0c: ('RX_ADDR_P2',  1),
    0x0d: ('RX_ADDR_P3',  1),
    0x0e: ('RX_ADDR_P4',  1),
    0x0f: ('RX_ADDR_P5',  1),
    0x10: ('TX_ADDR',     5),
    0x11: ('RX_PW_P0',    1),
    0x12: ('RX_PW_P1',    1),
    0x13: ('RX_PW_P2',    1),
    0x14: ('RX_PW_P3',    1),
    0x15: ('RX_PW_P4',    1),
    0x16: ('RX_PW_P5',    1),
    0x17: ('FIFO_STATUS', 1),
    0x1c: ('DYNPD',       1),
    0x1d: ('FEATURE',     1),
}

xn297_regs = {
    0x19: ('DEMOD_CAL',   5),
    0x1e: ('RF_CAL',      7),
    0x1f: ('BB_CAL',      5),
}

class Decoder(srd.Decoder):
    api_version = 3
    id = 'nrf24l01'
    name = 'nRF24L01(+)'
    longname = 'Nordic Semiconductor nRF24L01(+)'
    desc = '2.4GHz RF transceiver chip.'
    license = 'gplv2+'
    inputs = ['spi']
    outputs = []
    tags = ['IC', 'Wireless/RF']
    options = (
        {'id': 'chip', 'desc': 'Chip type',
            'default': 'nrf24l01', 'values': ('nrf24l01', 'xn297')},
    )
    annotations = (
        # Sent from the host to the chip.
        ('cmd', 'Command'),
        ('tx-data', 'Payload'),

        # Returned by the chip.
        ('register', 'Register read'),
        ('rx-data', 'Payload read'),

        ('warning', 'Warning'),
    )
    ann_cmd = 0
    ann_tx = 1
    ann_reg = 2
    ann_rx = 3
    ann_warn = 4
    annotation_rows = (
        ('commands', 'Commands', (ann_cmd, ann_tx)),
        ('responses', 'Responses', (ann_reg, ann_rx)),
        ('warnings', 'Warnings', (ann_warn,)),
    )

    def __init__(self):
        self.reset()

    def reset(self):
        self.next()
        self.requirements_met = True
        self.cs_was_released = False

    def start(self):
        self.out_ann = self.register(srd.OUTPUT_ANN)
        if self.options['chip'] == 'xn297':
            regs.update(xn297_regs)

    def warn(self, pos, msg):
        '''Put a warning message 'msg' at 'pos'.'''
        self.put(pos[0], pos[1], self.out_ann, [self.ann_warn, [msg]])

    def putp(self, pos, ann, msg):
        '''Put an annotation message 'msg' at 'pos'.'''
        self.put(pos[0], pos[1], self.out_ann, [ann, [msg]])

    def next(self):
        '''Resets the decoder after a complete command was decoded.'''
        # 'True' for the first byte after CS went low.
        self.first = True

        # The current command, and the minimum and maximum number
        # of data bytes to follow.
        self.cmd = None
        self.min = 0
        self.max = 0

        # Used to collect the bytes after the command byte
        # (and the start/end sample number).
        self.mb = []
        self.mb_s = -1
        self.mb_e = -1

    def mosi_bytes(self):
        '''Returns the collected MOSI bytes of a multi byte command.'''
        return [b[0] for b in self.mb]

    def miso_bytes(self):
        '''Returns the collected MISO bytes of a multi byte command.'''
        return [b[1] for b in self.mb]

    def decode_command(self, pos, b):
        '''Decodes the command byte 'b' at position 'pos' and prepares
        the decoding of the following data bytes.'''
        c = self.parse_command(b)
        if c is None:
            self.warn(pos, 'unknown command')
            return

        self.cmd, self.dat, self.min, self.max = c

        if self.cmd in ('W_REGISTER', 'ACTIVATE'):
            # Don't output anything now, the command is merged with
            # the data bytes following it.
            self.mb_s = pos[0]
        else:
            self.putp(pos, self.ann_cmd, self.format_command())

    def format_command(self):
        '''Returns the label for the current command.'''
        if self.cmd == 'R_REGISTER':
            reg = regs[self.dat][0] if self.dat in regs else 'unknown register'
            return 'Cmd R_REGISTER "{}"'.format(reg)
        else:
            return 'Cmd {}'.format(self.cmd)

    def parse_command(self, b):
        '''Parses the command byte.

        Returns a tuple consisting of:
        - the name of the command
        - additional data needed to dissect the following bytes
        - minimum number of following bytes
        - maximum number of following bytes
        '''

        if (b & 0xe0) in (0b00000000, 0b00100000):
            c = 'R_REGISTER' if not (b & 0xe0) else 'W_REGISTER'
            d = b & 0x1f
            m = regs[d][1] if d in regs else 1
            return (c, d, 1, m)
        if b == 0b01010000:
            # nRF24L01 only
            return ('ACTIVATE', None, 1, 1)
        if b == 0b01100001:
            return ('R_RX_PAYLOAD', None, 1, 32)
        if b == 0b01100000:
            return ('R_RX_PL_WID', None, 1, 1)
        if b == 0b10100000:
            return ('W_TX_PAYLOAD', None, 1, 32)
        if b == 0b10110000:
            return ('W_TX_PAYLOAD_NOACK', None, 1, 32)
        if (b & 0xf8) == 0b10101000:
            return ('W_ACK_PAYLOAD', b & 0x07, 1, 32)
        if b == 0b11100001:
            return ('FLUSH_TX', None, 0, 0)
        if b == 0b11100010:
            return ('FLUSH_RX', None, 0, 0)
        if b == 0b11100011:
            return ('REUSE_TX_PL', None, 0, 0)
        if b == 0b11111111:
            return ('NOP', None, 0, 0)

    def decode_register(self, pos, ann, regid, data):
        '''Decodes a register.

        pos   -- start and end sample numbers of the register
        ann   -- is the annotation number that is used to output the register.
        regid -- may be either an integer used as a key for the 'regs'
                 dictionary, or a string directly containing a register name.'
        data  -- is the register content.
        '''

        if type(regid) == int:
            # Get the name of the register.
            if regid not in regs:
                self.warn(pos, 'unknown register')
                return
            name = regs[regid][0]
        else:
            name = regid

        # Multi byte register come LSByte first.
        data = reversed(data)

        if self.cmd == 'W_REGISTER' and ann == self.ann_cmd:
            # The 'W_REGISTER' command is merged with the following byte(s).
            label = '{}: {}'.format(self.format_command(), name)
        else:
            label = 'Reg {}'.format(name)

        self.decode_mb_data(pos, ann, data, label, True)

    def decode_mb_data(self, pos, ann, data, label, always_hex):
        '''Decodes the data bytes 'data' of a multibyte command at position
        'pos'. The decoded data is prefixed with 'label'. If 'always_hex' is
        True, all bytes are decoded as hex codes, otherwise only non
        printable characters are escaped.'''

        if always_hex:
            def escape(b):
                return '{:02X}'.format(b)
        else:
            def escape(b):
                c = chr(b)
                if not str.isprintable(c):
                    return '\\x{:02X}'.format(b)
                return c

        data = ''.join([escape(b) for b in data])
        text = '{} = "{}"'.format(label, data)
        self.putp(pos, ann, text)

    def finish_command(self, pos):
        '''Decodes the remaining data bytes at position 'pos'.'''

        if self.cmd == 'R_REGISTER':
            self.decode_register(pos, self.ann_reg,
                                 self.dat, self.miso_bytes())
        elif self.cmd == 'W_REGISTER':
            self.decode_register(pos, self.ann_cmd,
                                 self.dat, self.mosi_bytes())
        elif self.cmd == 'R_RX_PAYLOAD':
            self.decode_mb_data(pos, self.ann_rx,
                                self.miso_bytes(), 'RX payload', False)
        elif (self.cmd == 'W_TX_PAYLOAD' or
              self.cmd == 'W_TX_PAYLOAD_NOACK'):
            self.decode_mb_data(pos, self.ann_tx,
                                self.mosi_bytes(), 'TX payload', False)
        elif self.cmd == 'W_ACK_PAYLOAD':
            lbl = 'ACK payload for pipe {}'.format(self.dat)
            self.decode_mb_data(pos, self.ann_tx,
                                self.mosi_bytes(), lbl, False)
        elif self.cmd == 'R_RX_PL_WID':
            msg = 'Payload width = {}'.format(self.mb[0][1])
            self.putp(pos, self.ann_reg, msg)
        elif self.cmd == 'ACTIVATE':
            self.putp(pos, self.ann_cmd, self.format_command())
            if self.mosi_bytes()[0] != 0x73:
                self.warn(pos, 'wrong data for "ACTIVATE" command')

    def decode(self, ss, es, data):
        if not self.requirements_met:
            return

        ptype, data1, data2 = data

        if ptype == 'CS-CHANGE':
            if data1 is None:
                if data2 is None:
                    self.requirements_met = False
                    raise ChannelError('CS# pin required.')
                elif data2 == 1:
                    self.cs_was_released = True

            if data1 == 0 and data2 == 1:
                # Rising edge, the complete command is transmitted, process
                # the bytes that were send after the command byte.
                if self.cmd:
                    # Check if we got the minimum number of data bytes
                    # after the command byte.
                    if len(self.mb) < self.min:
                        self.warn((ss, ss), 'missing data bytes')
                    elif self.mb:
                        self.finish_command((self.mb_s, self.mb_e))

                self.next()
                self.cs_was_released = True
        elif ptype == 'DATA' and self.cs_was_released:
            mosi, miso = data1, data2
            pos = (ss, es)

            if miso is None or mosi is None:
                self.requirements_met = False
                raise ChannelError('Both MISO and MOSI pins required.')

            if self.first:
                self.first = False
                # First MOSI byte is always the command.
                self.decode_command(pos, mosi)
                # First MISO byte is always the status register.
                self.decode_register(pos, self.ann_reg, 'STATUS', [miso])
            else:
                if not self.cmd or len(self.mb) >= self.max:
                    self.warn(pos, 'excess byte')
                else:
                    # Collect the bytes after the command byte.
                    if self.mb_s == -1:
                        self.mb_s = ss
                    self.mb_e = es
                    self.mb.append((mosi, miso))
