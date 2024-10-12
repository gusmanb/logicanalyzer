##
## This file is part of the libsigrokdecode project.
##
## Copyright (C) 2014 Uwe Hermann <uwe@hermann-uwe.de>
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

import copy
import sigrokdecode as srd
from .lists import *

class Decoder(srd.Decoder):
    api_version = 3
    id = 'eeprom24xx'
    name = '24xx EEPROM'
    longname = '24xx I²C EEPROM'
    desc = '24xx series I²C EEPROM protocol.'
    license = 'gplv2+'
    inputs = ['i2c']
    outputs = []
    tags = ['IC', 'Memory']
    options = (
        {'id': 'chip', 'desc': 'Chip', 'default': 'generic',
            'values': tuple(chips.keys())},
        {'id': 'addr_counter', 'desc': 'Initial address counter value',
            'default': 0},
    )
    annotations = (
        # Warnings
        ('warning', 'Warning'),
        # Bits/bytes
        ('control-code', 'Control code'),
        ('address-pin', 'Address pin (A0/A1/A2)'),
        ('rw-bit', 'Read/write bit'),
        ('word-addr-byte', 'Word address byte'),
        ('data-byte', 'Data byte'),
        # Fields
        ('control-word', 'Control word'),
        ('word-addr', 'Word address'),
        ('data', 'Data'),
        # Operations
        ('byte-write', 'Byte write'),
        ('page-write', 'Page write'),
        ('cur-addr-read', 'Current address read'),
        ('random-read', 'Random read'),
        ('seq-random-read', 'Sequential random read'),
        ('seq-cur-addr-read', 'Sequential current address read'),
        ('ack-polling', 'Acknowledge polling'),
        ('set-bank-addr', 'Set bank address'), # SBA. Only 34AA04.
        ('read-bank-addr', 'Read bank address'), # RBA. Only 34AA04.
        ('set-wp', 'Set write protection'), # SWP
        ('clear-all-wp', 'Clear all write protection'), # CWP
        ('read-wp', 'Read write protection status'), # RPS
    )
    annotation_rows = (
        ('bits-bytes', 'Bits/bytes', (1, 2, 3, 4, 5)),
        ('fields', 'Fields', (6, 7, 8)),
        ('ops', 'Operations', tuple(range(9, 21))),
        ('warnings', 'Warnings', (0,)),
    )
    binary = (
        ('binary', 'Binary'),
    )

    def __init__(self):
        self.reset()

    def reset(self):
        self.reset_variables()

    def start(self):
        self.out_ann = self.register(srd.OUTPUT_ANN)
        self.out_binary = self.register(srd.OUTPUT_BINARY)
        self.chip = chips[self.options['chip']]
        self.addr_counter = self.options['addr_counter']

    def putb(self, data):
        self.put(self.ss_block, self.es_block, self.out_ann, data)

    def putbin(self, data):
        self.put(self.ss_block, self.es_block, self.out_binary, data)

    def putbits(self, bit1, bit2, bits, data):
        self.put(bits[bit1][1], bits[bit2][2], self.out_ann, data)

    def reset_variables(self):
        self.state = 'WAIT FOR START'
        self.packets = []
        self.bytebuf = []
        self.is_cur_addr_read = False
        self.is_random_access_read = False
        self.is_seq_random_read = False
        self.is_byte_write = False
        self.is_page_write = False

    def packet_append(self):
        self.packets.append([self.ss, self.es, self.cmd, self.databyte, self.bits])
        if self.cmd in ('DATA READ', 'DATA WRITE'):
            self.bytebuf.append(self.databyte)

    def hexbytes(self, idx):
        return ' '.join(['%02X' % b for b in self.bytebuf[idx:]])

    def put_control_word(self, bits):
        s = ''.join(['%d' % b[0] for b in reversed(bits[4:])])
        self.putbits(7, 4, bits, [1, ['Control code bits: ' + s,
            'Control code: ' + s, 'Ctrl code: ' + s, 'Ctrl code', 'Ctrl', 'C']])
        for i in reversed(range(self.chip['addr_pins'])):
            self.putbits(i + 1, i + 1, bits,
                [2, ['Address bit %d: %d' % (i, bits[i + 1][0]),
                     'Addr bit %d' % i, 'A%d' % i, 'A']])
        s1 = 'read' if bits[0][0] == 1 else 'write'
        s2 = 'R' if bits[0][0] == 1 else 'W'
        self.putbits(0, 0, bits, [3, ['R/W bit: ' + s1, 'R/W', 'RW', s2]])
        self.putbits(7, 0, bits, [6, ['Control word', 'Control', 'CW', 'C']])

    def put_word_addr(self, p):
        if self.chip['addr_bytes'] == 1:
            a = p[1][3]
            self.put(p[1][0], p[1][1], self.out_ann,
                [4, ['Word address byte: %02X' % a, 'Word addr byte: %02X' % a,
                     'Addr: %02X' % a, 'A: %02X' % a, '%02X' % a]])
            self.put(p[1][0], p[1][1], self.out_ann, [7, ['Word address',
                     'Word addr', 'Addr', 'A']])
            self.addr_counter = a
        else:
            a = p[1][3]
            self.put(p[1][0], p[1][1], self.out_ann,
                [4, ['Word address high byte: %02X' % a,
                     'Word addr high byte: %02X' % a,
                     'Addr high: %02X' % a, 'AH: %02X' % a, '%02X' % a]])
            a = p[2][3]
            self.put(p[2][0], p[2][1], self.out_ann,
                [4, ['Word address low byte: %02X' % a,
                     'Word addr low byte: %02X' % a,
                     'Addr low: %02X' % a, 'AL: %02X' % a, '%02X' % a]])
            self.put(p[1][0], p[2][1], self.out_ann, [7, ['Word address',
                     'Word addr', 'Addr', 'A']])
            self.addr_counter = (p[1][3] << 8) | p[2][3]

    def put_data_byte(self, p):
        if self.chip['addr_bytes'] == 1:
            s = '%02X' % self.addr_counter
        else:
            s = '%04X' % self.addr_counter
        self.put(p[0], p[1], self.out_ann, [5, ['Data byte %s: %02X' % \
            (s, p[3]), 'Data byte: %02X' % p[3], \
            'Byte: %02X' % p[3], 'DB: %02X' % p[3], '%02X' % p[3]]])

    def put_data_bytes(self, idx, cls, s):
        for p in self.packets[idx:]:
            self.put_data_byte(p)
            self.addr_counter += 1
        self.put(self.packets[idx][0], self.packets[-1][1], self.out_ann,
            [8, ['Data', 'D']])
        a = ''.join(['%s' % c[0] for c in s.split()]).upper()
        self.putb([cls, ['%s (%s): %s' % (s, self.addr_and_len(), \
                  self.hexbytes(self.chip['addr_bytes'])),
                  '%s (%s)' % (s, self.addr_and_len()), s, a, s[0]]])
        self.putbin([0, bytes(self.bytebuf[self.chip['addr_bytes']:])])

    def addr_and_len(self):
        if self.chip['addr_bytes'] == 1:
            a = '%02X' % self.bytebuf[0]
        else:
            a = '%02X%02X' % tuple(self.bytebuf[:2])
        num_data_bytes = len(self.bytebuf) - self.chip['addr_bytes']
        d = '%d bytes' % num_data_bytes
        if num_data_bytes <= 1:
            d = d[:-1]
        return 'addr=%s, %s' % (a, d)

    def decide_on_seq_or_rnd_read(self):
        if len(self.bytebuf) < 2:
            self.reset_variables()
            return
        if len(self.bytebuf) == 2:
            self.is_random_access_read = True
        else:
            self.is_seq_random_read = True

    def put_operation(self):
        idx = 1 + self.chip['addr_bytes']
        if self.is_byte_write:
            # Byte write: word address, one data byte.
            self.put_word_addr(self.packets)
            self.put_data_bytes(idx, 9, 'Byte write')
        elif self.is_page_write:
            # Page write: word address, two or more data bytes.
            self.put_word_addr(self.packets)
            intitial_addr = self.addr_counter
            self.put_data_bytes(idx, 10, 'Page write')
            num_bytes_to_write = len(self.packets[idx:])
            if num_bytes_to_write > self.chip['page_size']:
                self.putb([0, ['Warning: Wrote %d bytes but page size is '
                               'only %d bytes!' % (num_bytes_to_write,
                               self.chip['page_size'])]])
            page1 = int(intitial_addr / self.chip['page_size'])
            page2 = int((self.addr_counter - 1) / self.chip['page_size'])
            if page1 != page2:
                self.putb([0, ['Warning: Page write crossed page boundary '
                               'from page %d to %d!' % (page1, page2)]])
        elif self.is_cur_addr_read:
            # Current address read: no word address, one data byte.
            self.put_data_byte(self.packets[1])
            self.put(self.packets[1][0], self.packets[-1][1], self.out_ann,
                [8, ['Data', 'D']])
            self.putb([11, ['Current address read: %02X' % self.bytebuf[0],
                       'Current address read', 'Cur addr read', 'CAR', 'C']])
            self.putbin([0, bytes([self.bytebuf[0]])])
            self.addr_counter += 1
        elif self.is_random_access_read:
            # Random access read: word address, one data byte.
            self.put_control_word(self.packets[idx][4])
            self.put_word_addr(self.packets)
            self.put_data_bytes(idx + 1, 12, 'Random access read')
        elif self.is_seq_random_read:
            # Sequential random read: word address, two or more data bytes.
            self.put_control_word(self.packets[idx][4])
            self.put_word_addr(self.packets)
            self.put_data_bytes(idx + 1, 13, 'Sequential random read')

    def handle_wait_for_start(self):
        # Wait for an I²C START condition.
        if self.cmd not in ('START', 'START REPEAT'):
            return
        self.ss_block = self.ss
        self.state = 'GET CONTROL WORD'

    def handle_get_control_word(self):
        # The packet after START must be an ADDRESS READ or ADDRESS WRITE.
        if self.cmd not in ('ADDRESS READ', 'ADDRESS WRITE'):
            self.reset_variables()
            return
        self.packet_append()
        self.put_control_word(self.bits)
        self.state = '%s GET ACK NACK AFTER CONTROL WORD' % self.cmd[8]

    def handle_r_get_ack_nack_after_control_word(self):
        if self.cmd == 'ACK':
            self.state = 'R GET WORD ADDR OR BYTE'
        elif self.cmd == 'NACK':
            self.es_block = self.es
            self.putb([0, ['Warning: No reply from slave!']])
            self.reset_variables()
        else:
            self.reset_variables()

    def handle_r_get_word_addr_or_byte(self):
        if self.cmd == 'STOP':
            self.es_block = self.es
            self.putb([0, ['Warning: Slave replied, but master aborted!']])
            self.reset_variables()
            return
        elif self.cmd != 'DATA READ':
            self.reset_variables()
            return
        self.packet_append()
        self.state = 'R GET ACK NACK AFTER WORD ADDR OR BYTE'

    def handle_r_get_ack_nack_after_word_addr_or_byte(self):
        if self.cmd == 'ACK':
            self.state = 'R GET RESTART'
        elif self.cmd == 'NACK':
            self.is_cur_addr_read = True
            self.state = 'GET STOP AFTER LAST BYTE'
        else:
            self.reset_variables()

    def handle_r_get_restart(self):
        if self.cmd == 'RESTART':
            self.state = 'R READ BYTE'
        else:
            self.reset_variables()

    def handle_r_read_byte(self):
        if self.cmd == 'DATA READ':
            self.packet_append()
            self.state = 'R GET ACK NACK AFTER BYTE WAS READ'
        else:
            self.reset_variables()

    def handle_r_get_ack_nack_after_byte_was_read(self):
        if self.cmd == 'ACK':
            self.state = 'R READ BYTE'
        elif self.cmd == 'NACK':
            # It's either a RANDOM READ or a SEQUENTIAL READ.
            self.state = 'GET STOP AFTER LAST BYTE'
        else:
            self.reset_variables()

    def handle_w_get_ack_nack_after_control_word(self):
        if self.cmd == 'ACK':
            self.state = 'W GET WORD ADDR'
        elif self.cmd == 'NACK':
            self.es_block = self.es
            self.putb([0, ['Warning: No reply from slave!']])
            self.reset_variables()
        else:
            self.reset_variables()

    def handle_w_get_word_addr(self):
        if self.cmd == 'STOP':
            self.es_block = self.es
            self.putb([0, ['Warning: Slave replied, but master aborted!']])
            self.reset_variables()
            return
        elif self.cmd != 'DATA WRITE':
            self.reset_variables()
            return
        self.packet_append()
        self.state = 'W GET ACK AFTER WORD ADDR'

    def handle_w_get_ack_after_word_addr(self):
        if self.cmd == 'ACK':
            self.state = 'W DETERMINE EEPROM READ OR WRITE'
        else:
            self.reset_variables()

    def handle_w_determine_eeprom_read_or_write(self):
        if self.cmd == 'START REPEAT':
            # It's either a RANDOM ACCESS READ or SEQUENTIAL RANDOM READ.
            self.state = 'R2 GET CONTROL WORD'
        elif self.cmd == 'DATA WRITE':
            self.packet_append()
            self.state = 'W GET ACK NACK AFTER BYTE WAS WRITTEN'
        else:
            self.reset_variables()

    def handle_w_write_byte(self):
        if self.cmd == 'DATA WRITE':
            self.packet_append()
            self.state = 'W GET ACK NACK AFTER BYTE WAS WRITTEN'
        elif self.cmd == 'STOP':
            if len(self.bytebuf) < 2:
                self.reset_variables()
                return
            self.es_block = self.es
            if len(self.bytebuf) == 2:
                self.is_byte_write = True
            else:
                self.is_page_write = True
            self.put_operation()
            self.reset_variables()
        elif self.cmd == 'START REPEAT':
            # It's either a RANDOM ACCESS READ or SEQUENTIAL RANDOM READ.
            self.state = 'R2 GET CONTROL WORD'
        else:
            self.reset_variables()

    def handle_w_get_ack_nack_after_byte_was_written(self):
        if self.cmd == 'ACK':
            self.state = 'W WRITE BYTE'
        else:
            self.reset_variables()

    def handle_r2_get_control_word(self):
        if self.cmd == 'ADDRESS READ':
            self.packet_append()
            self.state = 'R2 GET ACK AFTER ADDR READ'
        else:
            self.reset_variables()

    def handle_r2_get_ack_after_addr_read(self):
        if self.cmd == 'ACK':
            self.state = 'R2 READ BYTE'
        else:
            self.reset_variables()

    def handle_r2_read_byte(self):
        if self.cmd == 'DATA READ':
            self.packet_append()
            self.state = 'R2 GET ACK NACK AFTER BYTE WAS READ'
        elif self.cmd == 'STOP':
            self.decide_on_seq_or_rnd_read()
            self.es_block = self.es
            self.putb([0, ['Warning: STOP expected after a NACK (not ACK)']])
            self.put_operation()
            self.reset_variables()
        else:
            self.reset_variables()

    def handle_r2_get_ack_nack_after_byte_was_read(self):
        if self.cmd == 'ACK':
            self.state = 'R2 READ BYTE'
        elif self.cmd == 'NACK':
            self.decide_on_seq_or_rnd_read()
            self.state = 'GET STOP AFTER LAST BYTE'
        else:
            self.reset_variables()

    def handle_get_stop_after_last_byte(self):
        if self.cmd == 'STOP':
            self.es_block = self.es
            self.put_operation()
            self.reset_variables()
        elif self.cmd == 'START REPEAT':
            self.es_block = self.es
            self.putb([0, ['Warning: STOP expected (not RESTART)']])
            self.put_operation()
            self.reset_variables()
            self.ss_block = self.ss
            self.state = 'GET CONTROL WORD'
        else:
            self.reset_variables()

    def decode(self, ss, es, data):
        cmd, _ = data

        # Collect the 'BITS' packet, then return. The next packet is
        # guaranteed to belong to these bits we just stored.
        if cmd == 'BITS':
            _, databits = data
            self.bits = copy.deepcopy(databits)
            return

        # Store the start/end samples of this I²C packet. Deep copy
        # caller's data, assuming that implementation details of the
        # above complex methods can access the data after returning
        # from the .decode() invocation, with the data having become
        # invalid by that time of access. This conservative approach
        # can get weakened after close inspection of those methods.
        self.ss, self.es = ss, es
        _, databyte = data
        databyte = copy.deepcopy(databyte)
        self.cmd, self.databyte = cmd, databyte

        # State machine.
        s = 'handle_%s' % self.state.lower().replace(' ', '_')
        handle_state = getattr(self, s)
        handle_state()
