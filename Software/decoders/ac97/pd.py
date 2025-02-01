##
## This file is part of the libsigrokdecode project.
##
## Copyright (C) 2017 Gerhard Sittig <gerhard.sittig@gmx.net>
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

# This implementation is incomplete. TODO items:
# - Support the optional RESET# pin, detect cold and warm reset.
# - Split slot values into audio samples of their respective width and
#   frequency (either on user provided parameters, or from inspection of
#   decoded register access).

import sigrokdecode as srd
from common.srdhelper import SrdIntEnum

class ChannelError(Exception):
    pass

Pin = SrdIntEnum.from_str('Pin', 'SYNC BIT_CLK SDATA_OUT SDATA_IN RESET')

slots = 'TAG ADDR DATA 03 04 05 06 07 08 09 10 11 IO'.split()
a = 'BITS_OUT BITS_IN SLOT_RAW_OUT SLOT_RAW_IN WARN ERROR'.split() + \
    ['SLOT_OUT_' + s for s in slots] + ['SLOT_IN_' + s for s in slots]
Ann = SrdIntEnum.from_list('Ann', a)

Bin = SrdIntEnum.from_str('Bin', 'FRAME_OUT FRAME_IN SLOT_RAW_OUT SLOT_RAW_IN')

class Decoder(srd.Decoder):
    api_version = 3
    id = 'ac97'
    name = "AC '97"
    longname = "Audio Codec '97"
    desc = 'Audio and modem control for PC systems.'
    license = 'gplv2+'
    inputs = ['logic']
    outputs = []
    tags = ['Audio', 'PC']
    channels = (
        {'id': 'sync', 'name': 'SYNC', 'desc': 'Frame synchronization'},
        {'id': 'clk', 'name': 'BIT_CLK', 'desc': 'Data bits clock'},
    )
    optional_channels = (
        {'id': 'out', 'name': 'SDATA_OUT', 'desc': 'Data output'},
        {'id': 'in', 'name': 'SDATA_IN', 'desc': 'Data input'},
        {'id': 'rst', 'name': 'RESET#', 'desc': 'Reset line'},
    )
    annotations = (
        ('bit-out', 'Output bit'),
        ('bit-in', 'Input bit'),
        ('slot-out-raw', 'Output raw value'),
        ('slot-in-raw', 'Input raw value'),
        ('warning', 'Warning'),
        ('error', 'Error'),
        ('slot-out-tag', 'Output TAG'),
        ('slot-out-cmd-addr', 'Output command address'),
        ('slot-out-cmd-data', 'Output command data'),
        ('slot-out-03', 'Output slot 3'),
        ('slot-out-04', 'Output slot 4'),
        ('slot-out-05', 'Output slot 5'),
        ('slot-out-06', 'Output slot 6'),
        ('slot-out-07', 'Output slot 7'),
        ('slot-out-08', 'Output slot 8'),
        ('slot-out-09', 'Output slot 9'),
        ('slot-out-10', 'Output slot 10'),
        ('slot-out-11', 'Output slot 11'),
        ('slot-out-io-ctrl', 'Output I/O control'),
        ('slot-in-tag', 'Input TAG'),
        ('slot-in-sts-addr', 'Input status address'),
        ('slot-in-sts-data', 'Input status data'),
        ('slot-in-03', 'Input slot 3'),
        ('slot-in-04', 'Input slot 4'),
        ('slot-in-05', 'Input slot 5'),
        ('slot-in-06', 'Input slot 6'),
        ('slot-in-07', 'Input slot 7'),
        ('slot-in-08', 'Input slot 8'),
        ('slot-in-09', 'Input slot 9'),
        ('slot-in-10', 'Input slot 10'),
        ('slot-in-11', 'Input slot 11'),
        ('slot-in-io-sts', 'Input I/O status'),
        # TODO: Add more annotation classes:
        # TAG: 'ready', 'valid', 'id', 'rsv'
        # CMD ADDR: 'r/w', 'addr', 'unused'
        # CMD DATA: 'data', 'unused'
        # 3-11: 'data', 'unused', 'double data'
    )
    annotation_rows = (
        ('bits-out', 'Output bits', (Ann.BITS_OUT,)),
        ('slots-out-raw', 'Output numbers', (Ann.SLOT_RAW_OUT,)),
        ('slots-out', 'Output slots', Ann.prefixes('SLOT_OUT_')),
        ('bits-in', 'Input bits', (Ann.BITS_IN,)),
        ('slots-in-raw', 'Input numbers', (Ann.SLOT_RAW_IN,)),
        ('slots-in', 'Input slots', Ann.prefixes('SLOT_IN_')),
        ('warnings', 'Warnings', (Ann.WARN,)),
        ('errors', 'Errors', (Ann.ERROR,)),
    )
    binary = (
        ('frame-out', 'Frame bits, output data'),
        ('frame-in', 'Frame bits, input data'),
        ('slot-raw-out', 'Raw slot bits, output data'),
        ('slot-raw-in', 'Raw slot bits, input data'),
        # TODO: Which (other) binary classes to implement?
        # - Are binary annotations per audio slot useful?
        # - Assume 20bit per slot, in 24bit units? Or assume 16bit
        #   audio samples? Observe register access and derive width
        #   of the audio data? Dump channels 3-11 or 1-12?
    )

    def putx(self, ss, es, cls, data):
        self.put(ss, es, self.out_ann, [cls, data])

    def putf(self, frombit, bitcount, cls, data):
        ss = self.frame_ss_list[frombit]
        es = self.frame_ss_list[frombit + bitcount]
        self.putx(ss, es, cls, data)

    def putb(self, frombit, bitcount, cls, data):
        ss = self.frame_ss_list[frombit]
        es = self.frame_ss_list[frombit + bitcount]
        self.put(ss, es, self.out_binary, [cls, data])

    def __init__(self):
        self.reset()

    def reset(self):
        self.frame_ss_list = None
        self.frame_slot_lens = [0, 16] + [16 + 20 * i for i in range(1, 13)]
        self.frame_total_bits = self.frame_slot_lens[-1]
        self.handle_slots = {
            0: self.handle_slot_00,
            1: self.handle_slot_01,
            2: self.handle_slot_02,
        }

    def start(self):
        self.out_binary = self.register(srd.OUTPUT_BINARY)
        self.out_ann = self.register(srd.OUTPUT_ANN)

    def metadata(self, key, value):
        if key == srd.SRD_CONF_SAMPLERATE:
            self.samplerate = value

    def bits_to_int(self, bits):
        # Convert MSB-first bit sequence to integer value.
        if not bits:
            return 0
        count = len(bits)
        value = sum([2 ** (count - 1 - i) for i in range(count) if bits[i]])
        return value

    def bits_to_bin_ann(self, bits):
        # Convert MSB-first bit sequence to binary annotation data.
        # It's assumed that the number of bits does not (in useful ways)
        # fit into an integer, and we need to create an array of bytes
        # from the data afterwards, anyway. Hence the separate routine
        # and the conversion of eight bits each.
        out = []
        count = len(bits)
        while count > 0:
            count -= 8
            by, bits = bits[:8], bits[8:]
            by = self.bits_to_int(by)
            out.append(by)
        out = bytes(out)
        return out

    def int_to_nibble_text(self, value, bitcount):
        # Convert number to hex digits for given bit count.
        digits = (bitcount + 3) // 4
        text = '{{:0{:d}x}}'.format(digits).format(value)
        return text

    def get_bit_field(self, data, size, off, count):
        shift = size - off - count
        data >>= shift
        mask = (1 << count) - 1
        data &= mask
        return data

    def flush_frame_bits(self):
        # Flush raw frame bits to binary annotation.
        data = self.frame_bits_out[:]
        count = len(data)
        data = self.bits_to_bin_ann(data)
        self.putb(0, count, Bin.FRAME_OUT, data)

        data = self.frame_bits_in[:]
        count = len(data)
        data = self.bits_to_bin_ann(data)
        self.putb(0, count, Bin.FRAME_IN, data)

    def start_frame(self, ss):
        # Mark the start of a frame.
        if self.frame_ss_list:
            # Flush bits if we had a frame before the frame which is
            # starting here.
            self.flush_frame_bits()
        self.frame_ss_list = [ss]
        self.frame_bits_out = []
        self.frame_bits_in = []
        self.frame_slot_data_out = []
        self.frame_slot_data_in = []
        self.have_slots = {True: None, False: None}

    def handle_slot_dummy(self, slotidx, bitidx, bitcount, is_out, data):
        # Handle slot x, default/fallback handler.
        # Only process data of slots 1-12 when slot 0 says "valid".
        if not self.have_slots[is_out]:
            return
        if not self.have_slots[is_out][slotidx]:
            return

        # Emit a naive annotation with just the data bits that we saw
        # for the slot (hex nibbles for density). For audio data this
        # can be good enough. Slots with special meaning should not end
        # up calling the dummy handler.
        text = self.int_to_nibble_text(data, bitcount)
        anncls = Ann.SLOT_OUT_TAG if is_out else Ann.SLOT_IN_TAG
        self.putf(bitidx, bitcount, anncls + slotidx, [text])

        # Emit binary output for the data that is contained in slots
        # which end up calling the default handler. This transparently
        # should translate to "the slots with audio data", as other
        # slots which contain management data should have their specific
        # handler routines. In the present form, this approach might be
        # good enough to get a (header-less) audio stream for typical
        # setups where only line-in or line-out are in use.
        #
        # TODO: Improve this early prototype implementation. For now the
        # decoder just exports the upper 16 bits of each audio channel
        # that happens to be valid. For an improved implementation, it
        # either takes user provided specs or more smarts like observing
        # register access (if the capture includes it).
        anncls = Bin.SLOT_RAW_OUT if is_out else Bin.SLOT_RAW_IN
        data_bin = data >> 4
        data_bin &= 0xffff
        data_bin = data_bin.to_bytes(2, byteorder = 'big')
        self.putb(bitidx, bitcount, anncls, data_bin)

    def handle_slot_00(self, slotidx, bitidx, bitcount, is_out, data):
        # Handle slot 0, TAG.
        slotpos = self.frame_slot_lens[slotidx]
        fieldoff = 0
        anncls = Ann.SLOT_OUT_TAG if is_out else Ann.SLOT_IN_TAG

        fieldlen = 1
        ready = self.get_bit_field(data, bitcount, fieldoff, fieldlen)
        text = ['READY: 1', 'READY', 'RDY', 'R'] if ready else ['ready: 0', 'rdy', '-']
        self.putf(slotpos + fieldoff, fieldlen, anncls, text)
        fieldoff += fieldlen

        fieldlen = 12
        valid = self.get_bit_field(data, bitcount, fieldoff, fieldlen)
        text = ['VALID: {:3x}'.format(valid), '{:3x}'.format(valid)]
        self.putf(slotpos + fieldoff, fieldlen, anncls, text)
        have_slots = [True] + [False] * 12
        for idx in range(12):
            have_slots[idx + 1] = bool(valid & (1 << (11 - idx)))
        self.have_slots[is_out] = have_slots
        fieldoff += fieldlen

        fieldlen = 1
        rsv = self.get_bit_field(data, bitcount, fieldoff, fieldlen)
        if rsv != 0:
            text = ['reserved bit error', 'rsv error', 'rsv']
            self.putf(slotpos + fieldoff, fieldlen, Ann.ERROR, text)
        fieldoff += fieldlen

        # TODO: Will input slot 0 have a Codec ID, or 3 reserved bits?
        fieldlen = 2
        codec = self.get_bit_field(data, bitcount, fieldoff, fieldlen)
        text = ['CODEC: {:1x}'.format(codec), '{:1x}'.format(codec)]
        self.putf(slotpos + fieldoff, fieldlen, anncls, text)
        fieldoff += fieldlen

    def handle_slot_01(self, slotidx, bitidx, bitcount, is_out, data):
        # Handle slot 1, command/status address.
        slotpos = self.frame_slot_lens[slotidx]
        if not self.have_slots[is_out]:
            return
        if not self.have_slots[is_out][slotidx]:
            return
        fieldoff = 0
        anncls = Ann.SLOT_OUT_TAG if is_out else Ann.SLOT_IN_TAG
        anncls += slotidx

        fieldlen = 1
        if is_out:
            is_read = self.get_bit_field(data, bitcount, fieldoff, fieldlen)
            text = ['READ', 'RD', 'R'] if is_read else ['WRITE', 'WR', 'W']
            self.putf(slotpos + fieldoff, fieldlen, anncls, text)
            # TODO: Check for the "atomic" constraint? Some operations
            # involve address _and_ data, which cannot be spread across
            # several frames. Slot 0 and 1 _must_ be provided within the
            # same frame (the test should occur in the handler for slot
            # 2 of course, in slot 1 we don't know what will follow).
        else:
            rsv = self.get_bit_field(data, bitcount, fieldoff, fieldlen)
            if rsv != 0:
                text = ['reserved bit error', 'rsv error', 'rsv']
                self.putf(slotpos + fieldoff, fieldlen, Ann.ERROR, text)
        fieldoff += fieldlen

        fieldlen = 7
        regaddr = self.get_bit_field(data, bitcount, fieldoff, fieldlen)
        # TODO: Present 0-63 or 0-126 as the address of the 16bit register?
        text = ['ADDR: {:2x}'.format(regaddr), '{:2x}'.format(regaddr)]
        self.putf(slotpos + fieldoff, fieldlen, anncls, text)
        if regaddr & 0x01:
            text = ['odd register address', 'odd reg addr', 'odd addr', 'odd']
            self.putf(slotpos + fieldoff, fieldlen, Ann.ERROR, text)
        fieldoff += fieldlen

        # Strictly speaking there are 10 data request bits and 2 reserved
        # bits for input slots, and 12 reserved bits for output slots. We
        # test for 10 and 2 bits, to simplify the logic. Only in case of
        # non-zero reserved bits for outputs this will result in "a little
        # strange" an annotation. This is a cosmetic issue, we don't mind.
        fieldlen = 10
        reqdata = self.get_bit_field(data, bitcount, fieldoff, fieldlen)
        if is_out and reqdata != 0:
            text = ['reserved bit error', 'rsv error', 'rsv']
            self.putf(slotpos + fieldoff, fieldlen, Ann.ERROR, text)
        if not is_out:
            text = ['REQ: {:3x}'.format(reqdata), '{:3x}'.format(reqdata)]
            self.putf(slotpos + fieldoff, fieldlen, anncls, text)
        fieldoff += fieldlen

        fieldlen = 2
        rsv = self.get_bit_field(data, bitcount, fieldoff, fieldlen)
        if rsv != 0:
            text = ['reserved bit error', 'rsv error', 'rsv']
            self.putf(slotpos + fieldoff, fieldlen, Ann.ERROR, text)
        fieldoff += fieldlen

    def handle_slot_02(self, slotidx, bitidx, bitcount, is_out, data):
        # Handle slot 2, command/status data.
        slotpos = self.frame_slot_lens[slotidx]
        if not self.have_slots[is_out]:
            return
        if not self.have_slots[is_out][slotidx]:
            return
        fieldoff = 0
        anncls = Ann.SLOT_OUT_TAG if is_out else Ann.SLOT_IN_TAG
        anncls += slotidx

        fieldlen = 16
        rwdata = self.get_bit_field(data, bitcount, fieldoff, fieldlen)
        # TODO: Check for zero output data when the operation is a read.
        # TODO: Check for the "atomic" constraint.
        text = ['DATA: {:4x}'.format(rwdata), '{:4x}'.format(rwdata)]
        self.putf(slotpos + fieldoff, fieldlen, anncls, text)
        fieldoff += fieldlen

        fieldlen = 4
        rsv = self.get_bit_field(data, bitcount, fieldoff, fieldlen)
        if rsv != 0:
            text = ['reserved bits error', 'rsv error', 'rsv']
            self.putf(slotpos + fieldoff, fieldlen, Ann.ERROR, text)
        fieldoff += fieldlen

    # TODO: Implement other slots.
    # - 1: cmd/status addr (check status vs command)
    # - 2: cmd/status data (check status vs command)
    # - 3-11: audio out/in
    # - 12: io control/status (modem GPIO(?))

    def handle_slot(self, slotidx, data_out, data_in):
        # Process a received slot of a frame.
        func = self.handle_slots.get(slotidx, self.handle_slot_dummy)
        bitidx = self.frame_slot_lens[slotidx]
        bitcount = self.frame_slot_lens[slotidx + 1] - bitidx
        if data_out is not None:
            func(slotidx, bitidx, bitcount, True, data_out)
        if data_in is not None:
            func(slotidx, bitidx, bitcount, False, data_in)

    def handle_bits(self, ss, es, bit_out, bit_in):
        # Process a received pair of bits.
        # Emit the bits' annotations. Only interpret the data when we
        # are in a frame (have seen the start of the frame, and don't
        # exceed the expected number of bits in a frame).
        if bit_out is not None:
            self.putx(ss, es, Ann.BITS_OUT, ['{:d}'.format(bit_out)])
        if bit_in is not None:
            self.putx(ss, es, Ann.BITS_IN, ['{:d}'.format(bit_in)])
        if self.frame_ss_list is None:
            return
        self.frame_ss_list.append(es)
        have_len = len(self.frame_ss_list) - 1
        if have_len > self.frame_total_bits:
            return

        # Accumulate the bits within the frame, until one slot of the
        # frame has become available.
        slot_idx = 0
        if bit_out is not None:
            self.frame_bits_out.append(bit_out)
            slot_idx = len(self.frame_slot_data_out)
        if bit_in is not None:
            self.frame_bits_in.append(bit_in)
            slot_idx = len(self.frame_slot_data_in)
        want_len = self.frame_slot_lens[slot_idx + 1]
        if have_len != want_len:
            return
        prev_len = self.frame_slot_lens[slot_idx]

        # Convert bits to integer values. This shall simplify extraction
        # of bit fields in multiple other locations.
        slot_data_out = None
        if bit_out is not None:
            slot_bits = self.frame_bits_out[prev_len:]
            slot_data = self.bits_to_int(slot_bits)
            self.frame_slot_data_out.append(slot_data)
            slot_data_out = slot_data
        slot_data_in = None
        if bit_in is not None:
            slot_bits = self.frame_bits_in[prev_len:]
            slot_data = self.bits_to_int(slot_bits)
            self.frame_slot_data_in.append(slot_data)
            slot_data_in = slot_data

        # Emit simple annotations for the integer values, until upper
        # layer decode stages will be implemented.
        slot_len = have_len - prev_len
        slot_ss = self.frame_ss_list[prev_len]
        slot_es = self.frame_ss_list[have_len]
        if slot_data_out is not None:
            slot_text = self.int_to_nibble_text(slot_data_out, slot_len)
            self.putx(slot_ss, slot_es, Ann.SLOT_RAW_OUT, [slot_text])
        if slot_data_in is not None:
            slot_text = self.int_to_nibble_text(slot_data_in, slot_len)
            self.putx(slot_ss, slot_es, Ann.SLOT_RAW_IN, [slot_text])

        self.handle_slot(slot_idx, slot_data_out, slot_data_in)

    def decode(self):
        have_sdo = self.has_channel(Pin.SDATA_OUT)
        have_sdi = self.has_channel(Pin.SDATA_IN)
        if not have_sdo and not have_sdi:
            raise ChannelError('Either SDATA_OUT or SDATA_IN (or both) are required.')
        have_reset = self.has_channel(Pin.RESET)

        # Data is sampled at falling CLK edges. Annotations need to span
        # the period between rising edges. SYNC rises one cycle _before_
        # the start of a frame. Grab the earliest SYNC sample we can get
        # and advance to the start of a bit time. Then keep getting the
        # samples and the end of all subsequent bit times.
        prev_sync = [None, None, None]
        pins = self.wait({Pin.BIT_CLK: 'e'})
        if pins[Pin.BIT_CLK] == 0:
            prev_sync[-1] = pins[Pin.SYNC]
            pins = self.wait({Pin.BIT_CLK: 'r'})
        bit_ss = self.samplenum
        while True:
            pins = self.wait({Pin.BIT_CLK: 'f'})
            prev_sync.pop(0)
            prev_sync.append(pins[Pin.SYNC])
            self.wait({Pin.BIT_CLK: 'r'})
            if prev_sync[0] == 0 and prev_sync[1] == 1:
                self.start_frame(bit_ss)
            self.handle_bits(bit_ss, self.samplenum,
                    pins[Pin.SDATA_OUT] if have_sdo else None,
                    pins[Pin.SDATA_IN] if have_sdi else None)
            bit_ss = self.samplenum
