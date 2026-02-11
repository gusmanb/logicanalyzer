##
## This file is part of the libsigrokdecode project.
##
## Copyright (C) 2011-2020 Uwe Hermann <uwe@hermann-uwe.de>
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
import re
from common.srdhelper import SrdIntEnum
from .lists import *

L = len(cmds)

a = [re.sub(r'\/', '_', c[0]).replace('2READ', 'READ2X') for c in cmds.values()] + ['BIT', 'FIELD', 'WARN']
Ann = SrdIntEnum.from_list('Ann', a)

def cmd_annotation_classes():
    return tuple([tuple([cmd[0].lower(), cmd[1]]) for cmd in cmds.values()])

def decode_dual_bytes(sio0, sio1):
    # Given a byte in SIO0 (MOSI) of even bits and a byte in
    # SIO1 (MISO) of odd bits, return a tuple of two bytes.
    def combine_byte(even, odd):
        result = 0
        for bit in range(4):
            if even & (1 << bit):
                result |= 1 << (bit*2)
            if odd & (1 << bit):
                result |= 1 << ((bit*2) + 1)
        return result
    return (combine_byte(sio0 >> 4, sio1 >> 4), combine_byte(sio0, sio1))

def decode_status_reg(data):
    # TODO: Additional per-bit(s) self.put() calls with correct start/end.

    # Bits[0:0]: WIP (write in progress)
    s = 'W' if (data & (1 << 0)) else 'No w'
    ret = '%srite operation in progress.\n' % s

    # Bits[1:1]: WEL (write enable latch)
    s = '' if (data & (1 << 1)) else 'not '
    ret += 'Internal write enable latch is %sset.\n' % s

    # Bits[5:2]: Block protect bits
    # TODO: More detailed decoding (chip-dependent).
    ret += 'Block protection bits (BP3-BP0): 0x%x.\n' % ((data & 0x3c) >> 2)

    # Bits[6:6]: Continuously program mode (CP mode)
    s = '' if (data & (1 << 6)) else 'not '
    ret += 'Device is %sin continuously program mode (CP mode).\n' % s

    # Bits[7:7]: SRWD (status register write disable)
    s = 'not ' if (data & (1 << 7)) else ''
    ret += 'Status register writes are %sallowed.\n' % s

    return ret

class Decoder(srd.Decoder):
    api_version = 3
    id = 'spiflash'
    name = 'SPI flash/EEPROM'
    longname = 'SPI flash/EEPROM chips'
    desc = 'xx25 series SPI (NOR) flash/EEPROM chip protocol.'
    license = 'gplv2+'
    inputs = ['spi']
    outputs = []
    tags = ['IC', 'Memory']
    annotations = cmd_annotation_classes() + (
        ('bit', 'Bit'),
        ('field', 'Field'),
        ('warning', 'Warning'),
    )
    annotation_rows = (
        ('bits', 'Bits', (L + 0,)),
        ('fields', 'Fields', (L + 1,)),
        ('commands', 'Commands', tuple(range(len(cmds)))),
        ('warnings', 'Warnings', (L + 2,)),
    )
    options = (
        {'id': 'chip', 'desc': 'Chip', 'default': tuple(chips.keys())[0],
            'values': tuple(chips.keys())},
        {'id': 'format', 'desc': 'Data format', 'default': 'hex',
            'values': ('hex', 'ascii')},
    )

    def __init__(self):
        self.reset()

    def reset(self):
        self.device_id = -1
        self.on_end_transaction = None
        self.end_current_transaction()
        self.writestate = 0

        # Build dict mapping command keys to handler functions. Each
        # command in 'cmds' (defined in lists.py) has a matching
        # handler self.handle_<shortname>.
        def get_handler(cmd):
            s = 'handle_%s' % cmds[cmd][0].lower().replace('/', '_')
            return getattr(self, s)
        self.cmd_handlers = dict((cmd, get_handler(cmd)) for cmd in cmds.keys())

    def end_current_transaction(self):
        if self.on_end_transaction is not None: # Callback for CS# transition.
            self.on_end_transaction()
            self.on_end_transaction = None
        self.state = None
        self.cmdstate = 1
        self.addr = 0
        self.data = []

    def start(self):
        self.out_ann = self.register(srd.OUTPUT_ANN)
        self.chip = chips[self.options['chip']]
        self.vendor = self.options['chip'].split('_')[0]

    def putx(self, data):
        # Simplification, most annotations span exactly one SPI byte/packet.
        self.put(self.ss, self.es, self.out_ann, data)

    def putf(self, data):
        self.put(self.ss_field, self.es_field, self.out_ann, data)

    def putc(self, data):
        self.put(self.ss_cmd, self.es_cmd, self.out_ann, data)

    def device(self):
        return device_name[self.vendor].get(self.device_id, 'Unknown')

    def vendor_device(self):
        return '%s %s' % (self.chip['vendor'], self.device())

    def cmd_ann_list(self):
        x, s = cmds[self.state][0], cmds[self.state][1]
        return ['Command: %s (%s)' % (s, x), 'Command: %s' % s,
                'Cmd: %s' % s, 'Cmd: %s' % x, x]

    def cmd_vendor_dev_list(self):
        c, d = cmds[self.state], 'Device = %s' % self.vendor_device()
        return ['%s (%s): %s' % (c[1], c[0], d), '%s: %s' % (c[1], d),
                '%s: %s' % (c[0], d), d, self.vendor_device()]

    def emit_cmd_byte(self):
        self.ss_cmd = self.ss
        self.putx([Ann.FIELD, self.cmd_ann_list()])
        self.addr = 0

    def emit_addr_bytes(self, mosi):
        self.addr |= (mosi << ((4 - self.cmdstate) * 8))
        b = ((3 - (self.cmdstate - 2)) * 8) - 1
        self.putx([Ann.BIT,
            ['Address bits %d..%d: 0x%02x' % (b, b - 7, mosi),
             'Addr bits %d..%d: 0x%02x' % (b, b - 7, mosi),
             'Addr bits %d..%d' % (b, b - 7), 'A%d..A%d' % (b, b - 7)]])
        if self.cmdstate == 2:
            self.ss_field = self.ss
        if self.cmdstate == 4:
            self.es_field = self.es
            self.putf([Ann.FIELD, ['Address: 0x%06x' % self.addr,
                'Addr: 0x%06x' % self.addr, '0x%06x' % self.addr]])

    def handle_wren(self, mosi, miso):
        self.putx([Ann.WREN, self.cmd_ann_list()])
        self.writestate = 1

    def handle_wrdi(self, mosi, miso):
        self.putx([Ann.WRDI, self.cmd_ann_list()])
        self.writestate = 0

    def handle_rdid(self, mosi, miso):
        if self.cmdstate == 1:
            # Byte 1: Master sends command ID.
            self.emit_cmd_byte()
        elif self.cmdstate == 2:
            # Byte 2: Slave sends the JEDEC manufacturer ID.
            self.putx([Ann.FIELD, ['Manufacturer ID: 0x%02x' % miso]])
        elif self.cmdstate == 3:
            # Byte 3: Slave sends the memory type.
            self.putx([Ann.FIELD, ['Memory type: 0x%02x' % miso]])
        elif self.cmdstate == 4:
            # Byte 4: Slave sends the device ID.
            self.device_id = miso
            self.putx([Ann.FIELD, ['Device ID: 0x%02x' % miso]])

        if self.cmdstate == 4:
            self.es_cmd = self.es
            self.putc([Ann.RDID, self.cmd_vendor_dev_list()])
            self.state = None
        else:
            self.cmdstate += 1

    def handle_rdsr(self, mosi, miso):
        # Read status register: Master asserts CS#, sends RDSR command,
        # reads status register byte. If CS# is kept asserted, the status
        # register can be read continuously / multiple times in a row.
        # When done, the master de-asserts CS# again.
        if self.cmdstate == 1:
            # Byte 1: Master sends command ID.
            self.emit_cmd_byte()
        elif self.cmdstate >= 2:
            # Bytes 2-x: Slave sends status register as long as master clocks.
            self.es_cmd = self.es
            self.putx([Ann.BIT, [decode_status_reg(miso)]])
            self.putx([Ann.FIELD, ['Status register']])
            self.putc([Ann.RDSR, self.cmd_ann_list()])
            # Set write latch state.
            self.writestate = 1 if (miso & (1 << 1)) else 0
        self.cmdstate += 1

    def handle_rdsr2(self, mosi, miso):
        # Read status register 2: Master asserts CS#, sends RDSR2 command,
        # reads status register 2 byte. If CS# is kept asserted, the status
        # register 2 can be read continuously / multiple times in a row.
        # When done, the master de-asserts CS# again.
        if self.cmdstate == 1:
            # Byte 1: Master sends command ID.
            self.emit_cmd_byte()
        elif self.cmdstate >= 2:
            # Bytes 2-x: Slave sends status register 2 as long as master clocks.
            self.es_cmd = self.es
            # TODO: Decode status register 2 correctly.
            self.putx([Ann.BIT, [decode_status_reg(miso)]])
            self.putx([Ann.FIELD, ['Status register 2']])
            self.putc([Ann.RDSR2, self.cmd_ann_list()])
        self.cmdstate += 1

    def handle_wrsr(self, mosi, miso):
        # Write status register: Master asserts CS#, sends WRSR command,
        # writes 1 or 2 status register byte(s).
        # When done, the master de-asserts CS# again. If this doesn't happen
        # the WRSR command will not be executed.
        if self.cmdstate == 1:
            # Byte 1: Master sends command ID.
            self.emit_cmd_byte()
        elif self.cmdstate == 2:
            # Byte 2: Master sends status register 1.
            self.putx([Ann.BIT, [decode_status_reg(mosi)]])
            self.putx([Ann.FIELD, ['Status register 1']])
            # Set write latch state.
            self.writestate = 1 if (miso & (1 << 1)) else 0
        elif self.cmdstate == 3:
            # Byte 3: Master sends status register 2.
            # TODO: Decode status register 2 correctly.
            self.putx([Ann.BIT, [decode_status_reg(mosi)]])
            self.putx([Ann.FIELD, ['Status register 2']])
            self.es_cmd = self.es
            self.putc([Ann.WRSR, self.cmd_ann_list()])
        self.cmdstate += 1

    def handle_read(self, mosi, miso):
        # Read data bytes: Master asserts CS#, sends READ command, sends
        # 3-byte address, reads >= 1 data bytes, de-asserts CS#.
        if self.cmdstate == 1:
            # Byte 1: Master sends command ID.
            self.emit_cmd_byte()
        elif self.cmdstate in (2, 3, 4):
            # Bytes 2/3/4: Master sends read address (24bits, MSB-first).
            self.emit_addr_bytes(mosi)
        elif self.cmdstate >= 5:
            # Bytes 5-x: Master reads data bytes (until CS# de-asserted).
            self.es_field = self.es # Will be overwritten for each byte.
            if self.cmdstate == 5:
                self.ss_field = self.ss
                self.on_end_transaction = lambda: self.output_data_block('Data', Ann.READ)
            self.data.append(miso)
        self.cmdstate += 1

    def handle_write_common(self, mosi, miso, ann):
        # Write data bytes: Master asserts CS#, sends WRITE command, sends
        # 3-byte address, writes >= 1 data bytes, de-asserts CS#.
        if self.cmdstate == 1:
            # Byte 1: Master sends command ID.
            self.emit_cmd_byte()
            if self.writestate == 0:
                self.putc([Ann.WARN, ['Warning: WREN might be missing']])
        elif self.cmdstate in (2, 3, 4):
            # Bytes 2/3/4: Master sends write address (24bits, MSB-first).
            self.emit_addr_bytes(mosi)
        elif self.cmdstate >= 5:
            # Bytes 5-x: Master writes data bytes (until CS# de-asserted).
            self.es_field = self.es # Will be overwritten for each byte.
            if self.cmdstate == 5:
                self.ss_field = self.ss
                self.on_end_transaction = lambda: self.output_data_block('Data', ann)
            self.data.append(mosi)
        self.cmdstate += 1

    def handle_write1(self, mosi, miso):
        self.handle_write_common(mosi, miso, Ann.WRITE1)

    def handle_write2(self, mosi, miso):
        self.handle_write_common(mosi, miso, Ann.WRITE2)

    def handle_fast_read(self, mosi, miso):
        # Fast read: Master asserts CS#, sends FAST READ command, sends
        # 3-byte address + 1 dummy byte, reads >= 1 data bytes, de-asserts CS#.
        if self.cmdstate == 1:
            # Byte 1: Master sends command ID.
            self.emit_cmd_byte()
        elif self.cmdstate in (2, 3, 4):
            # Bytes 2/3/4: Master sends read address (24bits, MSB-first).
            self.emit_addr_bytes(mosi)
        elif self.cmdstate == 5:
            self.putx([Ann.BIT, ['Dummy byte: 0x%02x' % mosi]])
        elif self.cmdstate >= 6:
            # Bytes 6-x: Master reads data bytes (until CS# de-asserted).
            self.es_field = self.es # Will be overwritten for each byte.
            if self.cmdstate == 6:
                self.ss_field = self.ss
                self.on_end_transaction = lambda: self.output_data_block('Data', Ann.FAST_READ)
            self.data.append(miso)
        self.cmdstate += 1

    def handle_2read(self, mosi, miso):
        # 2x I/O read (fast read dual I/O): Master asserts CS#, sends 2READ
        # command, sends 3-byte address + 1 dummy byte, reads >= 1 data bytes,
        # de-asserts CS#. All data after the command is sent via two I/O pins.
        # MOSI = SIO0 = even bits, MISO = SIO1 = odd bits.
        if self.cmdstate != 1:
            b1, b2 = decode_dual_bytes(mosi, miso)
        if self.cmdstate == 1:
            # Byte 1: Master sends command ID.
            self.emit_cmd_byte()
        elif self.cmdstate == 2:
            # Bytes 2/3(/4): Master sends read address (24bits, MSB-first).
            # Handle bytes 2 and 3 here.
            self.emit_addr_bytes(b1)
            self.cmdstate = 3
            self.emit_addr_bytes(b2)
        elif self.cmdstate == 4:
            # Byte 5: Dummy byte. Also handle byte 4 (address LSB) here.
            self.emit_addr_bytes(b1)
            self.cmdstate = 5
            self.putx([Ann.BIT, ['Dummy byte: 0x%02x' % b2]])
        elif self.cmdstate >= 6:
            # Bytes 6-x: Master reads data bytes (until CS# de-asserted).
            self.es_field = self.es # Will be overwritten for each byte.
            if self.cmdstate == 6:
                self.ss_field = self.ss
                self.on_end_transaction = lambda: self.output_data_block('Data', Ann.READ2X)
            self.data.append(b1)
            self.data.append(b2)
        self.cmdstate += 1

    def handle_status(self, mosi, miso):
        if self.cmdstate == 1:
            # Byte 1: Master sends command ID.
            self.emit_cmd_byte()
            self.on_end_transaction = lambda: self.putc([Ann.STATUS, [cmds[self.state][1]]])
        else:
            # Will be overwritten for each byte.
            self.es_cmd = self.es
            self.es_field = self.es
            if self.cmdstate == 2:
                self.ss_field = self.ss
            self.putx([Ann.BIT, ['Status register byte %d: 0x%02x' % ((self.cmdstate % 2) + 1, miso)]])
        self.cmdstate += 1

    # TODO: Warn/abort if we don't see the necessary amount of bytes.
    def handle_se(self, mosi, miso):
        if self.cmdstate == 1:
            # Byte 1: Master sends command ID.
            self.emit_cmd_byte()
            if self.writestate == 0:
                self.putx([Ann.WARN, ['Warning: WREN might be missing']])
        elif self.cmdstate in (2, 3, 4):
            # Bytes 2/3/4: Master sends sector address (24bits, MSB-first).
            self.emit_addr_bytes(mosi)

        if self.cmdstate == 4:
            self.es_cmd = self.es
            d = 'Erase sector %d (0x%06x)' % (self.addr, self.addr)
            self.putc([Ann.SE, [d]])
            # TODO: Max. size depends on chip, check that too if possible.
            if self.addr % 4096 != 0:
                # Sector addresses must be 4K-aligned (same for all 3 chips).
                self.putc([Ann.WARN, ['Warning: Invalid sector address!']])
            self.state = None
        else:
            self.cmdstate += 1

    def handle_be(self, mosi, miso):
        pass # TODO

    def handle_ce(self, mosi, miso):
        self.putx([Ann.CE, self.cmd_ann_list()])
        if self.writestate == 0:
            self.putx([Ann.WARN, ['Warning: WREN might be missing']])

    def handle_ce2(self, mosi, miso):
        self.putx([Ann.CE2, self.cmd_ann_list()])
        if self.writestate == 0:
            self.putx([Ann.WARN, ['Warning: WREN might be missing']])

    def handle_pp(self, mosi, miso):
        # Page program: Master asserts CS#, sends PP command, sends 3-byte
        # page address, sends >= 1 data bytes, de-asserts CS#.
        if self.cmdstate == 1:
            # Byte 1: Master sends command ID.
            self.emit_cmd_byte()
        elif self.cmdstate in (2, 3, 4):
            # Bytes 2/3/4: Master sends page address (24bits, MSB-first).
            self.emit_addr_bytes(mosi)
        elif self.cmdstate >= 5:
            # Bytes 5-x: Master sends data bytes (until CS# de-asserted).
            self.es_field = self.es # Will be overwritten for each byte.
            if self.cmdstate == 5:
                self.ss_field = self.ss
                self.on_end_transaction = lambda: self.output_data_block('Data', Ann.PP)
            self.data.append(mosi)
        self.cmdstate += 1

    def handle_cp(self, mosi, miso):
        pass # TODO

    def handle_dp(self, mosi, miso):
        pass # TODO

    def handle_rdp_res(self, mosi, miso):
        if self.cmdstate == 1:
            # Byte 1: Master sends command ID.
            self.emit_cmd_byte()
        elif self.cmdstate in (2, 3, 4):
            # Bytes 2/3/4: Master sends three dummy bytes.
            self.putx([Ann.FIELD, ['Dummy byte: %02x' % mosi]])
        elif self.cmdstate == 5:
            # Byte 5: Slave sends device ID.
            self.es_cmd = self.es
            self.device_id = miso
            self.putx([Ann.FIELD, ['Device ID: %s' % self.device()]])
            d = 'Device = %s' % self.vendor_device()
            self.putc([Ann.RDP_RES, self.cmd_vendor_dev_list()])
            self.state = None
        self.cmdstate += 1

    def handle_rems(self, mosi, miso):
        if self.cmdstate == 1:
            # Byte 1: Master sends command ID.
            self.emit_cmd_byte()
        elif self.cmdstate in (2, 3):
            # Bytes 2/3: Master sends two dummy bytes.
            self.putx([Ann.FIELD, ['Dummy byte: 0x%02x' % mosi]])
        elif self.cmdstate == 4:
            # Byte 4: Master sends 0x00 or 0x01.
            # 0x00: Master wants manufacturer ID as first reply byte.
            # 0x01: Master wants device ID as first reply byte.
            self.manufacturer_id_first = True if (mosi == 0x00) else False
            d = 'manufacturer' if (mosi == 0x00) else 'device'
            self.putx([Ann.FIELD, ['Master wants %s ID first' % d]])
        elif self.cmdstate == 5:
            # Byte 5: Slave sends manufacturer ID (or device ID).
            self.ids = [miso]
            d = 'Manufacturer' if self.manufacturer_id_first else 'Device'
            self.putx([Ann.FIELD, ['%s ID: 0x%02x' % (d, miso)]])
        elif self.cmdstate == 6:
            # Byte 6: Slave sends device ID (or manufacturer ID).
            self.ids.append(miso)
            d = 'Device' if self.manufacturer_id_first else 'Manufacturer'
            self.putx([Ann.FIELD, ['%s ID: 0x%02x' % (d, miso)]])

        if self.cmdstate == 6:
            id_ = self.ids[1] if self.manufacturer_id_first else self.ids[0]
            self.device_id = id_
            self.es_cmd = self.es
            self.putc([Ann.REMS, self.cmd_vendor_dev_list()])
            self.state = None
        else:
            self.cmdstate += 1

    def handle_rems2(self, mosi, miso):
        pass # TODO

    def handle_enso(self, mosi, miso):
        pass # TODO

    def handle_exso(self, mosi, miso):
        pass # TODO

    def handle_rdscur(self, mosi, miso):
        pass # TODO

    def handle_wrscur(self, mosi, miso):
        pass # TODO

    def handle_esry(self, mosi, miso):
        pass # TODO

    def handle_dsry(self, mosi, miso):
        pass # TODO

    def output_data_block(self, label, idx):
        # Print accumulated block of data
        # (called on CS# de-assert via self.on_end_transaction callback).
        self.es_cmd = self.es # End on the CS# de-assert sample.
        if self.options['format'] == 'hex':
            s = ' '.join([('%02x' % b) for b in self.data])
        else:
            s = ''.join(map(chr, self.data))
        self.putf([Ann.FIELD, ['%s (%d bytes)' % (label, len(self.data))]])
        self.putc([idx, ['%s (addr 0x%06x, %d bytes): %s' % \
                   (cmds[self.state][1], self.addr, len(self.data), s)]])

    def decode(self, ss, es, data):
        ptype, mosi, miso = data

        self.ss, self.es = ss, es

        if ptype == 'CS-CHANGE':
            self.end_current_transaction()

        if ptype != 'DATA':
            return

        # If we encountered a known chip command, enter the resp. state.
        if self.state is None:
            self.state = mosi
            self.cmdstate = 1

        # Handle commands.
        try:
            self.cmd_handlers[self.state](mosi, miso)
        except KeyError:
            self.putx([Ann.BIT, ['Unknown command: 0x%02x' % mosi]])
            self.state = None
