##
## This file is part of the libsigrokdecode project.
##
## Copyright (C) 2019 Vesa-Pekka Palmu <vpalmu@depili.fi>
##
## This program is free software; you can redistribute it and/or modify
## it under the terms of the GNU General Public License as published by
## the Free Software Foundation; either version 3 of the License, or
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
from math import ceil
from common.srdhelper import SrdIntEnum
from .lists import *

L = len(cmds)
RX = 0
TX = 1

Ann = SrdIntEnum.from_list('Ann',
    [c[0] for c in cmds.values()] + ['BIT', 'FIELD', 'WARN'])

def cmd_annotation_classes():
    return tuple([tuple([cmd[0].lower(), cmd[1]]) for cmd in cmds.values()])

class Decoder(srd.Decoder):
    api_version = 3
    id = 'amulet_ascii'
    name = 'Amulet ASCII'
    longname = 'Amulet LCD ASCII'
    desc = 'Amulet Technologies LCD controller ASCII protocol.'
    license = 'gplv3+'
    inputs = ['uart']
    outputs = []
    tags = ['Display']
    annotations = cmd_annotation_classes() + (
        ('bit', 'Bit'),
        ('field', 'Field'),
        ('warning', 'Warning'),
    )
    annotation_rows = (
        ('bits', 'Bits', (L + 0,)),
        ('fields', 'Fields', (L + 1,)),
        ('commands', 'Commands', tuple(range(L))),
        ('warnings', 'Warnings', (L + 2,)),
    )
    options = (
        {'id': 'ms_chan', 'desc': 'Master -> slave channel',
            'default': 'RX', 'values': ('RX', 'TX')},
        {'id': 'sm_chan', 'desc': 'Slave -> master channel',
            'default': 'TX', 'values': ('RX', 'TX')},
    )

    def __init__(self):
        self.reset()

    def reset(self):
        self.state = None
        self.cmdstate = None

        # Build dict mapping command keys to handler functions. Each
        # command in 'cmds' (defined in lists.py) has a matching
        # handler self.handle_<shortname>.
        def get_handler(cmd):
            s = 'handle_%s' % cmds[cmd][0].lower().replace('/', '_')
            return getattr(self, s)
        self.cmd_handlers = dict((cmd, get_handler(cmd)) for cmd in cmds.keys())

    def start(self):
        self.out_ann = self.register(srd.OUTPUT_ANN)

    def putx(self, data):
        # Simplification, most annotations span exactly one SPI byte/packet.
        self.put(self.ss, self.es, self.out_ann, data)

    def putf(self, data):
        self.put(self.ss_field, self.es_field, self.out_ann, data)

    def putc(self, data):
        self.put(self.ss_cmd, self.es_cmd, self.out_ann, data)

    def cmd_ann_list(self):
        x, s = cmds[self.state][0], cmds[self.state][1]
        return ['Command: %s (%s)' % (s, x), 'Command: %s' % s,
                'Cmd: %s' % s, 'Cmd: %s' % x, x]

    def emit_cmd_byte(self):
        self.ss_cmd = self.ss
        self.putx([Ann.FIELD, self.cmd_ann_list()])

    def emit_addr_bytes(self, pdata):
        if self.cmdstate == 2:
            self.ss_field = self.ss
            self.addr = chr(pdata)
            self.putx([Ann.BIT, ['Address high nibble: %c' % pdata,
                 'Addr high 0x%c' % pdata, 'Addr h 0x%c' % pdata]])
        elif self.cmdstate == 3:
            self.es_field = self.es
            self.addr += chr(pdata)
            self.addr = int(self.addr, 16)
            self.putx([Ann.BIT, ['Address low nibble: %c' % pdata,
                 'Addr low 0x%c' % pdata, 'Addr l 0x%c' % pdata]])
            self.putf([Ann.FIELD, ['Address: 0x%02X' % self.addr,
                'Addr: 0x%02X' % self.addr, '0x%02X' % self.addr]])

    def emit_cmd_end(self, data):
        self.es_cmd = self.es
        self.putc(data)
        self.state = None

    def handle_read(self, data):
        if self.cmdstate == 1:
            self.emit_cmd_byte()
            self.addr = 0
        elif self.cmdstate == 2:
            self.emit_addr_bytes(pdata)
        elif self.cmdstate == 3:
            self.emit_addr_bytes(pdata)
        self.cmdstate += 1

    def handle_set_common(self, pdata):
        if self.cmdstate == 1:
            self.addr = 0
        self.emit_addr_bytes(pdata)

    def emit_not_implemented(self, data):
        self.es_cmd = self.es
        self.putc([Ann.WARN, ['Command not decoded', 'Not decoded']])
        self.emit_cmd_end(data)

    def handle_string(self, pdata, ann_class):
        # TODO: unicode / string modifiers...
        self.handle_set_common(pdata)
        if self.cmdstate == 4:
            self.ss_field = self.ss
            self.value = ''
        if pdata == 0x00:
            # Null terminated string ends.
            self.es_field = self.es
            self.putx([Ann.BIT, ['NULL']])
            self.putf([Ann.FIELD, ['Value: %s' % self.value,
                'Val: %s' % self.value, '%s' % self.value]])
            self.emit_cmd_end([ann_class, self.cmd_ann_list()])
            return
        if self.cmdstate > 3:
            self.value += chr(pdata)
            self.putx([Ann.BIT, ['%c' % pdata]])
        self.cmdstate += 1

    # Command handlers

    # Page change 0xA0, 0x02, index_high, index_low, checksum
    def handle_page(self, pdata):
        if self.cmdstate == 2:
            if pdata == 0x02:
                self.ss_field = self.ss_cmd
                self.es_field = self.es
                self.putf([Ann.FIELD, self.cmd_ann_list()])
                self.checksum = 0xA0 + 0x02
            else:
                self.putx([Ann.WARN, ['Illegal second byte for page change',
                                      'Illegal byte']])
                self.state = None
        elif self.cmdstate == 3:
            self.ss_field = self.ss
            self.checksum += pdata
            self.page[0] = pdata
        elif self.cmdstate == 4:
            self.checksum += pdata
            self.page[1] = pdata
            self.es_field = self.es
            if self.page[0] == self.page [1] == 0xFF:
                # Soft reset trigger
                self.putf(Ann.WARN, ['Soft reset', 'Reset'])
            else:
                page = chr(self.page[0]) + chr(self.page[1])
                self.putf(Ann.FIELD, ['Page index: 0x%s' % page,
                                      'Page: 0x%s' % page, '0x%s' % page])
        elif self.cmdstate == 5:
            self.checksum += pdata
            if (self.checksum & 0xFF) != 0:
                self.putx([Ann.WARN, ['Checksum error', 'Error', 'ERR']])
            else:
                self.putx([Ann.FIELD, ['Checksum OK', 'OK']])
            self.emit_cmd_end(Ann.PAGE)
        self.cmdstate += 1

    # Value reads: command byte, address high nibble, address low nibble

    # Get byte value
    def handle_gbv(self, pdata):
        self.handle_read(pdata)
        self.emit_cmd_end([Ann.GBV, self.cmd_ann_list()])

    # Get word value
    def handle_gwv(self, pdata):
        self.handle_read(pdata)
        self.emit_cmd_end([Ann.GWV, self.cmd_ann_list()])

    # Get string value
    def handle_gsv(self, pdata):
        self.handle_read(pdata)
        self.emit_cmd_end([Ann.GSV, self.cmd_ann_list()])

    # Get label value
    def handle_glv(self, pdata):
        self.handle_read(pdata)
        self.emit_cmd_end([Ann.GLV, self.cmd_ann_list()])

    # Get RPC buffer
    def handle_grpc(self, pdata):
        if self.cmdstate == 2:
            self.ss_field = self.ss
            self.flags = int(chr(pdata), 16) << 4
        elif self.cmdstate == 3:
            self.flags += int(chr(pdata), 16)
            self.es_field = self.es
            self.putf([Ann.FIELD, ['RPC flag: 0x%02X' % self.flags]])
            self.emit_cmd_end([Ann.GRPC, self.cmd_ann_list()])

    # Get byte value array
    def handle_gbva(self, pdata):
        self.handle_read(pdata)
        self.emit_cmd_end([Ann.GBVA, self.cmd_ann_list()])

    # Get word value array
    def handle_gwva(self, pdata):
        self.handle_read(pdata)
        self.emit_cmd_end([Ann.GWVA, self.cmd_ann_list()])

    # Get color variable
    def handle_gcv(self, pdata):
        self.handle_read(pdata)
        self.emit_cmd_end([Ann.GCV, self.cmd_ann_list()])

    # Value setters: command byte, address high nibble, address low nibble, data bytes

    # Set byte value data = high nibble, low nibble
    def handle_sbv(self, pdata):
        self.handle_set_common(pdata)
        if self.cmdstate == 4:
            self.ss_field = self.ss
            self.value = chr(pdata)
        elif self.cmdstate == 5:
            self.value += chr(pdata)
            self.es_field = self.es
            self.putf([Ann.FIELD, ['Value: 0x%s' % self.value,
                'Val: 0x%s' % self.value, '0x%s' % self.value]])
            self.emit_cmd_end([Ann.SBV, self.cmd_ann_list()])
        self.cmdstate += 1

    # Set word value, msb high, msb low, lsb high, lsb low
    def handle_swv(self, pdata):
        self.handle_set_common(pdata)
        if self.cmdstate > 3:
            nibble = self.cmdstate - 4
            if nibble == 0:
                self.ss_field = self.ss
                self.value = 0
            self.value += int(chr(pdata), 16) << 12 - (4 * nibble)
            if nibble == 3:
                self.es_field = self.es
                self.putf([Ann.FIELD, ['Value: 0x%04x' % self.value,
                    'Val: 0x%04x' % self.value, '0x%04x' % self.value]])
                self.emit_cmd_end([Ann.SWV, self.cmd_ann_list()])
                return
        self.cmdstate += 1

    # Set string value, null terminated utf8 strings
    def handle_ssv(self, pdata):
        self.handle_string(pdata, Ann.SSV)

    # Set byte value array
    def handle_sbva(self, pdata):
        nibble = (self.cmdstate - 3) % 2
        if self.cmdstate == 2:
            self.addr = int(chr(pdata), 16) << 4
            self.ss_field = self.ss
            self.putx([Ann.BIT, ['Address high nibble: %c' % pdata,
                 'Addr high 0x%c' % pdata, '0x%c' % pdata]])
        elif self.cmdstate == 3:
            self.addr += int(chr(pdata), 16)
            self.es_field = self.ss
            self.putx([Ann.BIT, ['Address low nibble: %c' % pdata,
                 'Addr low 0x%c' % pdata, '0x%c' % pdata]])
            self.putf([Ann.FIELD, ['Address: 0x%02X' % self.addr,
                'Addr: 0x%02X' % self.addr, '0x%02X' % self.addr]])
        elif stage == 2:
            if pdata == 0x00:
                # Null terminated list
                self.emit_cmd_end([Ann.SBVA, self.cmd_ann_list()])
                return
            self.value = int(chr(pdata), 16) << 4
        else:
            self.value += int(chr(pdata), 16)
            self.es_field = self.es
            self.putf([Ann.FIELD, ['Value 0x%02X' % self.value,
                                   '0x%02X' % self.value]])
        self.cmdstate += 1

    # Set word value array
    def handle_swva(self, pdata):
        nibble = (self.cmdstate - 3) % 4
        if self.cmdstate == 2:
            self.addr = int(chr(pdata), 16) << 4
            self.ss_field = self.ss
            self.putx([Ann.BIT, ['Address high nibble: %c' % pdata,
                  'Addr high 0x%c' % pdata, '0x%c' % pdata]])
        elif self.cmdstate == 3:
            self.addr += int(chr(pdata), 16)
            self.es_field = self.ss
            self.putx([Ann.BIT, ['Address low nibble: %c' % pdata,
                 'Addr low 0x%c' % pdata, '0x%c' % pdata]])
            self.putf([Ann.FIELD, ['Address: 0x%02X' % self.addr,
                 'Addr: 0x%02X' % self.addr, '0x%02X' % self.addr]])
            self.value = 0
        else:
            self.value += int(chr(pdata), 16) << 12 - (4 * nibble)
            if nibble == 0:
                if pdata == 0x00:
                    # Null terminated list
                    self.emit_cmd_end([Ann.SWVA, self.cmd_ann_list()])
                    return
                self.ss_field = self.ss
            if nibble == 3:
                self.es_field = self.es
                self.putf([Ann.FIELD, ['Value 0x%04X' % self.value,
                                       '0x%04X' % self.value]])
                self.cmdstate += 1

    # Set color variable
    def handle_scv(self, pdata):
        if self.cmdstate == 8:
            self.emit_not_implemented([Ann.SCV, self.cmd_ann_list()])
        self.cmdstate += 1

    # RPC trigger
    def handle_rpc(self, pdata):
        self.handle_read(pdata)
        self.emit_cmd_end([Ann.RPC, self.cmd_ann_list()])

    # Drawing

    # Decode pair of (x,y) 16bit coordinates
    def decode_coords(self, pdata):
        if self.cmdstate == 1:
            self.coords[0] = 0
            self.coords[1] = 0
            self.coords[2] = 0
            self.coords[3] = 0
        if self.cmdstate < 18:
            # Coordinates
            nibble = (self.cmdstate - 1) % 4
            i = (self.cmdstate - 1) / 4
            self.coords[i] += int(chr(pdata), 16) << 12 - (4 * nibble)
            if nibble == 0:
                self.ss_field = self.ss
            elif nibble == 3:
                self.es_field = self.es
                self.putf([Ann.FIELD, ['Coordinate 0x%04X' % self.coords[i]],
                                      ['0x%04X' % self.coords[i]]])

    # TODO: There are actually two protocol revisions for drawing.
    # Both use 4 bytes for 16bit x and y pairs for start and end.
    # The older follows this by a pattern selector and then line weight.
    # Newer version has 6 bytes for 8bit RGB color...

    # Draw line
    def handle_line(self, pdata):
        decode_coords(pdata)
        if self.cmdstate == 18:
            self.es_cmd = self.es
            self.putc([Ann.LINE, self.cmd_ann_list()])
            self.putc([Ann.WARN, ['Line pattern / Color not implemented']])
            self.state = None
        self.cmdstate += 1

    # Draw rectange
    def handle_rect(self, pdata):
        decode_coords(pdata)
        if self.cmdstate == 18:
            self.es_cmd = self.es
            self.putc([Ann.RECT, self.cmd_ann_list()])
            self.putc([Ann.WARN, ['Line pattern / Color not implemented']])
            self.state = None
        self.cmdstate += 1

    # Draw filled rectangle
    def handle_frect(self, pdata):
        decode_coords(pdata)
        if self.cmdstate == 18:
            self.es_cmd = self.es
            self.putc([Ann.FRECT, self.cmd_ann_list()])
            self.putc([Ann.WARN, ['Fill pattern / Color not implemented']])
            self.state = None
        self.cmdstate += 1

    # Draw pixel
    def handle_pixel(self, pdata):
        self.es_cmd = self.es
        self.putc([Ann.WARN, ['Draw pixel documentation is missing.', 'Undocumented']])
        self.state = None

    # Replies
    def handle_gbvr(self, pdata):
        self.emit_add_bytes(pdata)
        if self.cmdstate == 4:
            self.ss_field = self.ss
            self.value = int(chr(pdata), 16) << 4
            self.putx([Ann.BIT, ['High nibble 0x%s' % pdata, '0x%s' % pdata]])
        elif self.cmdstate == 5:
            self.value += int(chr(pdata), 16)
            self.putx([Ann.BIT, ['Low nibble 0x%s' % pdata, '0x%s' % pdata]])
            self.es_field = self.es
            self.putf([Ann.FIELD, ['Value: 0x%02X' % self.value,
                                   '0x%02X' % self.value]])
            self.emit_cmd_end([Ann.GBVR, self.cmd_ann_list()])
        self.cmdstate += 1

    def handle_gwvr(self, pdata):
        self.emit_add_bytes(pdata)
        if self.cmdstate > 3:
            nibble = self.cmdstate - 3
            if nibble == 0:
                self.value = 0
                self.ss_field = self.ss
            self.value += int(chr(pdata), 16) << 12 - (4 * nibble)
            self.putx([Ann.BIT, ['0x%s' % pdata]])
            if nibble == 3:
                self.putf([Ann.FIELD, ['Value: 0x%04x' % self.value,
                                       '0x%04X' % self.value]])
                self.es_cmd = self.ss
                self.emit_cmd_end([Ann.GWVR, self.cmd_ann_list()])
        self.cmdstate += 1

    def handle_gsvr(self, pdata):
        self.handle_string(pdata, Ann.GSVR)

    def handle_glvr(self, pdata):
        self.handle_string(pdata, Ann.GLVR)

    def handle_grpcr(self, pdata):
        self.handle_addr(pdata)
        if self.cmdstate > 3:
            nibble = (self.cmdstate - 3) % 2
            if nibble == 0:
                if pdata == 0x00:
                    self.emit_cmd_end([Ann.GRPCR, self.cmd_ann_list()])
                    return
                self.value = int(chr(pdata), 16) << 4
                self.ss_field = self.ss
                self.putx([Ann.BIT, ['0x%s' % pdata]])
            if nibble == 2:
                self.value += int(chr(pdata), 16)
                self.es_field = self.es
                self.putx([Ann.BIT, ['0x%s' % pdata]])
                self.putf([Ann.FIELD, ['0x%02X' % self.value]])
        self.cmdstate += 1

    def handle_sbvr(self, pdata):
        self.handle_set_common(pdata)
        if self.cmdstate == 4:
            self.ss_field = self.ss
            self.value = chr(pdata)
        elif self.cmdstate == 5:
            self.value += chr(pdata)
            self.es_field = self.es
            self.putf([Ann.FIELD, ['Value: 0x%s' % self.value,
                'Val: 0x%s' % self.value, '0x%s' % self.value]])
            self.emit_cmd_end([Ann.SBVR, self.cmd_ann_list()])
        self.cmdstate += 1

    def handle_swvr(self, pdata):
        self.handle_set_common(pdata)
        if self.cmdstate == 4:
            self.ss_field = self.ss
            self.value = (pdata - 0x30) << 4
        elif self.cmdstate == 5:
            self.value += (pdata - 0x30)
            self.value = self.value << 8
        elif self.cmdstate == 6:
            self.value += (pdata - 0x30) << 4
        elif self.cmdstate == 7:
            self.value += (pdata - 0x30)
            self.es_field = self.es
            self.putf([Ann.FIELD, ['Value: 0x%04x' % self.value,
                'Val: 0x%04x' % self.value, '0x%04x' % self.value]])
            self.emit_cmd_end([Ann.SWVR, self.cmd_ann_list()])
            self.state = None
        self.cmdstate += 1

    def handle_ssvr(self, pdata):
        self.handle_string(pdata, Ann.SSVR)

    def handle_rpcr(self, pdata):
        self.handle_read(pdata)
        self.emit_cmd_end([Ann.RPCR, self.cmd_ann_list()])

    def handle_liner(self, pdata):
        decode_coords(pdata)
        if self.cmdstate == 18:
            self.es_cmd = self.es
            self.putc([Ann.LINER, self.cmd_ann_list()])
            self.putc([Ann.WARN, ['Line pattern / Color not implemented']])
            self.state = None
        self.cmdstate += 1

    def handle_rectr(self, pdata):
        decode_coords(pdata)
        if self.cmdstate == 18:
            self.es_cmd = self.es
            self.putc([Ann.RECTR, self.cmd_ann_list()])
            self.putc([Ann.WARN, ['Line pattern / Color not implemented']])
            self.state = None
        self.cmdstate += 1

    def handle_frectr(self, pdata):
        decode_coords(pdata)
        if self.cmdstate == 18:
            self.es_cmd = self.es
            self.putc([Ann.FRECTR, self.cmd_ann_list()])
            self.putc([Ann.WARN, ['Line pattern / Color not implemented']])
            self.state = None
        self.cmdstate += 1

    def handle_pixelr(self, pdata):
        self.es_cmd = self.es
        self.putc([Ann.WARN,['Draw pixel documentation is missing.', 'Undocumented']])
        self.state = None

    def handle_gbvar(self, pdata):
        nibble = (self.cmdstate - 3) % 2
        if self.cmdstate == 2:
            self.addr = int(chr(pdata), 16) << 4
            self.ss_field = self.ss
            self.putx([Ann.BIT, ['Address high nibble: %c' % pdata,
                 'Addr high 0x%c' % pdata, '0x%c' % pdata]])
        elif self.cmdstate == 3:
            self.addr += int(chr(pdata), 16)
            self.es_field = self.ss
            self.putx([Ann.BIT, ['Address low nibble: %c' % pdata,
                 'Addr low 0x%c' % pdata, '0x%c' % pdata]])
            self.putf([Ann.FIELD, ['Address: 0x%02X' % self.addr,
                'Addr: 0x%02X' % self.addr, '0x%02X' % self.addr]])
        elif stage == 2:
            if pdata == 0x00:
                # Null terminated list
                self.emit_cmd_end([Ann.GBVAR, self.cmd_ann_list()])
                return
            self.value = int(chr(pdata), 16) << 4
        else:
            self.value += int(chr(pdata), 16)
            self.es_field = self.es
            self.putf([Ann.FIELD, ['Value 0x%02X' % self.value,
                                   '0x%02X' % self.value]])
        self.cmdstate += 1

    def handle_gwvar(self, pdata):
        nibble = (self.cmdstate - 3) % 4
        if self.cmdstate == 2:
            self.addr = int(chr(pdata), 16) << 4
            self.ss_field = self.ss
            self.putx([Ann.BIT, ['Address high nibble: %c' % pdata,
                  'Addr high 0x%c' % pdata, '0x%c' % pdata]])
        elif self.cmdstate == 3:
            self.addr += int(chr(pdata), 16)
            self.es_field = self.ss
            self.putx([Ann.BIT, ['Address low nibble: %c' % pdata,
                 'Addr low 0x%c' % pdata, '0x%c' % pdata]])
            self.putf([Ann.FIELD, ['Address: 0x%02X' % self.addr,
                 'Addr: 0x%02X' % self.addr, '0x%02X' % self.addr]])
            self.value = 0
        else:
            self.value += int(chr(pdata), 16) << 12 - (4 * nibble)
            if nibble == 0:
                if pdata == 0x00:
                    # Null terminated list
                    self.emit_cmd_end([Ann.GWVAR, self.cmd_ann_list()])
                    return
                self.ss_field = self.ss
            if nibble == 3:
                self.es_field = self.es
                self.putf([Ann.FIELD, ['Value 0x%04X' % self.value,
                                       '0x%04X' % self.value]])
                self.cmdstate += 1

    # Get byte variable array reply
    def handle_sbvar(self, pdata):
        nibble = (self.cmdstate - 3) % 2
        if self.cmdstate == 2:
            self.addr = int(chr(pdata), 16) << 4
            self.ss_field = self.ss
            self.putx([Ann.BIT, ['Address high nibble: %c' % pdata,
                 'Addr high 0x%c' % pdata, '0x%c' % pdata]])
        elif self.cmdstate == 3:
            self.addr += int(chr(pdata), 16)
            self.es_field = self.ss
            self.putx([Ann.BIT, ['Address low nibble: %c' % pdata,
                 'Addr low 0x%c' % pdata, '0x%c' % pdata]])
            self.putf([Ann.FIELD, ['Address: 0x%02X' % self.addr,
                'Addr: 0x%02X' % self.addr, '0x%02X' % self.addr]])
        elif stage == 2:
            if pdata == 0x00:
                # Null terminated list
                self.emit_cmd_end([Ann.SBVAR, self.cmd_ann_list()])
                return
            self.value = int(chr(pdata), 16) << 4
        else:
            self.value += int(chr(pdata), 16)
            self.es_field = self.es
            self.putf([Ann.FIELD, ['Value 0x%02X' % self.value,
                                   '0x%02X' % self.value]])
        self.cmdstate += 1

    # Set word variable array reply
    def handle_swvar(self, pdata):
        nibble = (self.cmdstate - 3) % 4
        if self.cmdstate == 2:
            self.addr = int(chr(pdata), 16) << 4
            self.ss_field = self.ss
            self.putx([Ann.BIT, ['Address high nibble: %c' % pdata,
                  'Addr high 0x%c' % pdata, '0x%c' % pdata]])
        elif self.cmdstate == 3:
            self.addr += int(chr(pdata), 16)
            self.es_field = self.ss
            self.putx([Ann.BIT, ['Address low nibble: %c' % pdata,
                 'Addr low 0x%c' % pdata, '0x%c' % pdata]])
            self.putf([Ann.FIELD, ['Address: 0x%02X' % self.addr,
                 'Addr: 0x%02X' % self.addr, '0x%02X' % self.addr]])
            self.value = 0
        else:
            self.value += int(chr(pdata), 16) << 12 - (4 * nibble)
            if nibble == 0:
                if pdata == 0x00:
                    # Null terminated list
                    self.emit_cmd_end([Ann.SWVAR, self.cmd_ann_list()])
                    return
                self.ss_field = self.ss
            if nibble == 3:
                self.es_field = self.es
                self.putf([Ann.FIELD, ['Value 0x%04X' % self.value,
                                       '0x%04X' % self.value]])
                self.cmdstate += 1

    def handle_gcvr(self, pdata):
        if self.cmdstate == 8:
            self.emit_not_implemented([Ann.SCV, self.cmd_ann_list()])
        self.cmdstate += 1

    def handle_scvr(self, pdata):
        if self.cmdstate == 8:
            self.emit_not_implemented([Ann.SCV, self.cmd_ann_list()])
        self.cmdstate += 1

    # ACK & NACK

    def handle_ack(self, pdata):
        self.putx([Ann.ACK, self.cmd_ann_list()])
        self.state = None

    def handle_nack(self, pdata):
        self.putx([Ann.NACK, self.cmd_ann_list()])
        self.state = None

    def decode(self, ss, es, data):
        ptype, rxtx, pdata = data

        self.ss, self.es = ss, es

        if ptype != 'DATA':
            return

        # Handle commands.
        try:
            abort_current = (0xD0 <= pdata[0] <= 0xF7) and \
                (not (self.state in cmds_with_high_bytes)) and \
                self.state != None
            if abort_current:
                self.putx([Ann.WARN, ['Command aborted by invalid byte', 'Abort']])
                self.state = pdata[0]
                self.emit_cmd_byte()
                self.cmdstate = 1
            if self.state is None:
                self.state = pdata[0]
                self.emit_cmd_byte()
                self.cmdstate = 1
            self.cmd_handlers[self.state](pdata[0])
        except KeyError:
            self.putx([Ann.WARN, ['Unknown command: 0x%02x' % pdata[0]]])
            self.state = None
