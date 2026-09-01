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
import subprocess
import re

# See ETMv3 Signal Protocol table 7-11: 'Encoding of Exception[8:0]'.
exc_names = [
    'No exception', 'IRQ1', 'IRQ2', 'IRQ3', 'IRQ4', 'IRQ5', 'IRQ6', 'IRQ7',
    'IRQ0', 'UsageFault', 'NMI', 'SVC', 'DebugMon', 'MemManage', 'PendSV',
    'SysTick', 'Reserved', 'Reset', 'BusFault', 'Reserved', 'Reserved'
]

for i in range(8, 496):
    exc_names.append('IRQ%d' % i)

def parse_varint(bytes_):
    '''Parse an integer where the top bit is the continuation bit.
    Returns value and number of parsed bytes.'''
    v = 0
    for i, b in enumerate(bytes_):
        v |= (b & 0x7F) << (i * 7)
        if b & 0x80 == 0:
            return v, i+1
    return v, len(bytes_)

def parse_uint(bytes_):
    '''Parse little-endian integer.'''
    v = 0
    for i, b in enumerate(bytes_):
        v |= b << (i * 8)
    return v

def parse_exc_info(bytes_):
    '''Parse exception information bytes from a branch packet.'''
    if len(bytes_) < 1:
        return None

    excv, exclen = parse_varint(bytes_)
    if bytes_[exclen - 1] & 0x80 != 0x00:
        return None # Exception info not complete.

    if exclen == 2 and excv & (1 << 13):
        # Exception byte 1 was skipped, fix up the decoding.
        excv = (excv & 0x7F) | ((excv & 0x3F80) << 7)

    ns = excv & 1
    exc = ((excv >> 1) & 0x0F) | ((excv >> 7) & 0x1F0)
    cancel = (excv >> 5) & 1
    altisa = (excv >> 6) & 1
    hyp = (excv >> 12) & 1
    resume = (excv >> 14) & 0x0F
    return (ns, exc, cancel, altisa, hyp, resume)

def parse_branch_addr(bytes_, ref_addr, cpu_state, branch_enc):
    '''Parse encoded branch address.
       Returns addr, addrlen, cpu_state, exc_info.
       Returns None if packet is not yet complete'''

    addr, addrlen = parse_varint(bytes_)

    if bytes_[addrlen - 1] & 0x80 != 0x00:
        return None # Branch address not complete.

    addr_bits = 7 * addrlen

    have_exc_info = False
    if branch_enc == 'original':
        if addrlen == 5 and bytes_[4] & 0x40:
            have_exc_info = True
    elif branch_enc == 'alternative':
        addr_bits -= 1 # Top bit of address indicates exc_info.
        if addrlen >= 2 and addr & (1 << addr_bits):
            have_exc_info = True
            addr &= ~(1 << addr_bits)

    exc_info = None
    if have_exc_info:
        exc_info = parse_exc_info(bytes_[addrlen:])
        if exc_info is None:
            return None # Exception info not complete.

    if addrlen == 5:
        # Possible change in CPU state.
        if bytes_[4] & 0xB8 == 0x08:
            cpu_state = 'arm'
        elif bytes_[4] & 0xB0 == 0x10:
            cpu_state = 'thumb'
        elif bytes_[4] & 0xA0 == 0x20:
            cpu_state = 'jazelle'
        else:
            raise NotImplementedError('Unhandled branch byte 4: 0x%02x' % bytes_[4])

    # Shift the address according to current CPU state.
    if cpu_state == 'arm':
        addr = (addr & 0xFFFFFFFE) << 1
        addr_bits += 1
    elif cpu_state == 'thumb':
        addr = addr & 0xFFFFFFFE
    elif cpu_state == 'jazelle':
        addr = (addr & 0xFFFFFFFFE) >> 1
        addr_bits -= 1
    else:
        raise NotImplementedError('Unhandled state: ' + cpu_state)

    # If the address wasn't full, fill in with the previous address.
    if addrlen < 5:
        addr |= ref_addr & (0xFFFFFFFF << addr_bits)

    return addr, addrlen, cpu_state, exc_info

class Decoder(srd.Decoder):
    api_version = 3
    id = 'arm_etmv3'
    name = 'ARM ETMv3'
    longname = 'ARM Embedded Trace Macroblock v3'
    desc = 'ARM ETM v3 instruction trace protocol.'
    license = 'gplv2+'
    inputs = ['uart']
    outputs = []
    tags = ['Debug/trace']
    annotations = (
        ('trace', 'Trace info'),
        ('branch', 'Branch'),
        ('exception', 'Exception'),
        ('execution', 'Instruction execution'),
        ('data', 'Data access'),
        ('pc', 'Program counter'),
        ('instr_e', 'Executed instruction'),
        ('instr_n', 'Not executed instruction'),
        ('source', 'Source code'),
        ('location', 'Current location'),
        ('function', 'Current function'),
    )
    annotation_rows = (
        ('traces', 'Trace info', (0,)),
        ('flow', 'Code flow', (1, 2, 3,)),
        ('data-vals', 'Data access', (4,)),
        ('pc-vals', 'Program counters', (5,)),
        ('instructions', 'Instructions', (6, 7,)),
        ('sources', 'Source code', (8,)),
        ('locations', 'Current locations', (9,)),
        ('functions', 'Current functions', (10,)),
    )
    options = (
        {'id': 'objdump', 'desc': 'objdump path',
            'default': 'arm-none-eabi-objdump'},
        {'id': 'objdump_opts', 'desc': 'objdump options',
            'default': '-lSC'},
        {'id': 'elffile', 'desc': '.elf path',
            'default': ''},
        {'id': 'branch_enc', 'desc': 'Branch encoding',
            'default': 'alternative', 'values': ('alternative', 'original')},
    )

    def __init__(self):
        self.reset()

    def reset(self):
        self.buf = []
        self.syncbuf = []
        self.prevsample = 0
        self.last_branch = 0
        self.cpu_state = 'arm'
        self.current_pc = 0
        self.current_loc = None
        self.current_func = None
        self.next_instr_lookup = {}
        self.file_lookup = {}
        self.func_lookup = {}
        self.disasm_lookup = {}
        self.source_lookup = {}

    def start(self):
        self.out_ann = self.register(srd.OUTPUT_ANN)
        self.load_objdump()

    def load_objdump(self):
        '''Parse disassembly obtained from objdump into two tables:
        next_instr_lookup: Find the next PC addr from current PC.
        disasm_lookup: Find the instruction text from current PC.
        source_lookup: Find the source code line from current PC.
        '''
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
        branchpat = re.compile(r'(b|bl|b..|bl..|cbnz|cbz)(?:\.[wn])?\s+(?:r[0-9]+,\s*)?([0-9a-fA-F]+)')
        filepat = re.compile(r'[^\s]+[/\\\\]([a-zA-Z0-9._-]+:[0-9]+)(?:\s.*)?')
        funcpat = re.compile(r'[0-9a-fA-F]+\s*<([^>]+)>:.*')

        prev_src = ''
        prev_file = ''
        prev_func = ''

        for line in disasm.split('\n'):
            m = instpat.match(line)
            if m:
                addr = int(m.group(1), 16)
                raw = m.group(2)
                disas = m.group(3).strip().replace('\t', ' ')
                self.disasm_lookup[addr] = disas
                self.source_lookup[addr] = prev_src
                self.file_lookup[addr] = prev_file
                self.func_lookup[addr] = prev_func

                # Next address in direct sequence.
                ilen = len(raw.replace(' ', '')) // 2
                next_n = addr + ilen

                # Next address if branch is taken.
                bm = branchpat.match(disas)
                if bm:
                    next_e = int(bm.group(2), 16)
                else:
                    next_e = next_n

                self.next_instr_lookup[addr] = (next_n, next_e)
            else:
                m = funcpat.match(line)
                if m:
                    prev_func = m.group(1)
                    prev_src = None
                else:
                    m = filepat.match(line)
                    if m:
                        prev_file = m.group(1)
                        prev_src = None
                    else:
                        prev_src = line.strip()

    def flush_current_loc(self):
        if self.current_loc is not None:
            ss, es, loc, src = self.current_loc
            if loc:
                self.put(ss, es, self.out_ann, [9, [loc]])
            if src:
                self.put(ss, es, self.out_ann, [8, [src]])
            self.current_loc = None

    def flush_current_func(self):
        if self.current_func is not None:
            ss, es, func = self.current_func
            if func:
                self.put(ss, es, self.out_ann, [10, [func]])
            self.current_func = None

    def instructions_executed(self, exec_status):
        '''Advance program counter based on executed instructions.
        Argument is a list of False for not executed and True for executed
        instructions.
        '''

        if len(exec_status) == 0:
            return

        tdelta = max(1, (self.prevsample - self.startsample) / len(exec_status))

        for i, exec_status in enumerate(exec_status):
            pc = self.current_pc
            default_next = pc + 2 if self.cpu_state == 'thumb' else pc + 4
            target_n, target_e = self.next_instr_lookup.get(pc, (default_next, default_next))
            ss = self.startsample + round(tdelta * i)
            es = self.startsample + round(tdelta * (i+1))

            self.put(ss, es, self.out_ann,
                     [5, ['PC 0x%08x' % pc, '0x%08x' % pc, '%08x' % pc]])

            new_loc = self.file_lookup.get(pc)
            new_src = self.source_lookup.get(pc)
            new_dis = self.disasm_lookup.get(pc)
            new_func = self.func_lookup.get(pc)

            # Report source line only when it changes.
            if self.current_loc is not None:
                if new_loc != self.current_loc[2] or new_src != self.current_loc[3]:
                    self.flush_current_loc()

            if self.current_loc is None:
                self.current_loc = [ss, es, new_loc, new_src]
            else:
                self.current_loc[1] = es

            # Report function name only when it changes.
            if self.current_func is not None:
                if new_func != self.current_func[2]:
                    self.flush_current_func()

            if self.current_func is None:
                self.current_func = [ss, es, new_func]
            else:
                self.current_func[1] = es

            # Report instruction every time.
            if new_dis:
                if exec_status:
                    a = [6, ['Executed: ' + new_dis, new_dis, new_dis.split()[0]]]
                else:
                    a = [7, ['Not executed: ' + new_dis, new_dis, new_dis.split()[0]]]
                self.put(ss, es, self.out_ann, a)

            if exec_status:
                self.current_pc = target_e
            else:
                self.current_pc = target_n

    def get_packet_type(self, byte):
        '''Identify packet type based on its first byte.
           See ARM IHI0014Q section "ETMv3 Signal Protocol" "Packet Types"
        '''
        if byte & 0x01 == 0x01:
            return 'branch'
        elif byte == 0x00:
            return 'a_sync'
        elif byte == 0x04:
            return 'cyclecount'
        elif byte == 0x08:
            return 'i_sync'
        elif byte == 0x0C:
            return 'trigger'
        elif byte & 0xF3 in (0x20, 0x40, 0x60):
            return 'ooo_data'
        elif byte == 0x50:
            return 'store_failed'
        elif byte == 0x70:
            return 'i_sync'
        elif byte & 0xDF in (0x54, 0x58, 0x5C):
            return 'ooo_place'
        elif byte == 0x3C:
            return 'vmid'
        elif byte & 0xD3 == 0x02:
            return 'data'
        elif byte & 0xFB == 0x42:
            return 'timestamp'
        elif byte == 0x62:
            return 'data_suppressed'
        elif byte == 0x66:
            return 'ignore'
        elif byte & 0xEF == 0x6A:
            return 'value_not_traced'
        elif byte == 0x6E:
            return 'context_id'
        elif byte == 0x76:
            return 'exception_exit'
        elif byte == 0x7E:
            return 'exception_entry'
        elif byte & 0x81 == 0x80:
            return 'p_header'
        else:
            return 'unknown'

    def fallback(self, buf):
        ptype = self.get_packet_type(buf[0])
        return [0, ['Unhandled ' + ptype + ': ' + ' '.join(['%02x' % b for b in buf])]]

    def handle_a_sync(self, buf):
        if buf[-1] == 0x80:
            return [0, ['Synchronization']]

    def handle_exception_exit(self, buf):
        return [2, ['Exception exit']]

    def handle_exception_entry(self, buf):
        return [2, ['Exception entry']]

    def handle_i_sync(self, buf):
        contextid_bytes = 0 # This is the default ETM config.

        if len(buf) < 6:
            return None # Packet definitely not full yet.

        if buf[0] == 0x08: # No cycle count.
            cyclecount = None
            idx = 1 + contextid_bytes # Index to info byte.
        elif buf[0] == 0x70: # With cycle count.
            cyclecount, cyclen = parse_varint(buf[1:6])
            idx = 1 + cyclen + contextid_bytes

        if len(buf) <= idx + 4:
            return None
        infobyte = buf[idx]
        addr = parse_uint(buf[idx+1:idx+5])

        reasoncode = (infobyte >> 5) & 3
        reason = ('Periodic', 'Tracing enabled', 'After overflow', 'Exit from debug')[reasoncode]
        jazelle = (infobyte >> 4) & 1
        nonsec = (infobyte >> 3) & 1
        altisa = (infobyte >> 2) & 1
        hypervisor = (infobyte >> 1) & 1
        thumb = addr & 1
        addr &= 0xFFFFFFFE

        if reasoncode == 0 and self.current_pc != addr:
            self.put(self.startsample, self.prevsample, self.out_ann,
                     [0, ['WARN: Unexpected PC change 0x%08x -> 0x%08x' % \
                     (self.current_pc, addr)]])
        elif reasoncode != 0:
            # Reset location when the trace has been interrupted.
            self.flush_current_loc()
            self.flush_current_func()

        self.last_branch = addr
        self.current_pc = addr

        if jazelle:
            self.cpu_state = 'jazelle'
        elif thumb:
            self.cpu_state = 'thumb'
        else:
            self.cpu_state = 'arm'

        cycstr = ''
        if cyclecount is not None:
            cycstr = ', cyclecount %d' % cyclecount

        if infobyte & 0x80: # LSIP packet
            self.put(self.startsample, self.prevsample, self.out_ann,
                     [0, ['WARN: LSIP I-Sync packet not implemented']])

        return [0, ['I-Sync: %s, PC 0x%08x, %s state%s' % \
                    (reason, addr, self.cpu_state, cycstr), \
                    'I-Sync: %s 0x%08x' % (reason, addr)]]

    def handle_trigger(self, buf):
        return [0, ['Trigger event', 'Trigger']]

    def handle_p_header(self, buf):
        # Only non cycle-accurate mode supported.
        if buf[0] & 0x83 == 0x80:
            n = (buf[0] >> 6) & 1
            e = (buf[0] >> 2) & 15

            self.instructions_executed([1] * e + [0] * n)

            if n:
                return [3, ['%d instructions executed, %d skipped due to ' \
                            'condition codes' % (e, n),
                            '%d ins exec, %d skipped' % (e, n),
                            '%dE,%dN' % (e, n)]]
            else:
                return [3, ['%d instructions executed' % e,
                            '%d ins exec' % e, '%dE' % e]]
        elif buf[0] & 0xF3 == 0x82:
            i1 = (buf[0] >> 3) & 1
            i2 = (buf[0] >> 2) & 1
            self.instructions_executed([not i1, not i2])
            txt1 = ('executed', 'skipped')
            txt2 = ('E', 'S')
            return [3, ['Instruction 1 %s, instruction 2 %s' % (txt1[i1], txt1[i2]),
                        'I1 %s, I2 %s' % (txt2[i1], txt2[i2]),
                        '%s,%s' % (txt2[i1], txt2[i2])]]
        else:
            return self.fallback(buf)

    def handle_branch(self, buf):
        if buf[-1] & 0x80 != 0x00:
            return None # Not complete yet.

        brinfo = parse_branch_addr(buf, self.last_branch, self.cpu_state,
                                   self.options['branch_enc'])

        if brinfo is None:
            return None # Not complete yet.

        addr, addrlen, cpu_state, exc_info = brinfo
        self.last_branch = addr
        self.current_pc = addr

        txt = ''

        if cpu_state != self.cpu_state:
            txt += ', to %s state' % cpu_state
            self.cpu_state = cpu_state

        annidx = 1

        if exc_info:
            annidx = 2
            ns, exc, cancel, altisa, hyp, resume = exc_info
            if ns:
                txt += ', to non-secure state'
            if exc:
                if exc < len(exc_names):
                    txt += ', exception %s' % exc_names[exc]
                else:
                    txt += ', exception 0x%02x' % exc
            if cancel:
                txt += ', instr cancelled'
            if altisa:
                txt += ', to AltISA'
            if hyp:
                txt += ', to hypervisor'
            if resume:
                txt += ', instr resume 0x%02x' % resume

        return [annidx, ['Branch to 0x%08x%s' % (addr, txt),
                         'B 0x%08x%s' % (addr, txt)]]

    def decode(self, ss, es, data):
        ptype, rxtx, pdata = data

        if ptype != 'DATA':
            return

        # Reset packet if there is a long pause between bytes.
        # This helps getting the initial synchronization.
        self.byte_len = es - ss
        if ss - self.prevsample > 16 * self.byte_len:
            self.flush_current_loc()
            self.flush_current_func()
            self.buf = []
        self.prevsample = es

        self.buf.append(pdata[0])

        # Store the start time of the packet.
        if len(self.buf) == 1:
            self.startsample = ss

        # Keep separate buffer for detection of sync packets.
        # Sync packets override everything else, so that we can regain sync
        # even if some packets are corrupted.
        self.syncbuf = self.syncbuf[-4:] + [pdata[0]]
        if self.syncbuf == [0x00, 0x00, 0x00, 0x00, 0x80]:
            self.buf = self.syncbuf
            self.syncbuf = []

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
