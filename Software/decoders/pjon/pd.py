##
## This file is part of the libsigrokdecode project.
##
## Copyright (C) 2020 Gerhard Sittig <gerhard.sittig@gmx.net>
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

# See the https://www.pjon.org/ PJON project page and especially the
# https://www.pjon.org/PJON-protocol-specification-v3.2.php protocol
# specification, which can use different link layers.

# TODO
# - Check for the correct order of optional fields (the spec is not as
#   explicit on these details as I'd expect).
# - Check decoder's robustness, completeness, and correctness when more
#   captures become available. Currently there are only few, which only
#   cover minimal communication, and none of the protocol's flexibility.
#   The decoder was essentially written based on the available docs, and
#   then took some arbitrary choices and liberties to cope with real life
#   data from an example setup. Strictly speaking this decoder violates
#   the spec, and errs towards the usability side.

import sigrokdecode as srd
import struct

ANN_RX_INFO, ANN_HDR_CFG, ANN_PKT_LEN, ANN_META_CRC, ANN_TX_INFO, \
ANN_SVC_ID, ANN_PKT_ID, ANN_ANON_DATA, ANN_PAYLOAD, ANN_END_CRC, \
ANN_SYN_RSP, \
ANN_RELATION, \
ANN_WARN, \
    = range(13)

def calc_crc8(data):
    crc = 0
    for b in data:
        crc ^= b
        for i in range(8):
            odd = crc % 2
            crc >>= 1
            if odd:
                crc ^= 0x97
    return crc

def calc_crc32(data):
    crc = 0xffffffff
    for b in data:
        crc ^= b
        for i in range(8):
            odd = crc % 2
            crc >>= 1
            if odd:
                crc ^= 0xedb88320
    crc ^= 0xffffffff
    return crc

class Decoder(srd.Decoder):
    api_version = 3
    id = 'pjon'
    name = 'PJON'
    longname = 'PJON'
    desc = 'The PJON protocol.'
    license = 'gplv2+'
    inputs = ['pjon_link']
    outputs = []
    tags = ['Embedded/industrial']
    annotations = (
        ('rx_info', 'Receiver ID'),
        ('hdr_cfg', 'Header config'),
        ('pkt_len', 'Packet length'),
        ('meta_crc', 'Meta CRC'),
        ('tx_info', 'Sender ID'),
        ('port', 'Service ID'),
        ('pkt_id', 'Packet ID'),
        ('anon', 'Anonymous data'),
        ('payload', 'Payload'),
        ('end_crc', 'End CRC'),
        ('syn_rsp', 'Sync response'),
        ('relation', 'Relation'),
        ('warning', 'Warning'),
    )
    annotation_rows = (
        ('fields', 'Fields', (
            ANN_RX_INFO, ANN_HDR_CFG, ANN_PKT_LEN, ANN_META_CRC, ANN_TX_INFO,
            ANN_SVC_ID, ANN_ANON_DATA, ANN_PAYLOAD, ANN_END_CRC, ANN_SYN_RSP,
        )),
        ('relations', 'Relations', (ANN_RELATION,)),
        ('warnings', 'Warnings', (ANN_WARN,)),
    )

    def __init__(self):
        self.reset()

    def reset(self):
        self.reset_frame()

    def reset_frame(self):
        self.frame_ss = None
        self.frame_es = None
        self.frame_rx_id = None
        self.frame_tx_id = None
        self.frame_payload_text = None
        self.frame_bytes = None
        self.frame_has_ack = None
        self.ack_bytes = None
        self.ann_ss = None
        self.ann_es = None

    def start(self):
        self.out_ann = self.register(srd.OUTPUT_ANN)

    def putg(self, ss, es, ann, data):
        self.put(ss, es, self.out_ann, [ann, data])

    def frame_flush(self):
        if not self.frame_bytes:
            return
        if not self.frame_ss or not self.frame_es:
            return

        # Emit "communication relation" details.
        # TODO Include the service ID (port number) as well?
        text = []
        if self.frame_rx_id is not None:
            text.append("RX {}".format(self.frame_rx_id[-1]))
        if self.frame_tx_id is not None:
            text.append("TX {}".format(self.frame_tx_id[-1]))
        if self.frame_payload_text is not None:
            text.append("DATA {}".format(self.frame_payload_text))
        if self.frame_has_ack is not None:
            text.append("ACK {:02x}".format(self.frame_has_ack))
        if text:
            text = " - ".join(text)
            self.putg(self.frame_ss, self.frame_es, ANN_RELATION, [text])

    def handle_field_get_desc(self, idx = None):
        '''Lookup description of a PJON frame field.'''
        if not self.field_desc:
            return None
        if idx is None:
            idx = self.field_desc_idx
        if idx >= 0 and idx >= len(self.field_desc):
            return None
        if idx < 0 and abs(idx) > len(self.field_desc):
            return None
        desc = self.field_desc[idx]
        return desc

    def handle_field_add_desc(self, fmt, hdl, cls = None):
        '''Register description for a PJON frame field.'''
        item = {
            'format': fmt,
            'width': struct.calcsize(fmt),
            'handler': hdl,
            'anncls': cls,
        }
        self.field_desc.append(item)

    def handle_field_seed_desc(self):
        '''Seed list of PJON frame fields' descriptions.'''

        # At the start of a PJON frame, the layout of only two fields
        # is known. Subsequent fields (their presence, and width) depend
        # on the content of the header config field.

        self.field_desc = []
        self.handle_field_add_desc('<B', self.handle_field_rx_id, ANN_RX_INFO)
        self.handle_field_add_desc('<B', self.handle_field_config, ANN_HDR_CFG)

        self.field_desc_idx = 0
        self.field_desc_got = 0

        self.frame_ss = None
        self.frame_es = None
        self.frame_rx_id = None
        self.frame_is_broadcast = None
        self.frame_tx_id = None
        self.frame_payload = None
        self.frame_payload_text = None
        self.frame_has_ack = None

    def handle_field_rx_id(self, b):
        '''Process receiver ID field of a PJON frame.'''

        b = b[0]

        # Provide text presentation, caller emits frame field annotation.
        if b == 255: # "not assigned"
            id_txt = 'NA'
        elif b == 0: # "broadcast"
            id_txt = 'BC'
        else: # unicast
            id_txt = '{:d}'.format(b)
        texts = [
            'RX_ID {}'.format(id_txt),
            '{}'.format(id_txt),
        ]

        # Track RX info for communication relation emission.
        self.frame_rx_id = (b, id_txt)
        self.frame_is_broadcast = b == 0

        return texts

    def handle_field_config(self, b):
        '''Process header config field of a PJON frame.'''

        # Caller provides a list of values. We want a single scalar.
        b = b[0]

        # Get the config flags.
        self.cfg_shared = b & (1 << 0)
        self.cfg_tx_info = b & (1 << 1)
        self.cfg_sync_ack = b & (1 << 2)
        self.cfg_async_ack = b & (1 << 3)
        self.cfg_port = b & (1 << 4)
        self.cfg_crc32 = b & (1 << 5)
        self.cfg_len16 = b & (1 << 6)
        self.cfg_pkt_id = b & (1 << 7)

        # Get a textual presentation of the flags.
        text = []
        text.append('pkt_id' if self.cfg_pkt_id else '-') # packet number
        text.append('len16' if self.cfg_len16 else '-') # 16bit length not 8bit
        text.append('crc32' if self.cfg_crc32 else '-') # 32bit CRC not 8bit
        text.append('svc_id' if self.cfg_port else '-') # port aka service ID
        text.append('ack_mode' if self.cfg_async_ack else '-') # async response
        text.append('ack' if self.cfg_sync_ack else '-') # synchronous response
        text.append('tx_info' if self.cfg_tx_info else '-') # sender address
        text.append('bus_id' if self.cfg_shared else '-') # "shared" vs "local"
        text = ' '.join(text)
        bits = '{:08b}'.format(b)
        texts = [
            'CFG {:s}'.format(text),
            'CFG {}'.format(bits),
            bits
        ]

        # TODO Come up with the most appropriate phrases for this logic.
        # Are separate instruction groups with repeated conditions more
        # readable than one common block which registers fields _and_
        # updates the overhead size? Or is the latter preferrable due to
        # easier maintenance and less potential for inconsistency?

        # Get the size of variable width fields, to calculate the size
        # of the packet overhead (the part that is not the payload data).
        # This lets us derive the payload length when we later receive
        # the frame's total length.
        u8_fmt = '>B'
        u16_fmt = '>H'
        u32_fmt = '>L'
        len_fmt = u16_fmt if self.cfg_len16 else u8_fmt
        bus_fmt = '>4B'
        crc_fmt = u32_fmt if self.cfg_crc32 else u8_fmt
        self.cfg_overhead = 0
        self.cfg_overhead += struct.calcsize(u8_fmt) # receiver ID
        self.cfg_overhead += struct.calcsize(u8_fmt) # header config
        self.cfg_overhead += struct.calcsize(len_fmt) # packet length
        self.cfg_overhead += struct.calcsize(u8_fmt) # initial CRC, always CRC8
        # TODO Check for completeness and correctness.
        if self.cfg_shared:
            self.cfg_overhead += struct.calcsize(u32_fmt) # receiver bus
        if self.cfg_tx_info:
            if self.cfg_shared:
                self.cfg_overhead += struct.calcsize(u32_fmt) # sender bus
            self.cfg_overhead += struct.calcsize(u8_fmt) # sender ID
        if self.cfg_port:
            self.cfg_overhead += struct.calcsize(u16_fmt) # service ID
        if self.cfg_pkt_id:
            self.cfg_overhead += struct.calcsize(u16_fmt) # packet ID
        self.cfg_overhead += struct.calcsize(crc_fmt) # end CRC

        # Register more frame fields as we learn about their presence and
        # format. Up to this point only receiver ID and header config were
        # registered since their layout is fixed.
        #
        # Packet length and meta CRC are always present but can be of
        # variable width. Optional fields follow the meta CRC and preceed
        # the payload bytes. Notice that payload length isn't known here
        # either, though its position is known already. The packet length
        # is yet to get received. Subtracting the packet overhead from it
        # (which depends on the header configuration) will provide that
        # information.
        #
        # TODO Check for completeness and correctness.
        # TODO Optionally fold overhead size arith and field registration
        # into one block of instructions, to reduce the redundancy in the
        # condition checks, and raise awareness for incomplete sequences
        # during maintenance.
        self.handle_field_add_desc(len_fmt, self.handle_field_pkt_len, ANN_PKT_LEN)
        self.handle_field_add_desc(u8_fmt, self.handle_field_meta_crc, ANN_META_CRC)
        if self.cfg_shared:
            self.handle_field_add_desc(bus_fmt, self.handle_field_rx_bus, ANN_ANON_DATA)
        if self.cfg_tx_info:
            if self.cfg_shared:
                self.handle_field_add_desc(bus_fmt, self.handle_field_tx_bus, ANN_ANON_DATA)
            self.handle_field_add_desc(u8_fmt, self.handle_field_tx_id, ANN_ANON_DATA)
        if self.cfg_port:
            self.handle_field_add_desc(u16_fmt, ['PORT {:d}', '{:d}'], ANN_ANON_DATA)
        if self.cfg_pkt_id:
            self.handle_field_add_desc(u16_fmt, ['PKT {:04x}', '{:04x}'], ANN_ANON_DATA)
        pl_fmt = '>{:d}B'.format(0)
        self.handle_field_add_desc(pl_fmt, self.handle_field_payload, ANN_PAYLOAD)
        self.handle_field_add_desc(crc_fmt, self.handle_field_end_crc, ANN_END_CRC)

        # Emit warning annotations for invalid flag combinations.
        warn_texts = []
        wants_ack = self.cfg_sync_ack or self.cfg_async_ack
        if wants_ack and not self.cfg_tx_info:
            warn_texts.append('ACK request without TX info')
        if wants_ack and self.frame_is_broadcast:
            warn_texts.append('ACK request for broadcast')
        if self.cfg_sync_ack and self.cfg_async_ack:
            warn_texts.append('sync and async ACK request')
        if self.cfg_len16 and not self.cfg_crc32:
            warn_texts.append('extended length needs CRC32')
        if warn_texts:
            warn_texts = ', '.join(warn_texts)
            self.putg(self.ann_ss, self.ann_es, ANN_WARN, [warn_texts])

        # Have the caller emit the annotation for configuration data.
        return texts

    def handle_field_pkt_len(self, b):
        '''Process packet length field of a PJON frame.'''

        # Caller provides a list of values. We want a single scalar.
        b = b[0]

        # The wire communicates the total packet length. Some of it is
        # overhead (non-payload data), while its volume is variable in
        # size (depends on the header configuration).
        #
        # Derive the payload size from previously observed flags. Update
        # the previously registered field description (the second last
        # item in the list, before the end CRC).

        pkt_len = b
        pl_len = b - self.cfg_overhead
        warn_texts = []
        if pkt_len not in range(self.cfg_overhead, 65536):
            warn_texts.append('suspicious packet length')
        if pkt_len > 15 and not self.cfg_crc32:
            warn_texts.append('length above 15 needs CRC32')
        if pl_len < 1:
            warn_texts.append('suspicious payload length')
            pl_len = 0
        if warn_texts:
            warn_texts = ', '.join(warn_texts)
            self.putg(self.ann_ss, self.ann_es, ANN_WARN, [warn_texts])
        pl_fmt = '>{:d}B'.format(pl_len)

        desc = self.handle_field_get_desc(-2)
        desc['format'] = pl_fmt
        desc['width'] = struct.calcsize(pl_fmt)

        # Have the caller emit the annotation for the packet length.
        # Provide information of different detail level for zooming.
        texts = [
            'LENGTH {:d} (PAYLOAD {:d})'.format(pkt_len, pl_len),
            'LEN {:d} (PL {:d})'.format(pkt_len, pl_len),
            '{:d} ({:d})'.format(pkt_len, pl_len),
            '{:d}'.format(pkt_len),
        ]
        return texts

    def handle_field_common_crc(self, have, is_meta):
        '''Process a CRC field of a PJON frame.'''

        # CRC algorithm and width are configurable, and can differ
        # across meta and end checksums in a frame's fields.
        caption = 'META' if is_meta else 'END'
        crc_len = 8 if is_meta else 32 if self.cfg_crc32 else 8
        crc_bytes = crc_len // 8
        crc_fmt = '{:08x}' if crc_len == 32 else '{:02x}'
        have_text = crc_fmt.format(have)

        # Check received against expected checksum. Emit warnings.
        warn_texts = []
        data = self.frame_bytes[:-crc_bytes]
        want = calc_crc32(data) if crc_len == 32 else calc_crc8(data)
        if want != have:
            want_text = crc_fmt.format(want)
            warn_texts.append('CRC mismatch - want {} have {}'.format(want_text, have_text))
        if warn_texts:
            warn_texts = ', '.join(warn_texts)
            self.putg(self.ann_ss, self.ann_es, ANN_WARN, [warn_texts])

        # Provide text representation for frame field, caller emits
        # the annotation.
        texts = [
            '{}_CRC {}'.format(caption, have_text),
            'CRC {}'.format(have_text),
            have_text,
        ]
        return texts

    def handle_field_meta_crc(self, b):
        '''Process initial CRC (meta) field of a PJON frame.'''
        # Caller provides a list of values. We want a single scalar.
        b = b[0]
        return self.handle_field_common_crc(b, True)

    def handle_field_end_crc(self, b):
        '''Process end CRC (total frame) field of a PJON frame.'''
        # Caller provides a list of values. We want a single scalar.
        b = b[0]
        return self.handle_field_common_crc(b, False)

    def handle_field_common_bus(self, b):
        '''Common handling of bus ID details. Used for RX and TX.'''
        bus_id = b[:4]
        bus_num = struct.unpack('>L', bytearray(bus_id))
        bus_txt = '.'.join(['{:d}'.format(b) for b in bus_id])
        return bus_num, bus_txt

    def handle_field_rx_bus(self, b):
        '''Process receiver bus ID field of a PJON frame.'''

        # When we get here, there always should be an RX ID already.
        bus_num, bus_txt = self.handle_field_common_bus(b[:4])
        rx_txt = "{} {}".format(bus_txt, self.frame_rx_id[-1])
        self.frame_rx_id = (bus_num, self.frame_rx_id[0], rx_txt)

        # Provide text representation for frame field, caller emits
        # the annotation.
        texts = [
            'RX_BUS {}'.format(bus_txt),
            bus_txt,
        ]
        return texts

    def handle_field_tx_bus(self, b):
        '''Process transmitter bus ID field of a PJON frame.'''

        # The TX ID field is optional, as is the use of bus ID fields.
        # In the TX info case the TX bus ID is seen before the TX ID.
        bus_num, bus_txt = self.handle_field_common_bus(b[:4])
        self.frame_tx_id = (bus_num, None, bus_txt)

        # Provide text representation for frame field, caller emits
        # the annotation.
        texts = [
            'TX_BUS {}'.format(bus_txt),
            bus_txt,
        ]
        return texts

    def handle_field_tx_id(self, b):
        '''Process transmitter ID field of a PJON frame.'''

        b = b[0]

        id_txt = "{:d}".format(b)
        if self.frame_tx_id is None:
            self.frame_tx_id = (b, id_txt)
        else:
            tx_txt = "{} {}".format(self.frame_tx_id[-1], id_txt)
            self.frame_tx_id = (self.frame_tx_id[0], b, tx_txt)

        # Provide text representation for frame field, caller emits
        # the annotation.
        texts = [
            'TX_ID {}'.format(id_txt),
            id_txt,
        ]
        return texts

    def handle_field_payload(self, b):
        '''Process payload data field of a PJON frame.'''

        text = ' '.join(['{:02x}'.format(v) for v in b])
        self.frame_payload = b[:]
        self.frame_payload_text = text

        texts = [
            'PAYLOAD {}'.format(text),
            text,
        ]
        return texts

    def handle_field_sync_resp(self, b):
        '''Process synchronous response for a PJON frame.'''

        self.frame_has_ack = b

        texts = [
            'ACK {:02x}'.format(b),
            '{:02x}'.format(b),
        ]
        return texts

    def decode(self, ss, es, data):
        ptype, pdata = data

        # Start frame bytes accumulation when FRAME_INIT is seen. Flush
        # previously accumulated frame bytes when a new frame starts.
        if ptype == 'FRAME_INIT':
            self.frame_flush()
            self.reset_frame()
            self.frame_bytes = []
            self.handle_field_seed_desc()
            self.frame_ss = ss
            self.frame_es = es
            return

        # Use IDLE as another (earlier) trigger to flush frames. Also
        # trigger flushes on FRAME-DATA which mean that the link layer
        # inspection has seen the end of a protocol frame.
        #
        # TODO Improve usability? Emit warnings for PJON frames where
        # FRAME_DATA was seen but FRAME_INIT wasn't? So that users can
        # become aware of broken frames.
        if ptype in ('IDLE', 'FRAME_DATA'):
            self.frame_flush()
            self.reset_frame()
            return

        # Switch from data bytes to response bytes when WAIT is seen.
        if ptype == 'SYNC_RESP_WAIT':
            self.ack_bytes = []
            self.ann_ss, self.ann_es = None, None
            return

        # Accumulate data bytes as they arrive. Put them in the bucket
        # which corresponds to its most recently seen leader.
        if ptype == 'DATA_BYTE':
            b = pdata
            self.frame_es = es

            # Are we collecting response bytes (ACK)?
            if self.ack_bytes is not None:
                if not self.ann_ss:
                    self.ann_ss = ss
                self.ack_bytes.append(b)
                self.ann_es = es
                text = self.handle_field_sync_resp(b)
                if text:
                    self.putg(self.ann_ss, self.ann_es, ANN_SYN_RSP, text)
                self.ann_ss, self.ann_es = None, None
                return

            # Are we collecting frame content?
            if self.frame_bytes is not None:
                if not self.ann_ss:
                    self.ann_ss = ss
                self.frame_bytes.append(b)
                self.ann_es = es

                # Has the field value become available yet?
                desc = self.handle_field_get_desc()
                if not desc:
                    return
                width = desc.get('width', None)
                if not width:
                    return
                self.field_desc_got += 1
                if self.field_desc_got != width:
                    return

                # Grab most recent received field as a byte array. Get
                # the values that it contains.
                fmt = desc.get('format', '>B')
                raw = bytearray(self.frame_bytes[-width:])
                values = struct.unpack(fmt, raw)

                # Process the value, and get its presentation. Can be
                # mere formatting, or serious execution of logic.
                hdl = desc.get('handler', '{!r}')
                if isinstance(hdl, str):
                    text = [hdl.format(*values)]
                elif isinstance(hdl, (list, tuple)):
                    text = [f.format(*values) for f in hdl]
                elif hdl:
                    text = hdl(values)
                cls = desc.get('anncls', ANN_ANON_DATA)

                # Emit annotation unless the handler routine already did.
                if cls is not None and text:
                    self.putg(self.ann_ss, self.ann_es, cls, text)
                self.ann_ss, self.ann_es = None, None

                # Advance scan position for to-get-received field.
                self.field_desc_idx += 1
                self.field_desc_got = 0
                return

            # Unknown phase, not collecting. Not synced yet to the input?
            return

        # Unknown or unhandled kind of link layer output.
        return
