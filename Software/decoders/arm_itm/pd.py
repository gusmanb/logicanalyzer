##
## This file is part of the libsigrokdecode project.
##
## Copyright (C) 2015 Petteri Aimonen <jpa@sigrok.mail.kapsi.fi>
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
import string
import subprocess
import re

ARM_EXCEPTIONS = {
    0: 'Thread',
    1: 'Reset',
    2: 'NMI',
    3: 'HardFault',
    4: 'MemManage',
    5: 'BusFault',
    6: 'UsageFault',
    11: 'SVCall',
    12: 'Debug Monitor',
    14: 'PendSV',
    15: 'SysTick',
}

class Decoder(srd.Decoder):
    api_version = 3
    id = 'arm_itm'
    name = 'ARM ITM'
    longname = 'ARM Instrumentation Trace Macroblock'
    desc = 'ARM Cortex-M / ARMv7m ITM trace protocol.'
    license = 'gplv2+'
    inputs = ['uart']
    outputs = []
    tags = ['Debug/trace']
    options = (
        {'id': 'objdump', 'desc': 'objdump path',
            'default': 'arm-none-eabi-objdump'},
        {'id': 'objdump_opts', 'desc': 'objdump options',
            'default': '-lSC'},
        {'id': 'elffile', 'desc': '.elf path',
            'default': ''},
    )
    annotations = (
        ('trace', 'Trace info'),
        ('timestamp', 'Timestamp'),
        ('software', 'Software message'),
        ('dwt_event', 'DWT event'),
        ('dwt_watchpoint', 'DWT watchpoint'),
        ('dwt_exc', 'Exception trace'),
        ('dwt_pc', 'Program counter'),
        ('mode_thread', 'Current mode: thread'),
        ('mode_irq', 'Current mode: IRQ'),
        ('mode_exc', 'Current mode: Exception'),
        ('location', 'Current location'),
        ('function', 'Current function'),
    )
    annotation_rows = (
        ('traces', 'Trace info', (0, 1)),
        ('softwares', 'Software traces', (2,)),
        ('dwt_events', 'DWT events', (3,)),
        ('dwt_watchpoints', 'DWT watchpoints', (4,)),
        ('dwt_excs', 'Exception traces', (5,)),
        ('dwt_pcs', 'Program counters', (6,)),
        ('modes', 'Current modes', (7, 8, 9)),
        ('locations', 'Current locations', (10,)),
        ('functions', 'Current functions', (11,)),
    )

    def __init__(self):
        self.reset()

    def reset(self):
        self.buf = []
        self.syncbuf = []
        self.swpackets = {}
        self.prevsample = 0
        self.dwt_timestamp = 0
        self.current_mode = None
        self.file_lookup = {}
        self.func_lookup = {}

    def start(self):
        self.out_ann = self.register(srd.OUTPUT_ANN)
        self.load_objdump()

    def load_objdump(self):
        '''Parse disassembly obtained from objdump into a lookup tables'''
        if not (self.options['objdump'] and self.options['elffile']):
            return

        opts = [self.options['objdump']]
        opts += self.options['objdump_opts'].split()
        opts += [self.options['elffile']]

        try:
            disasm = subprocess.check_output(opts)
        except subprocess.CalledProcessError:
            return

        disasm = disasm.decode('utf-8', 'replace')

        instpat = re.compile(r'\s*([0-9a-fA-F]+):\t+([0-9a-fA-F ]+)\t+([a-zA-Z][^;]+)\s*;?.*')
        filepat = re.compile(r'[^\s]+[/\\\\]([a-zA-Z0-9._-]+:[0-9]+)(?:\s.*)?')
        funcpat = re.compile(r'[0-9a-fA-F]+\s*<([^>]+)>:.*')

        prev_file = ''
        prev_func = ''

        for line in disasm.split('\n'):
            m = instpat.match(line)
            if m:
                addr = int(m.group(1), 16)
                self.file_lookup[addr] = prev_file
                self.func_lookup[addr] = prev_func
            else:
                m = funcpat.match(line)
                if m:
                    prev_func = m.group(1)
                else:
                    m = filepat.match(line)
                    if m:
                        prev_file = m.group(1)

    def get_packet_type(self, byte):
        '''Identify packet type based on its first byte.
           See ARMv7-M_ARM.pdf section "Debug ITM and DWT" "Packet Types"
        '''
        if byte & 0x7F == 0:
            return 'sync'
        elif byte == 0x70:
            return 'overflow'
        elif byte & 0x0F == 0 and byte & 0xF0 != 0:
            return 'timestamp'
        elif byte & 0x0F == 0x08:
            return 'sw_extension'
        elif byte & 0x0F == 0x0C:
            return 'hw_extension'
        elif byte & 0x0F == 0x04:
            return 'reserved'
        elif byte & 0x04 == 0x00:
            return 'software'
        else:
            return 'hardware'

    def mode_change(self, new_mode):
        if self.current_mode is not None:
            start, mode = self.current_mode
            if mode.startswith('Thread'):
                ann_idx = 7
            elif mode.startswith('IRQ'):
                ann_idx = 8
            else:
                ann_idx = 9
            self.put(start, self.startsample, self.out_ann, [ann_idx, [mode]])

        if new_mode is None:
            self.current_mode = None
        else:
            self.current_mode = (self.startsample, new_mode)

    def location_change(self, pc):
        new_loc = self.file_lookup.get(pc)
        new_func = self.func_lookup.get(pc)
        ss = self.startsample
        es = self.prevsample

        if new_loc is not None:
            self.put(ss, es, self.out_ann, [10, [new_loc]])

        if new_func is not None:
            self.put(ss, es, self.out_ann, [11, [new_func]])

    def fallback(self, buf):
        ptype = self.get_packet_type(buf[0])
        return [0, [('Unhandled %s: ' % ptype) + ' '.join(['%02x' % b for b in buf])]]

    def handle_overflow(self, buf):
        return [0, ['Overflow']]

    def handle_hardware(self, buf):
        '''Handle packets from hardware source, i.e. DWT block.'''
        plen = (0, 1, 2, 4)[buf[0] & 0x03]
        pid = buf[0] >> 3
        if len(buf) != plen + 1:
            return None # Not complete yet.

        if pid == 0:
            text = 'DWT events:'
            if buf[1] & 0x20:
                text += ' Cyc'
            if buf[1] & 0x10:
                text += ' Fold'
            if buf[1] & 0x08:
                text += ' LSU'
            if buf[1] & 0x04:
                text += ' Sleep'
            if buf[1] & 0x02:
                text += ' Exc'
            if buf[1] & 0x01:
                text += ' CPI'
            return [3, [text]]
        elif pid == 1:
            excnum = ((buf[2] & 1) << 8) | buf[1]
            event = (buf[2] >> 4)
            excstr = ARM_EXCEPTIONS.get(excnum, 'IRQ %d' % (excnum - 16))
            if event == 1:
                self.mode_change(excstr)
                return [5, ['Enter: ' + excstr, 'E ' + excstr]]
            elif event == 2:
                self.mode_change(None)
                return [5, ['Exit: ' + excstr, 'X ' + excstr]]
            elif event == 3:
                self.mode_change(excstr)
                return [5, ['Resume: ' + excstr, 'R ' + excstr]]
        elif pid == 2:
            pc = buf[1] | (buf[2] << 8) | (buf[3] << 16) | (buf[4] << 24)
            self.location_change(pc)
            return [6, ['PC: 0x%08x' % pc]]
        elif (buf[0] & 0xC4) == 0x84:
            comp = (buf[0] & 0x30) >> 4
            what = 'Read' if (buf[0] & 0x08) == 0 else 'Write'
            if plen == 1:
                data = '0x%02x' % (buf[1])
            elif plen == 2:
                data = '0x%04x' % (buf[1] | (buf[2] << 8))
            else:
                data = '0x%08x' % (buf[1] | (buf[2] << 8) | (buf[3] << 16) | (buf[4] << 24))
            return [4, ['Watchpoint %d: %s data %s' % (comp, what, data),
                        'WP%d: %s %s' % (comp, what[0], data)]]
        elif (buf[0] & 0xCF) == 0x47:
            comp = (buf[0] & 0x30) >> 4
            addr = buf[1] | (buf[2] << 8) | (buf[3] << 16) | (buf[4] << 24)
            self.location_change(addr)
            return [4, ['Watchpoint %d: PC 0x%08x' % (comp, addr),
                        'WP%d: PC 0x%08x' % (comp, addr)]]
        elif (buf[0] & 0xCF) == 0x4E:
            comp = (buf[0] & 0x30) >> 4
            offset = buf[1] | (buf[2] << 8)
            return [4, ['Watchpoint %d: address 0x????%04x' % (comp, offset),
                        'WP%d: A 0x%04x' % (comp, offset)]]

        return self.fallback(buf)

    def handle_software(self, buf):
        '''Handle packets generated by software running on the CPU.'''
        plen = (0, 1, 2, 4)[buf[0] & 0x03]
        pid = buf[0] >> 3
        if len(buf) != plen + 1:
            return None # Not complete yet.

        if plen == 1 and chr(buf[1]) in string.printable:
            self.add_delayed_sw(pid, chr(buf[1]))
            return [] # Handled but no data to output.

        self.push_delayed_sw()

        if plen == 1:
            return [2, ['%d: 0x%02x' % (pid, buf[1])]]
        elif plen == 2:
            return [2, ['%d: 0x%02x%02x' % (pid, buf[2], buf[1])]]
        elif plen == 4:
            return [2, ['%d: 0x%02x%02x%02x%02x' % (pid, buf[4], buf[3], buf[2], buf[1])]]

    def handle_timestamp(self, buf):
        '''Handle timestamp packets, which indicate the time of some DWT event packet.'''
        if buf[-1] & 0x80 != 0:
            return None # Not complete yet.

        if buf[0] & 0x80 == 0:
            tc = 0
            ts = buf[0] >> 4
        else:
            tc = (buf[0] & 0x30) >> 4
            ts = buf[1] & 0x7F
            if len(buf) > 2:
                ts |= (buf[2] & 0x7F) << 7
            if len(buf) > 3:
                ts |= (buf[3] & 0x7F) << 14
            if len(buf) > 4:
                ts |= (buf[4] & 0x7F) << 21

        self.dwt_timestamp += ts

        if tc == 0:
            msg = '(exact)'
        elif tc == 1:
            msg = '(timestamp delayed)'
        elif tc == 2:
            msg = '(event delayed)'
        elif tc == 3:
            msg = '(event and timestamp delayed)'

        return [1, ['Timestamp: %d %s' % (self.dwt_timestamp, msg)]]

    def add_delayed_sw(self, pid, c):
        '''We join printable characters from software source so that printed
        strings are easy to read. Joining is done by PID so that different
        sources do not get confused with each other.'''
        if self.swpackets.get(pid) is not None:
            self.swpackets[pid][1] = self.prevsample
            self.swpackets[pid][2] += c
        else:
            self.swpackets[pid] = [self.startsample, self.prevsample, c]

    def push_delayed_sw(self):
        for pid, packet in self.swpackets.items():
            if packet is None:
                continue
            ss, prevtime, text = packet
            # Heuristic criterion: Text has ended if at least 16 byte
            # durations after previous received byte. Actual delay depends
            # on printf implementation on target.
            if self.prevsample - prevtime > 16 * self.byte_len:
                self.put(ss, prevtime, self.out_ann, [2, ['%d: "%s"' % (pid, text)]])
                self.swpackets[pid] = None

    def decode(self, ss, es, data):
        ptype, rxtx, pdata = data

        # For now, ignore all UART packets except the actual data packets.
        if ptype != 'DATA':
            return

        self.byte_len = es - ss

        # Reset packet if there is a long pause between bytes.
        # TPIU framing can introduce small pauses, but more than 1 frame
        # should reset packet.
        if ss - self.prevsample > 16 * self.byte_len:
            self.push_delayed_sw()
            self.buf = []
        self.prevsample = es

        # Build up the current packet byte by byte.
        self.buf.append(pdata[0])

        # Store the start time of the packet.
        if len(self.buf) == 1:
            self.startsample = ss

        # Keep separate buffer for detection of sync packets.
        # Sync packets override everything else, so that we can regain sync
        # even if some packets are corrupted.
        self.syncbuf = self.syncbuf[-5:] + [pdata[0]]
        if self.syncbuf == [0, 0, 0, 0, 0, 0x80]:
            self.buf = self.syncbuf

        # See if it is ready to be decoded.
        ptype = self.get_packet_type(self.buf[0])
        if hasattr(self, 'handle_' + ptype):
            func = getattr(self, 'handle_' + ptype)
            data = func(self.buf)
        else:
            data = self.fallback(self.buf)

        if data is not None:
            if data:
                self.put(self.startsample, es, self.out_ann, data)
            self.buf = []
