##
## This file is part of the libsigrokdecode project.
##
## Copyright (C) 2019 Marco Geisler <m-sigrok@mageis.de>
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
from collections import namedtuple
from common.srdhelper import SrdIntEnum
from .lists import *

Ann = SrdIntEnum.from_str('Ann', 'STROBE SINGLE_READ SINGLE_WRITE BURST_READ \
    BURST_WRITE STATUS_READ STATUS WARN')

Pos = namedtuple('Pos', ['ss', 'es'])
Data = namedtuple('Data', ['mosi', 'miso'])

class Decoder(srd.Decoder):
    api_version = 3
    id = 'cc1101'
    name = 'CC1101'
    longname = 'Texas Instruments CC1101'
    desc = 'Low-power sub-1GHz RF transceiver chip.'
    license = 'gplv2+'
    inputs = ['spi']
    outputs = []
    tags = ['IC', 'Wireless/RF']
    annotations = (
        ('strobe', 'Command strobe'),
        ('single_read', 'Single register read'),
        ('single_write', 'Single register write'),
        ('burst_read', 'Burst register read'),
        ('burst_write', 'Burst register write'),
        ('status_read', 'Status read'),
        ('status_reg', 'Status register'),
        ('warning', 'Warning'),
    )
    annotation_rows = (
        ('cmds', 'Commands', (Ann.STROBE,)),
        ('data', 'Data', (Ann.prefixes('SINGLE_ BURST_ STATUS_'))),
        ('status', 'Status register', (Ann.STATUS,)),
        ('warnings', 'Warnings', (Ann.WARN,)),
    )

    def __init__(self):
        self.reset()

    def reset(self):
        self.next()
        self.requirements_met = True
        self.cs_was_released = False

    def start(self):
        self.out_ann = self.register(srd.OUTPUT_ANN)

    def warn(self, pos, msg):
        '''Put a warning message 'msg' at 'pos'.'''
        self.put(pos.ss, pos.es, self.out_ann, [Ann.WARN, [msg]])

    def putp(self, pos, ann, msg):
        '''Put an annotation message 'msg' at 'pos'.'''
        self.put(pos.ss, pos.es, self.out_ann, [ann, [msg]])

    def putp2(self, pos, ann, msg1, msg2):
        '''Put an annotation message 'msg' at 'pos'.'''
        self.put(pos.ss, pos.es, self.out_ann, [ann, [msg1, msg2]])

    def next(self):
        '''Resets the decoder after a complete command was decoded.'''
        # 'True' for the first byte after CS# went low.
        self.first = True

        # The current command, and the minimum and maximum number
        # of data bytes to follow.
        self.cmd = None
        self.min = 0
        self.max = 0

        # Used to collect the bytes after the command byte
        # (and the start/end sample number).
        self.mb = []
        self.ss_mb = -1
        self.es_mb = -1

    def mosi_bytes(self):
        '''Returns the collected MOSI bytes of a multi byte command.'''
        return [b.mosi for b in self.mb]

    def miso_bytes(self):
        '''Returns the collected MISO bytes of a multi byte command.'''
        return [b.miso for b in self.mb]

    def decode_command(self, pos, b):
        '''Decodes the command byte 'b' at position 'pos' and prepares
        the decoding of the following data bytes.'''
        c = self.parse_command(b)
        if c is None:
            self.warn(pos, 'unknown command')
            return

        self.cmd, self.dat, self.min, self.max = c

        if self.cmd == 'Strobe':
            self.putp(pos, Ann.STROBE, self.format_command())
        else:
            # Don't output anything now, the command is merged with
            # the data bytes following it.
            self.ss_mb = pos.ss

    def format_command(self):
        '''Returns the label for the current command.'''
        if self.cmd in ('Read', 'Burst read', 'Write', 'Burst write', 'Status read'):
            return self.cmd
        if self.cmd == 'Strobe':
            reg = strobes.get(self.dat, 'unknown strobe')
            return '{} {}'.format(self.cmd, reg)
        else:
            return 'TODO Cmd {}'.format(self.cmd)

    def parse_command(self, b):
        '''Parses the command byte.

        Returns a tuple consisting of:
        - the name of the command
        - additional data needed to dissect the following bytes
        - minimum number of following bytes
        - maximum number of following bytes (None for infinite)
        '''

        addr = b & 0x3F
        if (addr < 0x30) or (addr == 0x3E) or (addr == 0x3F):
            if (b & 0xC0) == 0x00:
                return ('Write', addr, 1, 1)
            if (b & 0xC0) == 0x40:
                return ('Burst write', addr, 1, 99999)
            if (b & 0xC0) == 0x80:
                return ('Read', addr, 1, 1)
            if (b & 0xC0) == 0xC0:
                return ('Burst read', addr, 1, 99999)
            else:
                self.warn(pos, 'unknown address/command combination')
        else:
            if (b & 0x40) == 0x00:
                return ('Strobe', addr, 0, 0)
            if (b & 0xC0) == 0xC0:
                return ('Status read', addr, 1, 99999)
            else:
                self.warn(pos, 'unknown address/command combination')

    def decode_reg(self, pos, ann, regid, data):
        '''Decodes a register.

        pos   -- start and end sample numbers of the register
        ann   -- the annotation number that is used to output the register.
        regid -- may be either an integer used as a key for the 'regs'
                 dictionary, or a string directly containing a register name.'
        data  -- the register content.
        '''

        if type(regid) == int:
            # Get the name of the register.
            if regid not in regs:
                self.warn(pos, 'unknown register')
                return
            name = '{} ({:02X})'.format(regs[regid], regid)
        else:
            name = regid

        if regid == 'STATUS' and ann == Ann.STATUS:
            label = 'Status'
            self.decode_status_reg(pos, ann, data, label)
        else:
            if self.cmd in ('Write', 'Read', 'Status read', 'Burst read', 'Burst write'):
                label = '{}: {}'.format(self.format_command(), name)
            else:
                label = 'Reg ({}) {}'.format(self.cmd, name)
            self.decode_mb_data(pos, ann, data, label)

    def decode_status_reg(self, pos, ann, data, label):
        '''Decodes the data bytes 'data' of a status register at position
        'pos'. The decoded data is prefixed with 'label'.'''
        status = data[0]
        # bit 7 --> CHIP_RDYn
        if status & 0b10000000 == 0b10000000:
            longtext_chiprdy = 'CHIP_RDYn is high! '
        else:
            longtext_chiprdy = ''
        # bits 6:4 --> STATE
        state = (status & 0x70) >> 4
        longtext_state = 'STATE is {}, '.format(status_reg_states[state])
        # bits 3:0 --> FIFO_BYTES_AVAILABLE
        fifo_bytes = status & 0x0F
        if self.cmd in ('Single read', 'Status read', 'Burst read'):
            longtext_fifo = '{} bytes available in RX FIFO'.format(fifo_bytes)
        else:
            longtext_fifo = '{} bytes free in TX FIFO'.format(fifo_bytes)

        text = '{} = {:02X}'.format(label, status)
        longtext = ''.join([text, '; ', longtext_chiprdy, longtext_state, longtext_fifo])
        self.putp2(pos, ann, longtext, text)

    def decode_mb_data(self, pos, ann, data, label):
        '''Decodes the data bytes 'data' of a multibyte command at position
        'pos'. The decoded data is prefixed with 'label'.'''

        def escape(b):
            return '{:02X}'.format(b)

        data = ' '.join([escape(b) for b in data])
        text = '{} = {}'.format(label, data)
        self.putp(pos, ann, text)

    def finish_command(self, pos):
        '''Decodes the remaining data bytes at position 'pos'.'''

        if self.cmd == 'Write':
            self.decode_reg(pos, Ann.SINGLE_WRITE, self.dat, self.mosi_bytes())
        elif self.cmd == 'Burst write':
            self.decode_reg(pos, Ann.BURST_WRITE, self.dat, self.mosi_bytes())
        elif self.cmd == 'Read':
            self.decode_reg(pos, Ann.SINGLE_READ, self.dat, self.miso_bytes())
        elif self.cmd == 'Burst read':
            self.decode_reg(pos, Ann.BURST_READ, self.dat, self.miso_bytes())
        elif self.cmd == 'Strobe':
            self.decode_reg(pos, Ann.STROBE, self.dat, self.mosi_bytes())
        elif self.cmd == 'Status read':
            self.decode_reg(pos, Ann.STATUS_READ, self.dat, self.miso_bytes())
        else:
            self.warn(pos, 'unhandled command')

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
                # the bytes that were sent after the command byte.
                if self.cmd:
                    # Check if we got the minimum number of data bytes
                    # after the command byte.
                    if len(self.mb) < self.min:
                        self.warn((ss, ss), 'missing data bytes')
                    elif self.mb:
                        self.finish_command(Pos(self.ss_mb, self.es_mb))

                self.next()
                self.cs_was_released = True

        elif ptype == 'DATA' and self.cs_was_released:
            mosi, miso = data1, data2
            pos = Pos(ss, es)

            if miso is None or mosi is None:
                self.requirements_met = False
                raise ChannelError('Both MISO and MOSI pins required.')

            if self.first:
                self.first = False
                # First MOSI byte is always the command.
                self.decode_command(pos, mosi)
                # First MISO byte is always the status register.
                self.decode_reg(pos, Ann.STATUS, 'STATUS', [miso])
            else:
                if not self.cmd or len(self.mb) >= self.max:
                    self.warn(pos, 'excess byte')
                else:
                    # Collect the bytes after the command byte.
                    if self.ss_mb == -1:
                        self.ss_mb = ss
                    self.es_mb = es
                    self.mb.append(Data(mosi, miso))
