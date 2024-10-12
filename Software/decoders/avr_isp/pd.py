##
## This file is part of the libsigrokdecode project.
##
## Copyright (C) 2012-2014 Uwe Hermann <uwe@hermann-uwe.de>
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
from .parts import *

class Ann:
    PE, RSB0, RSB1, RSB2, CE, RFB, RHFB, REFB, \
    RLB, REEM, RP, LPMP, WP, WARN, DEV, = range(15)

VENDOR_CODE_ATMEL = 0x1e

class Decoder(srd.Decoder):
    api_version = 3
    id = 'avr_isp'
    name = 'AVR ISP'
    longname = 'AVR In-System Programming'
    desc = 'Atmel AVR In-System Programming (ISP) protocol.'
    license = 'gplv2+'
    inputs = ['spi']
    outputs = []
    tags = ['Debug/trace']
    annotations = (
        ('pe', 'Programming enable'),
        ('rsb0', 'Read signature byte 0'),
        ('rsb1', 'Read signature byte 1'),
        ('rsb2', 'Read signature byte 2'),
        ('ce', 'Chip erase'),
        ('rfb', 'Read fuse bits'),
        ('rhfb', 'Read high fuse bits'),
        ('refb', 'Read extended fuse bits'),
        ('rlb', 'Read lock bits'),
        ('reem', 'Read EEPROM memory'),
        ('rp', 'Read program memory'),
        ('lpmp' , 'Load program memory page'),
        ('wp', 'Write program memory'),
        ('warning', 'Warning'),
        ('dev', 'Device'),
    )
    annotation_rows = (
        ('commands', 'Commands', (Ann.PE, Ann.RSB0, Ann.RSB1, Ann.RSB2,
            Ann.CE, Ann.RFB, Ann.RHFB, Ann.REFB,
            Ann.RLB, Ann.REEM, Ann.RP, Ann.LPMP, Ann.WP,)),
        ('warnings', 'Warnings', (Ann.WARN,)),
        ('devs', 'Devices', (Ann.DEV,)),
    )

    def __init__(self):
        self.reset()

    def reset(self):
        self.state = 'IDLE'
        self.mosi_bytes, self.miso_bytes = [], []
        self.ss_cmd, self.es_cmd = 0, 0
        self.xx, self.yy, self.zz, self.mm = 0, 0, 0, 0
        self.ss_device = None

    def start(self):
        self.out_ann = self.register(srd.OUTPUT_ANN)

    def putx(self, data):
        self.put(self.ss_cmd, self.es_cmd, self.out_ann, data)

    def handle_cmd_programming_enable(self, cmd, ret):
        # Programming enable.
        # Note: The chip doesn't send any ACK for 'Programming enable'.
        self.putx([Ann.PE, ['Programming enable']])

        # Sanity check on reply.
        if ret[1:4] != [0xac, 0x53, cmd[2]]:
            self.putx([Ann.WARN, ['Warning: Unexpected bytes in reply!']])

    def handle_cmd_read_signature_byte_0x00(self, cmd, ret):
        # Signature byte 0x00: vendor code.
        self.vendor_code = ret[3]
        v = vendor_code[self.vendor_code]
        self.putx([Ann.RSB0, ['Vendor code: 0x%02x (%s)' % (ret[3], v)]])

        # Store for later.
        self.xx = cmd[1] # Same as ret[2].
        self.yy = cmd[3]
        self.zz = ret[0]

        # Sanity check on reply.
        if ret[1] != 0x30 or ret[2] != cmd[1]:
            self.putx([Ann.WARN, ['Warning: Unexpected bytes in reply!']])

        # Sanity check for the vendor code.
        if self.vendor_code != VENDOR_CODE_ATMEL:
            self.putx([Ann.WARN, ['Warning: Vendor code was not 0x1e (Atmel)!']])

    def handle_cmd_read_signature_byte_0x01(self, cmd, ret):
        # Signature byte 0x01: part family and memory size.
        self.part_fam_flash_size = ret[3]
        self.putx([Ann.RSB1, ['Part family / memory size: 0x%02x' % ret[3]]])

        # Store for later.
        self.mm = cmd[3]
        self.ss_device = self.ss_cmd

        # Sanity check on reply.
        if ret[1] != 0x30 or ret[2] != cmd[1] or ret[0] != self.yy:
            self.putx([Ann.WARN, ['Warning: Unexpected bytes in reply!']])

    def handle_cmd_read_signature_byte_0x02(self, cmd, ret):
        # Signature byte 0x02: part number.
        self.part_number = ret[3]
        self.putx([Ann.RSB2, ['Part number: 0x%02x' % ret[3]]])

        # Part name if known
        key = (self.part_fam_flash_size, self.part_number)
        if key in part:
            p = part[key]
            data = [Ann.DEV, ['Device: Atmel %s' % p]]
            self.put(self.ss_device, self.es_cmd, self.out_ann, data)

        # Sanity check on reply.
        if ret[1] != 0x30 or ret[2] != self.xx or ret[0] != self.mm:
            self.putx([Ann.WARN, ['Warning: Unexpected bytes in reply!']])

        self.xx, self.yy, self.zz, self.mm = 0, 0, 0, 0

    def handle_cmd_chip_erase(self, cmd, ret):
        # Chip erase (erases both flash an EEPROM).
        # Upon successful chip erase, the lock bits will also be erased.
        # The only way to end a Chip Erase cycle is to release RESET#.
        self.putx([Ann.CE, ['Chip erase']])

        # TODO: Check/handle RESET#.

        # Sanity check on reply.
        bit = (ret[2] & (1 << 7)) >> 7
        if ret[1] != 0xac or bit != 1 or ret[3] != cmd[2]:
            self.putx([Ann.WARN, ['Warning: Unexpected bytes in reply!']])

    def handle_cmd_read_fuse_bits(self, cmd, ret):
        # Read fuse bits.
        self.putx([Ann.RFB, ['Read fuse bits: 0x%02x' % ret[3]]])

        # TODO: Decode fuse bits.
        # TODO: Sanity check on reply.

    def handle_cmd_read_fuse_high_bits(self, cmd, ret):
        # Read fuse high bits.
        self.putx([Ann.RHFB, ['Read fuse high bits: 0x%02x' % ret[3]]])

        # TODO: Decode fuse bits.
        # TODO: Sanity check on reply.

    def handle_cmd_read_extended_fuse_bits(self, cmd, ret):
        # Read extended fuse bits.
        self.putx([Ann.REFB, ['Read extended fuse bits: 0x%02x' % ret[3]]])

        # TODO: Decode fuse bits.
        # TODO: Sanity check on reply.

    def handle_cmd_read_lock_bits(self, cmd, ret):
        # Read lock bits
        self.putx([Ann.RLB, ['Read lock bits: 0x%02x' % ret[3]]])

    def handle_cmd_read_eeprom_memory(self, cmd, ret):
        # Read EEPROM Memory
        _addr = ((cmd[1] & 1) << 8) + cmd[2]
        self.putx([Ann.REEM, ['Read EEPROM Memory: [0x%03x]: 0x%02x' % (_addr, ret[3])]])

    def handle_cmd_read_program_memory(self, cmd, ret):
        # Read Program Memory
        _HL = 'Low'
        _H = 'L'
        if cmd[0] & 0x08:
            _HL = 'High'
            _H = 'H'
        _addr = ((cmd[1] & 0x0f) << 8) + cmd[2]
        self.putx([Ann.RP, [
            'Read program memory %s: [0x%03x]: 0x%02x' % (_HL, _addr, ret[3]),
            '[%03x%s]:%02x' % (_addr, _H, ret[3]),
            '%02x' % ret[3]
        ]])

    def handle_cmd_load_program_memory_page(self, cmd, ret):
        # Load Program Memory Page
        _HL = 'Low'
        _H = 'L'
        if cmd[0] & 0x08:
            _HL = 'High'
            _H = 'H'
        _addr = cmd[2] & 0x1F
        self.putx([Ann.LPMP, [
            'Load program memory page %s: [0x%03x]: 0x%02x' % (_HL, _addr, cmd[3]),
            '[%03x%s]=%02x' % (_addr, _H, cmd[3]),
            '%02x' % cmd[3]
        ]])

    def handle_cmd_write_program_memory_page(self, cmd, ret):
        # Write Program Memory Page
        _addr = ((cmd[1] & 0x0F) << 3) + (cmd[2] << 5)
        self.putx([Ann.WP, ['Write program memory page: 0x%02x' % _addr]])

    def handle_command(self, cmd, ret):
        if cmd[:2] == [0xac, 0x53]:
            self.handle_cmd_programming_enable(cmd, ret)
        elif cmd[0] == 0xac and (cmd[1] & (1 << 7)) == (1 << 7):
            self.handle_cmd_chip_erase(cmd, ret)
        elif cmd[:3] == [0x50, 0x00, 0x00]:
            self.handle_cmd_read_fuse_bits(cmd, ret)
        elif cmd[:3] == [0x58, 0x08, 0x00]:
            self.handle_cmd_read_fuse_high_bits(cmd, ret)
        elif cmd[:3] == [0x50, 0x08, 0x00]:
            self.handle_cmd_read_extended_fuse_bits(cmd, ret)
        elif cmd[0] == 0x30 and cmd[2] == 0x00:
            self.handle_cmd_read_signature_byte_0x00(cmd, ret)
        elif cmd[0] == 0x30 and cmd[2] == 0x01:
            self.handle_cmd_read_signature_byte_0x01(cmd, ret)
        elif cmd[0] == 0x30 and cmd[2] == 0x02:
            self.handle_cmd_read_signature_byte_0x02(cmd, ret)
        elif cmd[:2] == [0x58, 0x00]:
            self.handle_cmd_read_lock_bits(cmd,ret)
        elif cmd[0] == 0xa0 and (cmd[1] & (3 << 6)) == (0 << 6):
            self.handle_cmd_read_eeprom_memory(cmd, ret)
        elif (cmd[0] == 0x20 or cmd[0] == 0x28) and ((cmd[1] & 0xf0) == 0x00):
            self.handle_cmd_read_program_memory(cmd, ret)
        elif (cmd[0] == 0x40 or cmd[0] == 0x48) and ((cmd[1] & 0xf0) == 0x00):
            self.handle_cmd_load_program_memory_page(cmd, ret)
        elif (cmd[0] == 0x4C and ((cmd[1] & 0xf0) == 0x00)):
            self.handle_cmd_write_program_memory_page(cmd, ret)
        else:
            c = '%02x %02x %02x %02x' % tuple(cmd)
            r = '%02x %02x %02x %02x' % tuple(ret)
            self.putx([Ann.WARN, ['Unknown command: %s (reply: %s)!' % (c, r)]])

    def decode(self, ss, es, data):
        ptype, mosi, miso = data

        # For now, only use DATA and BITS packets.
        if ptype not in ('DATA', 'BITS'):
            return

        # Store the individual bit values and ss/es numbers. The next packet
        # is guaranteed to be a 'DATA' packet belonging to this 'BITS' one.
        if ptype == 'BITS':
            self.miso_bits, self.mosi_bits = miso, mosi
            return

        self.ss, self.es = ss, es

        if len(self.mosi_bytes) == 0:
            self.ss_cmd = ss

        # Append new bytes.
        self.mosi_bytes.append(mosi)
        self.miso_bytes.append(miso)

        # All commands consist of 4 bytes.
        if len(self.mosi_bytes) < 4:
            return

        self.es_cmd = es

        self.handle_command(self.mosi_bytes, self.miso_bytes)

        self.mosi_bytes = []
        self.miso_bytes = []
