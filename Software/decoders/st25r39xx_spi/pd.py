##
## This file is part of the libsigrokdecode project.
##
## Copyright (C) 2019-2021 Benjamin Vernoux <bvernoux@gmail.com>
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
## v0.1 - 17 September 2019 B.VERNOUX
### Use ST25R3916 Datasheet DS12484 Rev 1 (January 2019)
## v0.2 - 28 April 2020 B.VERNOUX
### Use ST25R3916 Datasheet DS12484 Rev 2 (December 2019)
## v0.3 - 17 June 2020 B.VERNOUX
### Use ST25R3916 Datasheet DS12484 Rev 3 (04 June 2020)
## v0.4 - 10 Aug 2021 B.VERNOUX
### Fix FIFOR/FIFOW issues with Pulseview (with "Tabular Output View")
### because of FIFO Read/FIFO Write commands, was not returning the
### annotations short name FIFOR/FIFOW

import sigrokdecode as srd
from collections import namedtuple
from common.srdhelper import SrdIntEnum
from .lists import *

Ann = SrdIntEnum.from_str('Ann', 'BURST_READ BURST_WRITE \
    BURST_READB BURST_WRITEB BURST_READT BURST_WRITET \
    DIRECTCMD FIFO_WRITE FIFO_READ STATUS WARN')

Pos = namedtuple('Pos', ['ss', 'es'])
Data = namedtuple('Data', ['mosi', 'miso'])

class Decoder(srd.Decoder):
    api_version = 3
    id = 'st25r39xx_spi'
    name = 'ST25R39xx (SPI mode)'
    longname = 'STMicroelectronics ST25R39xx'
    desc = 'High performance NFC universal device and EMVCo reader protocol.'
    license = 'gplv2+'
    inputs = ['spi']
    outputs = []
    tags = ['IC', 'Wireless/RF']
    annotations = (
        ('Read', 'Burst register read'),
        ('Write', 'Burst register write'),
        ('ReadB', 'Burst register SpaceB read'),
        ('WriteB', 'Burst register SpaceB write'),
        ('ReadT', 'Burst register Test read'),
        ('WriteT', 'Burst register Test write'),
        ('Cmd', 'Direct command'),
        ('FIFOW', 'FIFO write'),
        ('FIFOR', 'FIFO read'),
        ('status_reg', 'Status register'),
        ('warning', 'Warning'),
    )
    annotation_rows = (
        ('regs', 'Regs', (Ann.prefixes('BURST_'))),
        ('cmds', 'Commands', (Ann.DIRECTCMD,)),
        ('data', 'Data', (Ann.prefixes('FIFO_'))),
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
            self.warn(pos, 'Unknown command')
            return

        self.cmd, self.dat, self.min, self.max = c

        if self.cmd == 'Cmd':
            self.putp(pos, Ann.DIRECTCMD, self.format_command())
        else:
            # Don't output anything now, the command is merged with
            # the data bytes following it.
            self.ss_mb = pos.ss

    def format_command(self):
        '''Returns the label for the current command.'''
        if self.cmd in ('Write', 'Read', 'WriteB', 'ReadB', 'WriteT', 'ReadT', 'FIFOW', 'FIFOR'):
            return self.cmd
        if self.cmd == 'Cmd':
            reg = dir_cmd.get(self.dat, 'Unknown direct command')
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
        # previous command was 'Space B'
        if self.cmd == 'Space B':
            if (b & 0xC0) == 0x00:
                return ('WriteB', addr, 1, 99999)
            if (b & 0xC0) == 0x40:
                return ('ReadB', addr, 1, 99999)
            else:
                self.warn(pos, 'Unknown address/command combination')
        # previous command was 'TestAccess'
        elif self.cmd == 'TestAccess':
            if (b & 0xC0) == 0x00:
                return ('WriteT', addr, 1, 99999)
            if (b & 0xC0) == 0x40:
                return ('ReadT', addr, 1, 99999)
            else:
                self.warn(pos, 'Unknown address/command combination')
        else:
            # Space A regs or other operation modes (except Space B)
            # Register Write   0b00xxxxxx 0x00 to 0x3F => 'Write'
            # Register Read    0b01xxxxxx 0x40 to 0x7F => 'Read'
            if (b <= 0x7F):
                if (b & 0xC0) == 0x00:
                    return ('Write', addr, 1, 99999)
                if (b & 0xC0) == 0x40:
                    return ('Read', addr, 1, 99999)
                else:
                    self.warn(pos, 'Unknown address/command combination')
            else:
                # FIFO Load                 0b10000000 0x80 => 'FIFO Write'
                # PT_memory loadA-config    0b10100000 0xA0 => 'Write'
                # PT_memory loadF-config    0b10101000 0xA8 => 'Write'
                # PT_memory loadTSN data    0b10101100 0xAC => 'Write'
                # PT_memory Read            0b10111111 0xBF => 'Read'
                # FIFO Read                 0b10011111 0x9F => 'FIFO Read'
                # Direct Command            0b11xxx1xx 0xC0 to 0xE8 => 'Cmd'
                # Register Space-B Access   0b11111011 0xFB => 'Space B'
                # Register Test Access      0b11111100 0xFC => 'TestAccess'
                if b == 0x80:
                    return ('FIFOW', b, 1, 99999)
                if b == 0xA0:
                    return ('Write', b, 1, 99999)
                if b == 0xA8:
                    return ('Write', b, 1, 99999)
                if b == 0xAC:
                    return ('Write', b, 1, 99999)
                if b == 0xBF:
                    return ('Read', b, 1, 99999)
                if b == 0x9F:
                    return ('FIFOR', b, 1, 99999)
                if (b >= 0x0C and b <= 0xE8) :
                    return ('Cmd', b, 0, 0)
                if b == 0xFB:
                    return ('Space B', b, 0, 0)
                if b == 0xFC:
                    return ('TestAccess', b, 0, 0)
                else:
                    self.warn(pos, 'Unknown address/command combination')

    def decode_reg(self, pos, ann, regid, data):
        '''Decodes a register.
        pos   -- start and end sample numbers of the register
        ann   -- the annotation number that is used to output the register.
        regid -- may be either an integer used as a key for the 'regs'
                 dictionary, or a string directly containing a register name.'
        data  -- the register content.
        '''
        if type(regid) == int:
            if (ann == Ann.FIFO_READ) or (ann == Ann.FIFO_WRITE):
                name = ''
            elif (ann == Ann.BURST_READB) or (ann == Ann.BURST_WRITEB):
                # Get the name of the register.
                if regid not in regsSpaceB:
                    self.warn(pos, 'Unknown register SpaceB')
                    return
                name = '{} ({:02X})'.format(regsSpaceB[regid], regid)
            elif (ann == Ann.BURST_READT) or (ann == Ann.BURST_WRITET):
                # Get the name of the register.
                if regid not in regsTest:
                    self.warn(pos, 'Unknown register Test')
                    return
                name = '{} ({:02X})'.format(regsTest[regid], regid)
            else:
                # Get the name of the register.
                if regid not in regsSpaceA:
                    self.warn(pos, 'Unknown register SpaceA')
                    return
                name = '{} ({:02X})'.format(regsSpaceA[regid], regid)
        else:
            name = regid

        if regid == 'STATUS' and ann == Ann.STATUS:
            label = 'Status'
            self.decode_status_reg(pos, ann, data, label)
        else:
            label = '{}: {}'.format(self.format_command(), name)
        self.decode_mb_data(pos, ann, data, label)

    def decode_status_reg(self, pos, ann, data, label):
        '''Decodes the data bytes 'data' of a status register at position
        'pos'. The decoded data is prefixed with 'label'.'''

    def decode_mb_data(self, pos, ann, data, label):
        '''Decodes the data bytes 'data' of a multibyte command at position
        'pos'. The decoded data is prefixed with 'label'.'''

        def escape(b):
            return '{:02X}'.format(b)

        data = ' '.join([escape(b) for b in data])
        if (ann == Ann.FIFO_WRITE) or (ann == Ann.FIFO_READ):
            text = '{}{}'.format(label, data)
        else:
            text = '{} = {}'.format(label, data)
        self.putp(pos, ann, text)

    def finish_command(self, pos):
        '''Decodes the remaining data bytes at position 'pos'.'''
        if self.cmd == 'Write':
            self.decode_reg(pos, Ann.BURST_WRITE, self.dat, self.mosi_bytes())
        elif self.cmd == 'Read':
            self.decode_reg(pos, Ann.BURST_READ, self.dat, self.miso_bytes())
        elif self.cmd == 'WriteB':
            self.decode_reg(pos, Ann.BURST_WRITEB, self.dat, self.mosi_bytes())
        elif self.cmd == 'ReadB':
            self.decode_reg(pos, Ann.BURST_READB, self.dat, self.miso_bytes())
        elif self.cmd == 'WriteT':
            self.decode_reg(pos, Ann.BURST_WRITET, self.dat, self.mosi_bytes())
        elif self.cmd == 'ReadT':
            self.decode_reg(pos, Ann.BURST_READT, self.dat, self.miso_bytes())
        elif self.cmd == 'FIFOW':
            self.decode_reg(pos, Ann.FIFO_WRITE, self.dat, self.mosi_bytes())
        elif self.cmd == 'FIFOR':
            self.decode_reg(pos, Ann.FIFO_READ, self.dat, self.miso_bytes())
        elif self.cmd == 'Cmd':
            self.decode_reg(pos, Ann.DIRECTCMD, self.dat, self.mosi_bytes())
        else:
            self.warn(pos, 'Unhandled command {}'.format(self.cmd))

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
                        self.warn((ss, ss), 'Missing data bytes')
                    elif self.mb:
                        self.finish_command(Pos(self.ss_mb, self.es_mb))

                self.next()
                self.cs_was_released = True

        elif ptype == 'DATA' and self.cs_was_released:
            mosi, miso = data1, data2
            pos = Pos(ss, es)

            if miso is None or mosi is None:
                self.requirements_met = False
                raise ChannelError('Both MISO and MOSI pins are required.')

            if self.first:
                # Register Space-B Access   0b11111011 0xFB => 'Space B'
                if mosi == 0xFB:
                    self.first = True
                    # First MOSI byte 'Space B' command.
                    self.decode_command(pos, mosi)
                    # First MISO byte is always the status register.
                    #self.decode_reg(pos, ANN_STATUS, 'STATUS', [miso])
                # Register TestAccess Access   0b11111100 0xFC => 'TestAccess'
                elif mosi == 0xFC:
                    self.first = True
                    # First MOSI byte 'TestAccess' command.
                    self.decode_command(pos, mosi)
                    # First MISO byte is always the status register.
                    #self.decode_reg(pos, ANN_STATUS, 'STATUS', [miso])
                else:
                    self.first = False
                    # First MOSI byte is always the command.
                    self.decode_command(pos, mosi)
                    # First MISO byte is always the status register.
                    #self.decode_reg(pos, ANN_STATUS, 'STATUS', [miso])
            else:
                if not self.cmd or len(self.mb) >= self.max:
                    self.warn(pos, 'Excess byte')
                else:
                    # Collect the bytes after the command byte.
                    if self.ss_mb == -1:
                        self.ss_mb = ss
                    self.es_mb = es
                    self.mb.append(Data(mosi, miso))
