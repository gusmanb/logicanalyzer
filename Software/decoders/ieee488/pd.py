##
## This file is part of the libsigrokdecode project.
##
## Copyright (C) 2016 Rudolf Reuter <reuterru@arcor.de>
## Copyright (C) 2017 Marcus Comstedt <marcus@mc.pp.se>
## Copyright (C) 2019 Gerhard Sittig <gerhard.sittig@gmx.net>
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

# This file was created from earlier implementations of the 'gpib' and
# the 'iec' protocol decoders. It combines the parallel and the serial
# transmission variants in a single instance with optional inputs for
# maximum code re-use.

# TODO
# - Extend annotations for improved usability.
#   - Keep talkers' data streams on separate annotation rows? Is this useful
#     here at the GPIB level, or shall stacked decoders dispatch these? May
#     depend on how often captures get inspected which involve multiple peers.
#   - Make serial bit annotations optional? Could slow down interactive
#     exploration for long captures (see USB).
# - Move the inlined Commodore IEC peripherals support to a stacked decoder
#   when more peripherals get added.
# - SCPI over GPIB may "represent somewhat naturally" here already when
#   text lines are a single run of data at the GPIB layer (each line between
#   the address spec and either EOI or ATN). So a stacked SCPI decoder may
#   only become necessary when the text lines' content shall get inspected.

import sigrokdecode as srd
from common.srdhelper import bitpack

'''
OUTPUT_PYTHON format for stacked decoders:

General packet format:
[<ptype>, <addr>, <pdata>]

This is the list of <ptype>s and their respective <pdata> values:

Raw bits and bytes at the physical transport level:
 - 'IEC_BIT': <addr> is not applicable, <pdata> is the transport's bit value.
 - 'GPIB_RAW': <addr> is not applicable, <pdata> is the transport's
   byte value. Data bytes are in the 0x00-0xff range, command/address
   bytes are in the 0x100-0x1ff range.

GPIB level byte fields (commands, addresses, pieces of data):
 - 'COMMAND': <addr> is not applicable, <pdata> is the command's byte value.
 - 'LISTEN': <addr> is the listener address (0-30), <pdata> is the raw
   byte value (including the 0x20 offset).
 - 'TALK': <addr> is the talker address (0-30), <pdata> is the raw byte
   value (including the 0x40 offset).
 - 'SECONDARY': <addr> is the secondary address (0-31), <pdata> is the
   raw byte value (including the 0x60 offset).
 - 'MSB_SET': <addr> as well as <pdata> are the raw byte value (including
   the 0x80 offset). This usually does not happen for GPIB bytes with ATN
   active, but was observed with the IEC bus and Commodore floppy drives,
   when addressing channels within the device.
 - 'DATA_BYTE': <addr> is the talker address (when available), <pdata>
   is the raw data byte (transport layer, ATN inactive).
 - 'PPOLL': <addr> is not applicable, <pdata> is a list of bit indices
   (DIO1 to DIO8 order) which responded to the PP request.

Extracted payload information (peers and their communicated data):
 - 'TALK_LISTEN': <addr> is the current talker, <pdata> is the list of
   current listeners. These updates for the current "connected peers"
   are sent when the set of peers changes, i.e. after talkers/listeners
   got selected or deselected. Of course the data only covers what could
   be gathered from the input data. Some controllers may not explicitly
   address themselves, or captures may not include an early setup phase.
 - 'TALKER_BYTES': <addr> is the talker address (when available), <pdata>
   is the accumulated byte sequence between addressing a talker and EOI,
   or the next command/address.
 - 'TALKER_TEXT': <addr> is the talker address (when available), <pdata>
   is the accumulated text sequence between addressing a talker and EOI,
   or the next command/address.
'''

class ChannelError(Exception):
    pass

def _format_ann_texts(fmts, **args):
    if not fmts:
        return None
    return [fmt.format(**args) for fmt in fmts]

_cmd_table = {
    # Command codes in the 0x00-0x1f range.
    0x01: ['Go To Local', 'GTL'],
    0x04: ['Selected Device Clear', 'SDC'],
    0x05: ['Parallel Poll Configure', 'PPC'],
    0x08: ['Global Execute Trigger', 'GET'],
    0x09: ['Take Control', 'TCT'],
    0x11: ['Local Lock Out', 'LLO'],
    0x14: ['Device Clear', 'DCL'],
    0x15: ['Parallel Poll Unconfigure', 'PPU'],
    0x18: ['Serial Poll Enable', 'SPE'],
    0x19: ['Serial Poll Disable', 'SPD'],
    # Unknown type of command.
    None: ['Unknown command 0x{cmd:02x}', 'command 0x{cmd:02x}', 'cmd {cmd:02x}', 'C{cmd_ord:c}'],
    # Special listener/talker "addresses" (deselecting previous peers).
    0x3f: ['Unlisten', 'UNL'],
    0x5f: ['Untalk', 'UNT'],
}

def _is_command(b):
    # Returns a tuple of booleans (or None when not applicable) whether
    # the raw GPIB byte is: a command, an un-listen, an un-talk command.
    if b in range(0x00, 0x20):
        return True, None, None
    if b in range(0x20, 0x40) and (b & 0x1f) == 31:
        return True, True, False
    if b in range(0x40, 0x60) and (b & 0x1f) == 31:
        return True, False, True
    return False, None, None

def _is_listen_addr(b):
    if b in range(0x20, 0x40):
        return b & 0x1f
    return None

def _is_talk_addr(b):
    if b in range(0x40, 0x60):
        return b & 0x1f
    return None

def _is_secondary_addr(b):
    if b in range(0x60, 0x80):
        return b & 0x1f
    return None

def _is_msb_set(b):
    if b & 0x80:
        return b
    return None

def _get_raw_byte(b, atn):
    # "Decorate" raw byte values for stacked decoders.
    return b | 0x100 if atn else b

def _get_raw_text(b, atn):
    return ['{leader}{data:02x}'.format(leader = '/' if atn else '', data = b)]

def _get_command_texts(b):
    fmts = _cmd_table.get(b, None)
    known = fmts is not None
    if not fmts:
        fmts = _cmd_table.get(None, None)
    if not fmts:
        return known, None
    return known, _format_ann_texts(fmts, cmd = b, cmd_ord = ord('0') + b)

def _get_address_texts(b):
    laddr = _is_listen_addr(b)
    taddr = _is_talk_addr(b)
    saddr = _is_secondary_addr(b)
    msb = _is_msb_set(b)
    fmts = None
    if laddr is not None:
        fmts = ['Listen {addr:d}', 'L {addr:d}', 'L{addr_ord:c}']
        addr = laddr
    elif taddr is not None:
        fmts = ['Talk {addr:d}', 'T {addr:d}', 'T{addr_ord:c}']
        addr = taddr
    elif saddr is not None:
        fmts = ['Secondary {addr:d}', 'S {addr:d}', 'S{addr_ord:c}']
        addr = saddr
    elif msb is not None: # For IEC bus compat.
        fmts = ['Secondary {addr:d}', 'S {addr:d}', 'S{addr_ord:c}']
        addr = msb
    return _format_ann_texts(fmts, addr = addr, addr_ord = ord('0') + addr)

def _get_data_text(b):
    # TODO Move the table of ASCII control characters to a common location?
    # TODO Move the "printable with escapes" logic to a common helper?
    _control_codes = {
        0x00: 'NUL',
        0x01: 'SOH',
        0x02: 'STX',
        0x03: 'ETX',
        0x04: 'EOT',
        0x05: 'ENQ',
        0x06: 'ACK',
        0x07: 'BEL',
        0x08: 'BS',
        0x09: 'TAB',
        0x0a: 'LF',
        0x0b: 'VT',
        0x0c: 'FF',
        0x0d: 'CR',
        0x0e: 'SO',
        0x0f: 'SI',
        0x10: 'DLE',
        0x11: 'DC1',
        0x12: 'DC2',
        0x13: 'DC3',
        0x14: 'DC4',
        0x15: 'NAK',
        0x16: 'SYN',
        0x17: 'ETB',
        0x18: 'CAN',
        0x19: 'EM',
        0x1a: 'SUB',
        0x1b: 'ESC',
        0x1c: 'FS',
        0x1d: 'GS',
        0x1e: 'RS',
        0x1f: 'US',
    }
    # Yes, exclude 0x7f (DEL) here. It's considered non-printable.
    if b in range(0x20, 0x7f) and b not in ('[', ']'):
        return '{:s}'.format(chr(b))
    elif b in _control_codes:
        return '[{:s}]'.format(_control_codes[b])
    # Use a compact yet readable and unambigous presentation for bytes
    # which contain non-printables. The format that is used here is
    # compatible with 93xx EEPROM and UART decoders.
    return '[{:02x}]'.format(b)

(
    PIN_DIO1, PIN_DIO2, PIN_DIO3, PIN_DIO4,
    PIN_DIO5, PIN_DIO6, PIN_DIO7, PIN_DIO8,
    PIN_EOI, PIN_DAV, PIN_NRFD, PIN_NDAC,
    PIN_IFC, PIN_SRQ, PIN_ATN, PIN_REN,
    PIN_CLK,
) = range(17)
PIN_DATA = PIN_DIO1

(
    ANN_RAW_BIT, ANN_RAW_BYTE,
    ANN_CMD, ANN_LADDR, ANN_TADDR, ANN_SADDR, ANN_DATA,
    ANN_EOI,
    ANN_PP,
    ANN_TEXT,
    # TODO Want to provide one annotation class per talker address (0-30)?
    ANN_IEC_PERIPH,
    ANN_WARN,
) = range(12)

(
    BIN_RAW,
    BIN_DATA,
    # TODO Want to provide one binary annotation class per talker address (0-30)?
) = range(2)

class Decoder(srd.Decoder):
    api_version = 3
    id = 'ieee488'
    name = 'IEEE-488'
    longname = 'IEEE-488 GPIB/HPIB/IEC'
    desc = 'IEEE-488 General Purpose Interface Bus (GPIB/HPIB or IEC).'
    license = 'gplv2+'
    inputs = ['logic']
    outputs = ['ieee488']
    tags = ['PC', 'Retro computing']
    channels = (
        {'id': 'dio1' , 'name': 'DIO1/DATA',
            'desc': 'Data I/O bit 1, or serial data'},
    )
    optional_channels = (
        {'id': 'dio2' , 'name': 'DIO2', 'desc': 'Data I/O bit 2'},
        {'id': 'dio3' , 'name': 'DIO3', 'desc': 'Data I/O bit 3'},
        {'id': 'dio4' , 'name': 'DIO4', 'desc': 'Data I/O bit 4'},
        {'id': 'dio5' , 'name': 'DIO5', 'desc': 'Data I/O bit 5'},
        {'id': 'dio6' , 'name': 'DIO6', 'desc': 'Data I/O bit 6'},
        {'id': 'dio7' , 'name': 'DIO7', 'desc': 'Data I/O bit 7'},
        {'id': 'dio8' , 'name': 'DIO8', 'desc': 'Data I/O bit 8'},
        {'id': 'eoi', 'name': 'EOI', 'desc': 'End or identify'},
        {'id': 'dav', 'name': 'DAV', 'desc': 'Data valid'},
        {'id': 'nrfd', 'name': 'NRFD', 'desc': 'Not ready for data'},
        {'id': 'ndac', 'name': 'NDAC', 'desc': 'Not data accepted'},
        {'id': 'ifc', 'name': 'IFC', 'desc': 'Interface clear'},
        {'id': 'srq', 'name': 'SRQ', 'desc': 'Service request'},
        {'id': 'atn', 'name': 'ATN', 'desc': 'Attention'},
        {'id': 'ren', 'name': 'REN', 'desc': 'Remote enable'},
        {'id': 'clk', 'name': 'CLK', 'desc': 'Serial clock'},
    )
    options = (
        {'id': 'iec_periph', 'desc': 'Decode Commodore IEC peripherals',
            'default': 'no', 'values': ('no', 'yes')},
        {'id': 'delim', 'desc': 'Payload data delimiter',
            'default': 'eol', 'values': ('none', 'eol')},
        {'id': 'atn_parity', 'desc': 'ATN commands use parity',
            'default': 'no', 'values': ('no', 'yes')},
    )
    annotations = (
        ('bit', 'IEC bit'),
        ('raw', 'Raw byte'),
        ('cmd', 'Command'),
        ('laddr', 'Listener address'),
        ('taddr', 'Talker address'),
        ('saddr', 'Secondary address'),
        ('data', 'Data byte'),
        ('eoi', 'EOI'),
        ('pp', 'Parallel poll'),
        ('text', 'Talker text'),
        ('periph', 'IEC bus peripherals'),
        ('warning', 'Warning'),
    )
    annotation_rows = (
        ('bits', 'IEC bits', (ANN_RAW_BIT,)),
        ('raws', 'Raw bytes', (ANN_RAW_BYTE,)),
        ('gpib', 'Commands/data', (ANN_CMD, ANN_LADDR, ANN_TADDR, ANN_SADDR, ANN_DATA,)),
        ('eois', 'EOI', (ANN_EOI,)),
        ('polls', 'Polls', (ANN_PP,)),
        ('texts', 'Talker texts', (ANN_TEXT,)),
        ('periphs', 'IEC peripherals', (ANN_IEC_PERIPH,)),
        ('warnings', 'Warnings', (ANN_WARN,)),
    )
    binary = (
        ('raw', 'Raw bytes'),
        ('data', 'Talker bytes'),
    )

    def __init__(self):
        self.reset()

    def reset(self):
        self.curr_raw = None
        self.curr_atn = None
        self.curr_eoi = None
        self.latch_atn = None
        self.latch_eoi = None
        self.accu_bytes = []
        self.accu_text = []
        self.ss_raw = None
        self.es_raw = None
        self.ss_eoi = None
        self.es_eoi = None
        self.ss_text = None
        self.es_text = None
        self.ss_pp = None
        self.last_talker = None
        self.last_listener = []
        self.last_iec_addr = None
        self.last_iec_sec = None

    def start(self):
        self.out_ann = self.register(srd.OUTPUT_ANN)
        self.out_bin = self.register(srd.OUTPUT_BINARY)
        self.out_python = self.register(srd.OUTPUT_PYTHON)

    def putg(self, ss, es, data):
        self.put(ss, es, self.out_ann, data)

    def putbin(self, ss, es, data):
        self.put(ss, es, self.out_bin, data)

    def putpy(self, ss, es, ptype, addr, pdata):
        self.put(ss, es, self.out_python, [ptype, addr, pdata])

    def emit_eoi_ann(self, ss, es):
        self.putg(ss, es, [ANN_EOI, ['EOI']])

    def emit_bin_ann(self, ss, es, ann_cls, data):
        self.putbin(ss, es, [ann_cls, bytes(data)])

    def emit_data_ann(self, ss, es, ann_cls, data):
        self.putg(ss, es, [ann_cls, data])

    def emit_warn_ann(self, ss, es, data):
        self.putg(ss, es, [ANN_WARN, data])

    def flush_bytes_text_accu(self):
        if self.accu_bytes and self.ss_text is not None and self.es_text is not None:
            self.emit_bin_ann(self.ss_text, self.es_text, BIN_DATA, bytearray(self.accu_bytes))
            self.putpy(self.ss_text, self.es_text, 'TALKER_BYTES', self.last_talker, bytearray(self.accu_bytes))
            self.accu_bytes = []
        if self.accu_text and self.ss_text is not None and self.es_text is not None:
            text = ''.join(self.accu_text)
            self.emit_data_ann(self.ss_text, self.es_text, ANN_TEXT, [text])
            self.putpy(self.ss_text, self.es_text, 'TALKER_TEXT', self.last_talker, text)
            self.accu_text = []
        self.ss_text = self.es_text = None

    def check_extra_flush(self, b):
        # Optionally flush previously accumulated runs of payload data
        # according to user specified conditions.
        if self.options['delim'] == 'none':
            return
        if not self.accu_bytes:
            return

        # This implementation exlusively handles "text lines", but adding
        # support for more variants here is straight forward.
        #
        # Search for the first data byte _after_ a user specified text
        # line termination sequence was seen. The termination sequence's
        # alphabet may be variable, and the sequence may span multiple
        # data bytes. We accept either CR or LF, and combine the CR+LF
        # sequence to strive for maximum length annotations for improved
        # readability at different zoom levels. It's acceptable that this
        # implementation would also combine multiple line terminations
        # like LF+LF.
        term_chars = (10, 13)
        is_eol = b in term_chars
        had_eol = self.accu_bytes[-1] in term_chars
        if had_eol and not is_eol:
            self.flush_bytes_text_accu()

    def check_pp(self, dio = None):
        # The combination of ATN and EOI means PP (parallel poll). Track
        # this condition's start and end, and keep grabing the DIO lines'
        # state as long as the condition is seen, since DAV is not used
        # in the PP communication.
        capture_in_pp = self.curr_atn and self.curr_eoi
        decoder_in_pp = self.ss_pp is not None
        if capture_in_pp and not decoder_in_pp:
            # Phase starts. Track its ss. Start collecting DIO state.
            self.ss_pp = self.samplenum
            self.dio_pp = []
            return 'enter'
        if not capture_in_pp and decoder_in_pp:
            # Phase ends. Void its ss. Process collected DIO state.
            ss, es = self.ss_pp, self.samplenum
            dio = self.dio_pp or []
            self.ss_pp, self.dio_pp = None, None
            if ss == es:
                # False positive, caused by low oversampling.
                return 'leave'
            # Emit its annotation. Translate bit indices 0..7 for the
            # DIO1..DIO8 signals to display text. Pass bit indices in
            # the Python output for upper layers.
            #
            # TODO The presentation of this information may need more
            # adjustment. The bit positions need not translate to known
            # device addresses. Bits need not even belong to a single
            # device. Participants and their location in the DIO pattern
            # is configurable. Leave the interpretation to upper layers.
            bits = [i for i, b in enumerate(dio) if b]
            bits_text = ' '.join(['{}'.format(i + 1) for i in bits])
            dios = ['DIO{}'.format(i + 1) for i in bits]
            dios_text = ' '.join(dios or ['-'])
            text = [
                'PPOLL {}'.format(dios_text),
                'PP {}'.format(bits_text),
                'PP',
            ]
            self.emit_data_ann(ss, es, ANN_PP, text)
            self.putpy(ss, es, 'PPOLL', None, bits)
            # Cease collecting DIO state.
            return 'leave'
        if decoder_in_pp:
            # Keep collecting DIO state for each individual sample in
            # the PP phase. Logically OR all DIO values that were seen.
            # This increases robustness for low oversampling captures,
            # where DIO may no longer be asserted when ATN/EOI deassert,
            # and DIO was not asserted yet when ATN/EOI start asserting.
            if dio is None:
                dio = []
            if len(dio) > len(self.dio_pp):
                self.dio_pp.extend([ 0, ] * (len(dio) - len(self.dio_pp)))
            for i, b in enumerate(dio):
                self.dio_pp[i] |= b
            return 'keep'
        return 'idle'

    def handle_ifc_change(self, ifc):
        # Track IFC line for parallel input.
        # Assertion of IFC de-selects all talkers and listeners.
        if ifc:
            self.last_talker = None
            self.last_listener = []
            self.flush_bytes_text_accu()

    def handle_eoi_change(self, eoi):
        # Track EOI line for parallel and serial input.
        if eoi:
            self.ss_eoi = self.samplenum
            self.curr_eoi = eoi
        else:
            self.es_eoi = self.samplenum
            if self.ss_eoi and self.latch_eoi:
               self.emit_eoi_ann(self.ss_eoi, self.es_eoi)
            self.es_text = self.es_eoi
            self.flush_bytes_text_accu()
            self.ss_eoi = self.es_eoi = None
            self.curr_eoi = None

    def handle_atn_change(self, atn):
        # Track ATN line for parallel and serial input.
        self.curr_atn = atn
        if atn:
            self.flush_bytes_text_accu()

    def handle_iec_periph(self, ss, es, addr, sec, data):
        # The annotation is optional.
        if self.options['iec_periph'] != 'yes':
            return
        # Void internal state.
        if addr is None and sec is None and data is None:
            self.last_iec_addr = None
            self.last_iec_sec = None
            return
        # Grab and evaluate new input.
        _iec_addr_names = {
            # TODO Add more items here. See the "Device numbering" section
            # of the https://en.wikipedia.org/wiki/Commodore_bus page.
            8: 'Disk 0',
            9: 'Disk 1',
        }
        _iec_disk_range = range(8, 16)
        if addr is not None:
            self.last_iec_addr = addr
            name = _iec_addr_names.get(addr, None)
            if name:
                self.emit_data_ann(ss, es, ANN_IEC_PERIPH, [name])
        addr = self.last_iec_addr # Simplify subsequent logic.
        if sec is not None:
            # BEWARE! The secondary address is a full byte and includes
            # the 0x60 offset, to also work when the MSB was set.
            self.last_iec_sec = sec
            subcmd, channel = sec & 0xf0, sec & 0x0f
            channel_ord = ord('0') + channel
            if addr is not None and addr in _iec_disk_range:
                subcmd_fmts = {
                    0x60: ['Reopen {ch:d}', 'Re {ch:d}', 'R{ch_ord:c}'],
                    0xe0: ['Close {ch:d}', 'Cl {ch:d}', 'C{ch_ord:c}'],
                    0xf0: ['Open {ch:d}', 'Op {ch:d}', 'O{ch_ord:c}'],
                }.get(subcmd, None)
                if subcmd_fmts:
                    texts = _format_ann_texts(subcmd_fmts, ch = channel, ch_ord = channel_ord)
                    self.emit_data_ann(ss, es, ANN_IEC_PERIPH, texts)
        sec = self.last_iec_sec # Simplify subsequent logic.
        if data is not None:
            if addr is None or sec is None:
                return
            # TODO Process data depending on peripheral type and channel?

    def handle_data_byte(self):
        if not self.curr_atn:
            self.check_extra_flush(self.curr_raw)
        b = self.curr_raw
        texts = _get_raw_text(b, self.curr_atn)
        self.emit_data_ann(self.ss_raw, self.es_raw, ANN_RAW_BYTE, texts)
        self.emit_bin_ann(self.ss_raw, self.es_raw, BIN_RAW, b.to_bytes(1, byteorder='big'))
        self.putpy(self.ss_raw, self.es_raw, 'GPIB_RAW', None, _get_raw_byte(b, self.curr_atn))
        if self.curr_atn:
            ann_cls = None
            upd_iec = False,
            py_type = None
            py_peers = False
            if self.options['atn_parity'] == 'yes':
                par = 1 if b & 0x80 else 0
                b &= ~0x80
                ones = bin(b).count('1') + par
                if ones % 2:
                    warn_texts = ['Command parity error', 'parity', 'PAR']
                    self.emit_warn_ann(self.ss_raw, self.es_raw, warn_texts)
            is_cmd, is_unl, is_unt = _is_command(b)
            laddr = _is_listen_addr(b)
            taddr = _is_talk_addr(b)
            saddr = _is_secondary_addr(b)
            msb = _is_msb_set(b)
            if is_cmd:
                known, texts = _get_command_texts(b)
                if not known:
                    warn_texts = ['Unknown GPIB command', 'unknown', 'UNK']
                    self.emit_warn_ann(self.ss_raw, self.es_raw, warn_texts)
                ann_cls = ANN_CMD
                py_type, py_addr = 'COMMAND', None
                if is_unl:
                    self.last_listener = []
                    py_peers = True
                if is_unt:
                    self.last_talker = None
                    py_peers = True
                if is_unl or is_unt:
                    upd_iec = True, None, None, None
            elif laddr is not None:
                addr = laddr
                texts = _get_address_texts(b)
                ann_cls = ANN_LADDR
                py_type, py_addr = 'LISTEN', addr
                if addr == self.last_talker:
                    self.last_talker = None
                self.last_listener.append(addr)
                upd_iec = True, addr, None, None
                py_peers = True
            elif taddr is not None:
                addr = taddr
                texts = _get_address_texts(b)
                ann_cls = ANN_TADDR
                py_type, py_addr = 'TALK', addr
                if addr in self.last_listener:
                    self.last_listener.remove(addr)
                self.last_talker = addr
                upd_iec = True, addr, None, None
                py_peers = True
            elif saddr is not None:
                addr = saddr
                texts = _get_address_texts(b)
                ann_cls = ANN_SADDR
                upd_iec = True, None, b, None
                py_type, py_addr = 'SECONDARY', addr
            elif msb is not None:
                # These are not really "secondary addresses", but they
                # are used by the Commodore IEC bus (floppy channels).
                texts = _get_address_texts(b)
                ann_cls = ANN_SADDR
                upd_iec = True, None, b, None
                py_type, py_addr = 'MSB_SET', b
            if ann_cls is not None and texts is not None:
                self.emit_data_ann(self.ss_raw, self.es_raw, ann_cls, texts)
            if upd_iec[0]:
                self.handle_iec_periph(self.ss_raw, self.es_raw, upd_iec[1], upd_iec[2], upd_iec[3])
            if py_type:
                self.putpy(self.ss_raw, self.es_raw, py_type, py_addr, b)
            if py_peers:
                self.last_listener.sort()
                self.putpy(self.ss_raw, self.es_raw, 'TALK_LISTEN', self.last_talker, self.last_listener)
        else:
            self.accu_bytes.append(b)
            text = _get_data_text(b)
            if not self.accu_text:
                self.ss_text = self.ss_raw
            self.accu_text.append(text)
            self.es_text = self.es_raw
            self.emit_data_ann(self.ss_raw, self.es_raw, ANN_DATA, [text])
            self.handle_iec_periph(self.ss_raw, self.es_raw, None, None, b)
            self.putpy(self.ss_raw, self.es_raw, 'DATA_BYTE', self.last_talker, b)

    def handle_dav_change(self, dav, data):
        if dav:
            # Data availability starts when the flag goes active.
            self.ss_raw = self.samplenum
            self.curr_raw = bitpack(data)
            self.latch_atn = self.curr_atn
            self.latch_eoi = self.curr_eoi
            return
        # Data availability ends when the flag goes inactive. Handle the
        # previously captured data byte according to associated flags.
        self.es_raw = self.samplenum
        self.handle_data_byte()
        self.ss_raw = self.es_raw = None
        self.curr_raw = None

    def inject_dav_phase(self, ss, es, data):
        # Inspection of serial input has resulted in one raw byte which
        # spans a given period of time. Pretend we had seen a DAV active
        # phase, to re-use code for the parallel transmission.
        self.ss_raw = ss
        self.curr_raw = bitpack(data)
        self.latch_atn = self.curr_atn
        self.latch_eoi = self.curr_eoi
        self.es_raw = es
        self.handle_data_byte()
        self.ss_raw = self.es_raw = None
        self.curr_raw = None

    def invert_pins(self, pins):
        # All lines (including data bits!) are low active and thus need
        # to get inverted to receive their logical state (high active,
        # regular data bit values). Cope with inputs being optional.
        return [1 - p if p in (0, 1) else p for p in pins]

    def decode_serial(self, has_clk, has_data_1, has_atn, has_srq):
        if not has_clk or not has_data_1 or not has_atn:
            raise ChannelError('IEC bus needs at least ATN and serial CLK and DATA.')

        # This is a rephrased version of decoders/iec/pd.py:decode().
        # SRQ was not used there either. Magic numbers were eliminated.
        (
            STEP_WAIT_READY_TO_SEND,
            STEP_WAIT_READY_FOR_DATA,
            STEP_PREP_DATA_TEST_EOI,
            STEP_CLOCK_DATA_BITS,
        ) = range(4)
        step_wait_conds = (
            [{PIN_ATN: 'f'}, {PIN_DATA: 'l', PIN_CLK: 'h'}],
            [{PIN_ATN: 'f'}, {PIN_DATA: 'h', PIN_CLK: 'h'}, {PIN_CLK: 'l'}],
            [{PIN_ATN: 'f'}, {PIN_DATA: 'f'}, {PIN_CLK: 'l'}],
            [{PIN_ATN: 'f'}, {PIN_CLK: 'e'}],
        )
        step = STEP_WAIT_READY_TO_SEND
        bits = []

        while True:

            # Sample input pin values. Keep DATA/CLK in verbatim form to
            # re-use 'iec' decoder logic. Turn ATN to positive logic for
            # easier processing. The data bits get handled during byte
            # accumulation.
            pins = self.wait(step_wait_conds[step])
            data, clk = pins[PIN_DATA], pins[PIN_CLK]
            atn, = self.invert_pins([pins[PIN_ATN]])

            if self.matched[0]:
                # Falling edge on ATN, reset step.
                step = STEP_WAIT_READY_TO_SEND

            if step == STEP_WAIT_READY_TO_SEND:
                # Don't use self.matched[1] here since we might come from
                # a step with different conds due to the code above.
                if data == 0 and clk == 1:
                    # Rising edge on CLK while DATA is low: Ready to send.
                    step = STEP_WAIT_READY_FOR_DATA
            elif step == STEP_WAIT_READY_FOR_DATA:
                if data == 1 and clk == 1:
                    # Rising edge on DATA while CLK is high: Ready for data.
                    ss_byte = self.samplenum
                    self.handle_atn_change(atn)
                    if self.curr_eoi:
                        self.handle_eoi_change(False)
                    bits = []
                    step = STEP_PREP_DATA_TEST_EOI
                elif clk == 0:
                    # CLK low again, transfer aborted.
                    step = STEP_WAIT_READY_TO_SEND
            elif step == STEP_PREP_DATA_TEST_EOI:
                if data == 0 and clk == 1:
                    # DATA goes low while CLK is still high, EOI confirmed.
                    self.handle_eoi_change(True)
                elif clk == 0:
                    step = STEP_CLOCK_DATA_BITS
                    ss_bit = self.samplenum
            elif step == STEP_CLOCK_DATA_BITS:
                if self.matched[1]:
                    if clk == 1:
                        # Rising edge on CLK; latch DATA.
                        bits.append(data)
                    elif clk == 0:
                        # Falling edge on CLK; end of bit.
                        es_bit = self.samplenum
                        self.emit_data_ann(ss_bit, es_bit, ANN_RAW_BIT, ['{:d}'.format(bits[-1])])
                        self.putpy(ss_bit, es_bit, 'IEC_BIT', None, bits[-1])
                        ss_bit = self.samplenum
                        if len(bits) == 8:
                            es_byte = self.samplenum
                            self.inject_dav_phase(ss_byte, es_byte, bits)
                            if self.curr_eoi:
                                self.handle_eoi_change(False)
                            step = STEP_WAIT_READY_TO_SEND

    def decode_parallel(self, has_data_n, has_dav, has_atn, has_eoi, has_srq):

        if False in has_data_n or not has_dav or not has_atn:
            raise ChannelError('IEEE-488 needs at least ATN and DAV and eight DIO lines.')
        has_ifc = self.has_channel(PIN_IFC)

        # Capture data lines at the falling edge of DAV, process their
        # values at rising DAV edge (when data validity ends). Also make
        # sure to start inspection when the capture happens to start with
        # low signal levels, i.e. won't include the initial falling edge.
        # Scan for ATN/EOI edges as well (including the trick which works
        # around initial pin state).
        #
        # Use efficient edge based wait conditions for most activities,
        # though some phases may require individual inspection of each
        # sample (think parallel poll in combination with slow sampling).
        #
        # Map low-active physical transport lines to positive logic here,
        # to simplify logical inspection/decoding of communicated data,
        # and to avoid redundancy and inconsistency in later code paths.
        waitcond = []
        idx_dav = len(waitcond)
        waitcond.append({PIN_DAV: 'l'})
        idx_atn = len(waitcond)
        waitcond.append({PIN_ATN: 'l'})
        idx_eoi = None
        if has_eoi:
            idx_eoi = len(waitcond)
            waitcond.append({PIN_EOI: 'l'})
        idx_ifc = None
        if has_ifc:
            idx_ifc = len(waitcond)
            waitcond.append({PIN_IFC: 'l'})
        idx_pp_check = None
        def add_data_cond(conds):
            idx = len(conds)
            conds.append({'skip': 1})
            return idx
        def del_data_cond(conds, idx):
            conds.pop(idx)
            return None
        while True:
            pins = self.wait(waitcond)
            pins = self.invert_pins(pins)

            # BEWARE! Order of evaluation does matter. For low samplerate
            # captures, many edges fall onto the same sample number. So
            # we process active edges of flags early (before processing
            # data bits), and inactive edges late (after data got processed).
            want_pp_check = False
            if idx_ifc is not None and self.matched[idx_ifc] and pins[PIN_IFC] == 1:
                self.handle_ifc_change(pins[PIN_IFC])
            if idx_eoi is not None and self.matched[idx_eoi] and pins[PIN_EOI] == 1:
                self.handle_eoi_change(pins[PIN_EOI])
                want_pp_check = True
            if self.matched[idx_atn] and pins[PIN_ATN] == 1:
                self.handle_atn_change(pins[PIN_ATN])
                want_pp_check = True
            if want_pp_check and not idx_pp_check:
                pp = self.check_pp()
                if pp in ('enter',):
                    idx_pp_check = add_data_cond(waitcond)
            if self.matched[idx_dav]:
                self.handle_dav_change(pins[PIN_DAV], pins[PIN_DIO1:PIN_DIO8 + 1])
            if idx_pp_check:
                pp = self.check_pp(pins[PIN_DIO1:PIN_DIO8 + 1])
            want_pp_check = False
            if self.matched[idx_atn] and pins[PIN_ATN] == 0:
                self.handle_atn_change(pins[PIN_ATN])
                want_pp_check = True
            if idx_eoi is not None and self.matched[idx_eoi] and pins[PIN_EOI] == 0:
                self.handle_eoi_change(pins[PIN_EOI])
                want_pp_check = True
            if idx_pp_check is not None and want_pp_check:
                pp = self.check_pp(pins[PIN_DIO1:PIN_DIO8 + 1])
                if pp in ('leave',) and idx_pp_check is not None:
                    idx_pp_check = del_data_cond(waitcond, idx_pp_check)
            if idx_ifc is not None and self.matched[idx_ifc] and pins[PIN_IFC] == 0:
                self.handle_ifc_change(pins[PIN_IFC])

            waitcond[idx_dav][PIN_DAV] = 'e'
            waitcond[idx_atn][PIN_ATN] = 'e'
            if has_eoi:
                waitcond[idx_eoi][PIN_EOI] = 'e'
            if has_ifc:
                waitcond[idx_ifc][PIN_IFC] = 'e'

    def decode(self):
        # The decoder's boilerplate declares some of the input signals as
        # optional, but only to support both serial and parallel variants.
        # The CLK signal discriminates the two. For either variant some
        # of the "optional" signals are not really optional for proper
        # operation of the decoder. Check these conditions here.
        has_clk = self.has_channel(PIN_CLK)
        has_data_1 = self.has_channel(PIN_DIO1)
        has_data_n = [bool(self.has_channel(pin) for pin in range(PIN_DIO1, PIN_DIO8 + 1))]
        has_dav = self.has_channel(PIN_DAV)
        has_atn = self.has_channel(PIN_ATN)
        has_eoi = self.has_channel(PIN_EOI)
        has_srq = self.has_channel(PIN_SRQ)
        if has_clk:
            self.decode_serial(has_clk, has_data_1, has_atn, has_srq)
        else:
            self.decode_parallel(has_data_n, has_dav, has_atn, has_eoi, has_srq)
