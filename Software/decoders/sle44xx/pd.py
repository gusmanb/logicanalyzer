##
## This file is part of the libsigrokdecode project.
##
## Copyright (C) 2019 Federico Cerutti <federico@ceres-c.it>
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

from common.srdhelper import bitpack_lsb
import sigrokdecode as srd

class Pin:
    RST, CLK, IO, = range(3)

class Ann:
    RESET_SYM, INTR_SYM, START_SYM, STOP_SYM, BIT_SYM, \
    ATR_BYTE, CMD_BYTE, OUT_BYTE, PROC_BYTE, \
    ATR_DATA, CMD_DATA, OUT_DATA, PROC_DATA, \
    = range(13)

class Bin:
    BYTES, = range(1)

class Decoder(srd.Decoder):
    api_version = 3
    id = 'sle44xx'
    name = 'SLE 44xx'
    longname = 'SLE44xx memory card'
    desc = 'SLE 4418/28/32/42 memory card serial protocol'
    license = 'gplv2+'
    inputs = ['logic']
    outputs = []
    tags = ['Memory']
    channels = (
        {'id': 'rst', 'name': 'RST', 'desc': 'Reset line'},
        {'id': 'clk', 'name': 'CLK', 'desc': 'Clock line'},
        {'id': 'io', 'name': 'I/O', 'desc': 'I/O data line'},
    )
    annotations = (
        ('reset_sym', 'Reset Symbol'),
        ('intr_sym', 'Interrupt Symbol'),
        ('start_sym', 'Start Symbol'),
        ('stop_sym', 'Stop Symbol'),
        ('bit_sym', 'Bit Symbol'),
        ('atr_byte', 'ATR Byte'),
        ('cmd_byte', 'Command Byte'),
        ('out_byte', 'Outgoing Byte'),
        ('proc_byte', 'Processing Byte'),
        ('atr_data', 'ATR data'),
        ('cmd_data', 'Command data'),
        ('out_data', 'Outgoing data'),
        ('proc_data', 'Processing data'),
    )
    annotation_rows = (
        ('symbols', 'Symbols', (Ann.RESET_SYM, Ann.INTR_SYM,
            Ann.START_SYM, Ann.STOP_SYM, Ann.BIT_SYM,)),
        ('fields', 'Fields', (Ann.ATR_BYTE,
            Ann.CMD_BYTE, Ann.OUT_BYTE, Ann.PROC_BYTE,)),
        ('operations', 'Operations', (Ann.ATR_DATA,
            Ann.CMD_DATA, Ann.OUT_DATA, Ann.PROC_DATA,)),
    )
    binary = (
        ('bytes', 'Bytes'),
    )

    def __init__(self):
        self.reset()

    def reset(self):
        self.samplerate = None
        self.max_addr = 256
        self.bits = []
        self.atr_bytes = []
        self.cmd_bytes = []
        self.cmd_proc = None
        self.out_len = None
        self.out_bytes = []
        self.proc_state = None
        self.state = None

    def metadata(self, key, value):
        if key == srd.SRD_CONF_SAMPLERATE:
            self.samplerate = value

    def start(self):
        self.out_ann = self.register(srd.OUTPUT_ANN)
        self.out_binary = self.register(srd.OUTPUT_BINARY)

    def putx(self, ss, es, cls, data):
        self.put(ss, es, self.out_ann, [cls, data,])

    def putb(self, ss, es, cls , data):
        self.put(ss, es, self.out_binary, [cls, data,])

    def snums_to_usecs(self, snum_count):
        if not self.samplerate:
            return None
        snums_per_usec = self.samplerate / 1e6
        usecs = snum_count / snums_per_usec
        return usecs

    def lookup_proto_ann_txt(self, key, variables):
        ann = {
            'RESET_SYM': [Ann.RESET_SYM, 'Reset', 'R',],
            'INTR_SYM': [Ann.INTR_SYM, 'Interrupt', 'Intr', 'I',],
            'START_SYM': [Ann.START_SYM, 'Start', 'ST', 'S',],
            'STOP_SYM': [Ann.STOP_SYM, 'Stop', 'SP', 'P',],
            'BIT_SYM': [Ann.BIT_SYM, '{bit}',],
            'ATR_BYTE': [Ann.ATR_BYTE,
                'Answer To Reset: {data:02x}',
                'ATR: {data:02x}',
                '{data:02x}',
            ],
            'CMD_BYTE': [Ann.CMD_BYTE,
                'Command: {data:02x}',
                'Cmd: {data:02x}',
                '{data:02x}',
            ],
            'OUT_BYTE': [Ann.OUT_BYTE,
                'Outgoing data: {data:02x}',
                'Data: {data:02x}',
                '{data:02x}',
            ],
            'PROC_BYTE': [Ann.PROC_BYTE,
                'Internal processing: {data:02x}',
                'Proc: {data:02x}',
                '{data:02x}',
            ],
            'ATR_DATA': [Ann.ATR_DATA,
                'Answer To Reset: {data}',
                'ATR: {data}',
                '{data}',
            ],
            'CMD_DATA': [Ann.CMD_DATA,
                'Command: {data}',
                'Cmd: {data}',
                '{data}',
            ],
            'OUT_DATA': [Ann.OUT_DATA,
                'Outgoing: {data}',
                'Out: {data}',
                '{data}',
            ],
            'PROC_DATA': [Ann.PROC_DATA,
                'Processing: {data}',
                'Proc: {data}',
                '{data}',
            ],
        }.get(key, None)
        if ann is None:
            return None, []
        cls, texts = ann[0], ann[1:]
        texts = [t.format(**variables) for t in texts]
        return cls, texts

    def text_for_accu_bytes(self, accu):
        if not accu:
            return None, None, None, None
        ss, es = accu[0][1], accu[-1][2]
        data = [a[0] for a in accu]
        text = " ".join(['{:02x}'.format(a) for a in data])
        return ss, es, data, text

    def flush_queued(self):
        '''Flush previously accumulated operations details.'''

        # Can be called when either the completion of an operation got
        # detected (reliably), or when some kind of reset condition was
        # met while a potential previously observed operation has not
        # been postprocessed yet (best effort). Should not harm when the
        # routine gets invoked while no data was collected yet, or was
        # flushed already.
        # BEWARE! Will void internal state. Should really only get called
        # "between operations", NOT between fields of an operation.

        if self.atr_bytes:
            key = 'ATR_DATA'
            ss, es, _, text = self.text_for_accu_bytes(self.atr_bytes)
            cls, texts = self.lookup_proto_ann_txt(key, {'data': text})
            self.putx(ss, es, cls, texts)

        if self.cmd_bytes:
            key = 'CMD_DATA'
            ss, es, _, text = self.text_for_accu_bytes(self.cmd_bytes)
            cls, texts = self.lookup_proto_ann_txt(key, {'data': text})
            self.putx(ss, es, cls, texts)

        if self.out_bytes:
            key = 'OUT_DATA'
            ss, es, _, text = self.text_for_accu_bytes(self.out_bytes)
            cls, texts = self.lookup_proto_ann_txt(key, {'data': text})
            self.putx(ss, es, cls, texts)

        if self.proc_state:
            key = 'PROC_DATA'
            ss = self.proc_state['ss']
            es = self.proc_state['es']
            clk = self.proc_state['clk']
            high = self.proc_state['io1']
            text = '{clk} clocks, I/O {high}'.format(clk = clk, high = int(high))
            usecs = self.snums_to_usecs(es - ss)
            if usecs:
                msecs = usecs / 1000
                text = '{msecs:.2f} ms, {text}'.format(msecs = msecs, text = text)
            cls, texts = self.lookup_proto_ann_txt(key, {'data': text})
            self.putx(ss, es, cls, texts)

        self.atr_bytes = None
        self.cmd_bytes = None
        self.cmd_proc = None
        self.out_len = None
        self.out_bytes = None
        self.proc_state = None
        self.state = None

    def handle_reset(self, ss, es, has_clk):
        self.flush_queued()
        key = '{}_SYM'.format('RESET' if has_clk else 'INTR')
        cls, texts = self.lookup_proto_ann_txt(key, {})
        self.putx(ss, es, cls, texts)
        self.bits = []
        self.state = 'ATR' if has_clk else None

    def handle_command(self, ss, is_start):
        if is_start:
            self.flush_queued()
        key = '{}_SYM'.format('START' if is_start else 'STOP')
        cls, texts = self.lookup_proto_ann_txt(key, {})
        self.putx(ss, ss, cls, texts)
        self.bits = []
        self.state = 'CMD' if is_start else 'DATA'

    def command_check(self, ctrl, addr, data):
        '''Interpret CTRL/ADDR/DATA command entry.'''

        # See the Siemens Datasheet section 2.3 Commands. The abbreviated
        # text variants are my guesses, terse for readability at coarser
        # zoom levels.
        codes_table = {
            0x30: {
                'fmt': [
                    'read main memory, addr {addr:02x}',
                    'RD-M @{addr:02x}',
                ],
                'len': lambda ctrl, addr, data: self.max_addr - addr,
            },
            0x31: {
                'fmt': [
                    'read security memory',
                    'RD-S',
                ],
                'len': 4,
            },
            0x33: {
                'fmt': [
                    'compare verification data, addr {addr:02x}, data {data:02x}',
                    'CMP-V @{addr:02x} ={data:02x}',
                ],
                'proc': True,
            },
            0x34: {
                'fmt': [
                    'read protection memory, addr {addr:02x}',
                    'RD-P @{addr:02x}',
                ],
                'len': 4,
            },
            0x38: {
                'fmt': [
                    'update main memory, addr {addr:02x}, data {data:02x}',
                    'WR-M @{addr:02x} ={data:02x}',
                ],
                'proc': True,
            },
            0x39: {
                'fmt': [
                    'update security memory, addr {addr:02x}, data {data:02x}',
                    'WR-S @{addr:02x} ={data:02x}',
                ],
                'proc': True,
            },
            0x3c: {
                'fmt': [
                    'write protection memory, addr {addr:02x}, data {data:02x}',
                    'WR-P @{addr:02x} ={data:02x}',
                ],
                'proc': True,
            },
        }
        code = codes_table.get(ctrl, {})
        dflt_fmt = [
            'unknown, ctrl {ctrl:02x}, addr {addr:02x}, data {data:02x}',
            'UNK-{ctrl:02x} @{addr:02x}, ={data:02x}',
        ]
        fmt = code.get('fmt', dflt_fmt)
        if not isinstance(fmt, (list, tuple,)):
            fmt = [fmt,]
        texts = [f.format(ctrl = ctrl, addr = addr, data = data) for f in fmt]
        length = code.get('len', None)
        if callable(length):
            length = length(ctrl, addr, data)
        is_proc = code.get('proc', False)
        return texts, length, is_proc

    def processing_start(self, ss, es, io_high):
        self.proc_state = {
            'ss': ss or es,
            'es': es or ss,
            'clk': 0,
            'io1': bool(io_high),
        }

    def processing_update(self, es, clk_inc, io_high):
        if es is not None and es > self.proc_state['es']:
            self.proc_state['es'] = es
        self.proc_state['clk'] += clk_inc
        if io_high:
            self.proc_state['io1'] = True

    def handle_data_byte(self, ss, es, data, bits):
        '''Accumulate CMD or OUT data bytes.'''

        if self.state == 'ATR':
            if not self.atr_bytes:
                self.atr_bytes = []
            self.atr_bytes.append([data, ss, es, bits,])
            if len(self.atr_bytes) == 4:
                self.flush_queued()
            return

        if self.state == 'CMD':
            if not self.cmd_bytes:
                self.cmd_bytes = []
            self.cmd_bytes.append([data, ss, es, bits,])
            if len(self.cmd_bytes) == 3:
                ctrl, addr, data = [c[0] for c in self.cmd_bytes]
                texts, length, proc = self.command_check(ctrl, addr, data)
                # Immediately emit the annotation to not lose the text,
                # and to support zoom levels for this specific case.
                ss, es = self.cmd_bytes[0][1], self.cmd_bytes[-1][2]
                cls = Ann.CMD_DATA
                self.putx(ss, es, cls, texts)
                self.cmd_bytes = []
                # Prepare to continue either at OUT or PROC after CMD.
                self.out_len = length
                self.cmd_proc = bool(proc)
                self.state = None
            return

        if self.state == 'OUT':
            if not self.out_bytes:
                self.out_bytes = []
            self.out_bytes.append([data, ss, es, bits,])
            if self.out_len is not None and len(self.out_bytes) == self.out_len:
                self.flush_queued()
            return

    def handle_data_bit(self, ss, es, bit):
        '''Gather 8 bits of data (or track processing progress).'''

        # Switch late from DATA to either OUT or PROC. We can tell the
        # type and potentially fixed length at the end of CMD already,
        # but a START/STOP condition may void this information. So we
        # do the switch at the first data bit after CMD.
        # In the OUT case data bytes get accumulated, until either the
        # expected byte count is reached, or another CMD starts. In the
        # PROC case a high I/O level terminates execution.
        if self.state == 'DATA':
            if self.out_len:
                self.state = 'OUT'
            elif self.cmd_proc:
                self.state = 'PROC'
                self.processing_start(ss or es, es or ss, bit == 1)
            else:
                # Implementor's note: Handle unknown situations like
                # outgoing data bytes, for the user's convenience. This
                # will show OUT bytes even if it's just processing CLK
                # cycles with constant or irrelevant I/O bit patterns.
                self.state = 'OUT'
        if self.state == 'PROC':
            high = bit == 1
            if ss is not None:
                self.processing_update(ss, 0, high)
            if es is not None:
                self.processing_update(es, 1, high)
            if high:
                self.flush_queued()
            return

        # This routine gets called two times per bit value. Track the
        # bit's value and ss timestamp when the bit period starts. And
        # update the es timestamp at the end of the bit's validity.
        if ss is not None:
            self.bits.append([bit, ss, es or ss])
            return
        if es is None:
            # Unexpected invocation. Could be a glitch or invalid input
            # data, or an interaction with RESET/START/STOP conditions.
            self.bits = []
            return
        if not self.bits:
            return
        if bit is not None:
            self.bits[-1][0] = bit
            # TODO Check for consistent bit level at ss and es when
            # the information was available? Is bit data sampled at
            # different clock edges depending whether data is sent
            # or received?
        self.bits[-1][2] = es
        # Emit the bit's annotation. See if a byte was received.
        bit, ss, es = self.bits[-1]
        cls, texts = self.lookup_proto_ann_txt('BIT_SYM', {'bit': bit})
        self.putx(ss, es, cls, texts)
        if len(self.bits) < 8:
            return

        # Get the data byte value, and the byte's ss/es. Emit the byte's
        # annotation and binary output. Pass the byte to upper layers.
        # TODO Vary annotation classes with the byte's position within
        # a field? To tell CTRL/ADDR/DATA of a CMD entry apart?
        bits = self.bits
        self.bits = []
        data = bitpack_lsb(bits, 0)
        ss = bits[0][1]
        es = bits[-1][2]

        key = '{}_BYTE'.format(self.state)
        cls, texts = self.lookup_proto_ann_txt(key, {'data': data})
        if cls:
            self.putx(ss, es, cls, texts)
        self.putb(ss, es, Bin.BYTES, bytes([data]))

        self.handle_data_byte(ss, es, data, bits)

    def decode(self):
        '''Decoder's main data interpretation loop.'''

        # Signal conditions tracked by the protocol decoder:
        # - Rising and falling RST edges, which span the width of a
        #   high-active RESET pulse. RST has highest priority, no
        #   other activity can take place in this period.
        # - Rising and falling CLK edges when RST is active. The
        #   CLK pulse when RST is asserted will reset the card's
        #   address counter. RST alone can terminate memory reads.
        # - Rising and falling CLK edges when RST is inactive. This
        #   determines the period where BIT values are valid.
        # - I/O edges during high CLK. These are START and STOP
        #   conditions that tell COMMAND and DATA phases apart.
        # - Rise of I/O during internal processing. This expression
        #   is an unconditional part of the .wait() condition set. It
        #   is assumed that skipping this match in many cases is more
        #   efficient than the permanent re-construction of the .wait()
        #   condition list in every loop iteration, and preferrable to
        #   the maintainance cost of duplicating RST and CLK handling
        #   when checking I/O during internal processing.
        (
            COND_RESET_START, COND_RESET_STOP,
            COND_RSTCLK_START, COND_RSTCLK_STOP,
            COND_DATA_START, COND_DATA_STOP,
            COND_CMD_START, COND_CMD_STOP,
            COND_PROC_IOH,
        ) = range(9)
        conditions = [
            {Pin.RST: 'r'},
            {Pin.RST: 'f'},
            {Pin.RST: 'h', Pin.CLK: 'r'},
            {Pin.RST: 'h', Pin.CLK: 'f'},
            {Pin.RST: 'l', Pin.CLK: 'r'},
            {Pin.RST: 'l', Pin.CLK: 'f'},
            {Pin.CLK: 'h', Pin.IO: 'f'},
            {Pin.CLK: 'h', Pin.IO: 'r'},
            {Pin.RST: 'l', Pin.IO: 'r'},
        ]

        ss_reset = es_reset = ss_clk = es_clk = None
        while True:

            is_outgoing = self.state == 'OUT'
            is_processing = self.state == 'PROC'
            pins = self.wait(conditions)
            io = pins[Pin.IO]

            # Handle RESET conditions, including an optional CLK pulse
            # while RST is asserted.
            if self.matched[COND_RESET_START]:
                self.flush_queued()
                ss_reset = self.samplenum
                es_reset = ss_clk = es_clk = None
                continue
            if self.matched[COND_RESET_STOP]:
                es_reset = self.samplenum
                self.handle_reset(ss_reset or 0, es_reset, ss_clk and es_clk)
                ss_reset = es_reset = ss_clk = es_clk = None
                continue
            if self.matched[COND_RSTCLK_START]:
                ss_clk = self.samplenum
                es_clk = None
                continue
            if self.matched[COND_RSTCLK_STOP]:
                es_clk = self.samplenum
                continue

            # Handle data bits' validity boundaries. Also covers the
            # periodic check for high I/O level and update of details
            # during internal processing.
            if self.matched[COND_DATA_START]:
                self.handle_data_bit(self.samplenum, None, io)
                continue
            if self.matched[COND_DATA_STOP]:
                self.handle_data_bit(None, self.samplenum, None)
                continue

            # Additional check for idle I/O during internal processing,
            # independent of CLK edges this time. This assures that the
            # decoder ends processing intervals as soon as possible, at
            # the most precise timestamp.
            if is_processing and self.matched[COND_PROC_IOH]:
                self.handle_data_bit(self.samplenum, self.samplenum, io)
                continue

            # The START/STOP conditions are only applicable outside of
            # "outgoing data" or "internal processing" periods. This is
            # what the data sheet specifies.
            if not is_outgoing and not is_processing:
                if self.matched[COND_CMD_START]:
                    self.handle_command(self.samplenum, True)
                    continue
                if self.matched[COND_CMD_STOP]:
                    self.handle_command(self.samplenum, False)
                    continue
