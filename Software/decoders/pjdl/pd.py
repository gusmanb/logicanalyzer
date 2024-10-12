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
# https://www.pjon.org/PJDL-specification-v4.1.php PJDL v4.1 spec for
# the "Padded Jittering Data Link" single wire serial data link layer.

# TODO
# - Improve (fix, and extend) carrier sense support. Detection of the
#   idle/busy connection state is incomplete and fragile. Getting 'IDLE'
#   operational in the PJDL decoder would greatly help the PJON decoder
#   to flush ACK details before the start of new frames.
# - Check the correctness of timing assumptions. This implementation has
#   support for tolerances, which the spec does not discuss. Though real
#   world traffic was found to not decode at all with strict spec values
#   and without tolerances, while communication peers were able to talk
#   to each other. This needs more attention.
# - Check robustness when input data contains glitches. The spec does
#   not discuss how to handle these. Data bit sampling happens to work
#   because their value is taken at the center of the bit time. But
#   pad bits suffer badly from glitches, which breaks frame inspection
#   as well.
# - Cleanup the decoder implementation in general terms. Some details
#   have become obsolete ("edges", "pads"), and/or are covered by other
#   code paths.
# - Implement more data link decoders which can feed their output into
#   the PJON protocol decoder. Candidates are: PJDLR, PJDLS, TSDL.
# - Determine whether or not the data link layer should interpret any
#   frame content. From my perspective it should not, and needs not in
#   the strict sense. Possible gains would be getting the (expected!)
#   packet length, or whether a synchronous response is requested. But
#   this would duplicate knowledge which should remain internal to the
#   PJON decoder. And this link layer decoder neither shall assume that
#   the input data would be correct, or complete. Instead the decoder
#   shall remain usable on captures which demonstrate faults, and be
#   helpful in pointing them out. The design goal is to extract the
#   maximum of information possible, and pass it on as transparently
#   as possible.

import sigrokdecode as srd
from common.srdhelper import bitpack
from math import ceil, floor

'''
OUTPUT_PYTHON format for stacked decoders:

General packet format:
[<ptype>, <pdata>]

This is the list of <ptype>s and their respective <pdata> values:

Carrier sense:
- 'IDLE': <pdata> is the pin level (always 0).
- 'BUSY': <pdata> is always True.

Raw bit slots:
- 'PAD_BIT': <pdata> is the pin level (always 1).
- 'DATA_BIT': <pdata> is the pin level (0, or 1).
- 'SHORT_BIT': <pdata> is the pin level (always 1).
- 'SYNC_LOSS': <pdata> is an arbitrary text (internal use only).

Date bytes and frames:
- 'SYNC_PAD': <pdata> is True. Spans the high pad bit as well as the
  low data bit.
- 'DATA_BYTE': <pdata> is the byte value (0..255).
- 'FRAME_INIT': <pdata> is True. Spans three sync pads.
- 'FRAME_DATA': <pdata> is the sequence of bytes in the frame. Non-data
  phases in the frame get represented by strings instead of numbers
  ('INIT', 'SYNC', 'SHORT', 'WAIT'). Frames can be incomplete, depending
  on the decoder's input data.
- 'SYNC_RESP_WAIT': <pdata> is always True.

Notice that this link layer decoder is not aware of frame content. Will
neither check packet length, nor variable width fields, nor verify the
presence of requested synchronous responses. Cannot tell the sequence of
frame bytes then ACK bytes (without wait phase) from just frame bytes.
An upper layer protocol decoder will interpret content, the link layer
decoder remains as transparent as possible, and will neither assume
correct nor complete input data.
'''

# Carrier sense, and synchronization loss implementation is currently
# incomplete, and results in too many too short annotations, some of
# them spurious and confusing. TODO Improve the implementation.
_with_ann_carrier = False
_with_ann_sync_loss = False

PIN_DATA, = range(1)
ANN_CARRIER_BUSY, ANN_CARRIER_IDLE, \
ANN_PAD_BIT, ANN_LOW_BIT, ANN_DATA_BIT, ANN_SHORT_DATA, ANN_SYNC_LOSS, \
ANN_DATA_BYTE, \
ANN_FRAME_INIT, ANN_FRAME_BYTES, ANN_FRAME_WAIT, \
    = range(11)

class SamplerateError(Exception):
    pass

class Decoder(srd.Decoder):
    api_version = 3
    id = 'pjdl'
    name = 'PJDL'
    longname = 'Padded Jittering Data Link'
    desc = 'PJDL, a single wire serial link layer for PJON.'
    license = 'gplv2+'
    inputs = ['logic']
    outputs = ['pjon_link']
    tags = ['Embedded/industrial']
    channels = (
        {'id': 'data' , 'name': 'DATA', 'desc': 'Single wire data'},
    )
    options = (
        {'id': 'mode', 'desc': 'Communication mode',
            'default': 1, 'values': (1, 2, 3, 4)},
        {'id': 'idle_add_us', 'desc': 'Added idle time (us)', 'default': 4},
    )
    annotations = (
        ('cs_busy', 'Carrier busy'),
        ('cs_idle', 'Carrier idle'),
        ('bit_pad', 'Pad bit'),
        ('bit_low', 'Low bit'),
        ('bit_data', 'Data bit'),
        ('bit_short', 'Short data'),
        ('sync_loss', 'Sync loss'),
        ('byte', 'Data byte'),
        ('frame_init', 'Frame init'),
        ('frame_bytes', 'Frame bytes'),
        ('frame_wait', 'Frame wait'),
    )
    annotation_rows = (
        ('carriers', 'Carriers', (ANN_CARRIER_BUSY, ANN_CARRIER_IDLE,)),
        ('bits', 'Bits', (ANN_PAD_BIT, ANN_LOW_BIT, ANN_DATA_BIT, ANN_SHORT_DATA,)),
        ('bytes', 'Bytes', (ANN_FRAME_INIT, ANN_DATA_BYTE, ANN_FRAME_WAIT,)),
        ('frames', 'Frames', (ANN_FRAME_BYTES,)),
        ('warns', 'Warnings', (ANN_SYNC_LOSS,)),
    )

    # Communication modes' data bit and pad bit duration (in us), and
    # tolerances in percent and absolute (us).
    mode_times = {
        1: (44, 116),
        2: (40, 92),
        3: (28, 88),
        4: (26, 60),
    }
    time_tol_perc = 10
    time_tol_abs = 1.5

    def __init__(self):
        self.reset()

    def reset(self):
        self.reset_state()

    def reset_state(self):
        self.carrier_want_idle = True
        self.carrier_is_busy = False
        self.carrier_is_idle = False
        self.carrier_idle_ss = None
        self.carrier_busy_ss = None
        self.syncpad_fall_ss = None

        self.edges = None
        self.symbols = None
        self.sync_pads = None
        self.data_bits = None
        self.frame_bytes = None
        self.short_bits = None

    def start(self):
        self.out_ann = self.register(srd.OUTPUT_ANN)
        self.out_python = self.register(srd.OUTPUT_PYTHON)

    def metadata(self, key, value):
        if key == srd.SRD_CONF_SAMPLERATE:
            self.samplerate = value
            self.span_prepare()

    def putg(self, ss, es, data):
        cls = data[0]
        if not _with_ann_carrier and cls in (ANN_CARRIER_BUSY, ANN_CARRIER_IDLE):
            return
        if not _with_ann_sync_loss and cls in (ANN_SYNC_LOSS,):
            return
        self.put(ss, es, self.out_ann, data)

    def putpy(self, ss, es, ptype, pdata):
        self.put(ss, es, self.out_python, [ptype, pdata])

    def symbols_clear(self):
        syms = self.symbols or []
        self.symbols = []
        return syms

    def symbols_append(self, ss, es, symbol, data = None):
        if self.symbols is None:
            self.symbols = []
        item = (ss, es, symbol, data)
        self.symbols.append(item)

    def symbols_get_last(self, count = None):
        if not self.symbols:
            return None
        if count is None:
            count = 1
        if len(self.symbols) < count:
            return None
        items = self.symbols[-count:]
        if count == 1:
            items = items[0]
        return items

    def symbols_update_last(self, ss, es, symbol, data = None):
        if not self.symbols:
            return None
        item = list(self.symbols[-1])
        if ss is not None:
            item[0] = ss
        if es is not None:
            item[1] = es
        if symbol is not None:
            item[2] = symbol
        if data is not None:
            item[3] = data
        self.symbols[-1] = tuple(item)

    def symbols_has_prev(self, want_items):
        if not isinstance(want_items, (list, tuple,)):
            want_items = [want_items]
        if self.symbols is None:
            return False
        if len(self.symbols) < len(want_items):
            return False
        sym_off = len(self.symbols) - len(want_items)
        for idx, want_item in enumerate(want_items):
            if self.symbols[sym_off + idx][2] != want_item:
                return False
        return True

    def symbols_collapse(self, count, symbol, data = None, squeeze = None):
        if self.symbols is None:
            return None
        if len(self.symbols) < count:
            return None
        self.symbols, last_data = self.symbols[:-count], self.symbols[-count:]
        while squeeze and self.symbols and self.symbols[-1][2] == squeeze:
            last_data.insert(0, self.symbols.pop())
        ss, es = last_data[0][0], last_data[-1][1]
        if data is None:
            data = last_data
        item = (ss, es, symbol, data)
        self.symbols.append(item)

    def frame_flush(self):
        syms = self.symbols_clear()
        while syms and syms[0][2] == 'IDLE':
            syms.pop(0)
        while syms and syms[-1][2] == 'IDLE':
            syms.pop(-1)
        if not syms:
            return
        text = []
        data = []
        for sym in syms:
            if sym[2] == 'FRAME_INIT':
                text.append('INIT')
                data.append('INIT')
                continue
            if sym[2] == 'SYNC_PAD':
                if not text or text[-1] != 'SYNC':
                    text.append('SYNC')
                    data.append('SYNC')
                continue
            if sym[2] == 'DATA_BYTE':
                b = [bit[3] for bit in sym[3] if bit[2] == 'DATA_BIT']
                b = bitpack(b)
                text.append('{:02x}'.format(b))
                data.append(b)
                continue
            if sym[2] == 'SHORT_BIT':
                if not text or text[-1] != 'SHORT':
                    text.append('SHORT')
                    data.append('SHORT')
                continue
            if sym[2] == 'WAIT_ACK':
                text.append('WAIT')
                data.append('WAIT')
                continue
        text = ' '.join(text)
        ss, es = syms[0][0], syms[-1][1]
        self.putg(ss, es, [ANN_FRAME_BYTES, [text]])
        self.putpy(ss, es, 'FRAME_DATA', data)

    def carrier_flush(self):
        # Force annotations if BUSY started, or if IDLE tracking started
        # and kept running for long enough. This will be called before
        # internal state reset, so we won't manipulate internal variables,
        # and can afford to emit annotations which haven't met their
        # proper end condition yet.
        if self.carrier_busy_ss:
            ss, es = self.carrier_busy_ss, self.samplenum
            self.putg(ss, es, [ANN_CARRIER_BUSY, ['BUSY']])
        if self.carrier_idle_ss:
            ss, es = self.carrier_idle_ss, self.samplenum
            ss += int(self.idle_width)
            if ss < es:
                self.putg(ss, es, [ANN_CARRIER_IDLE, ['IDLE']])

    def carrier_set_idle(self, on, ss, es):
        if on:
            # IDLE starts here, or continues.
            if not self.carrier_idle_ss:
                self.carrier_idle_ss = int(ss)
            if not self.symbols_has_prev('IDLE'):
                self.symbols_append(ss, ss, 'IDLE')
            self.symbols_update_last(None, es, None)
            # HACK We have seen an IDLE condition. This implementation
            # loses details which are used to track IDLE, but it's more
            # important to start accumulation of a new frame here.
            self.frame_flush()
            self.reset_state()
            # end of HACK
            self.carrier_is_idle = True
            self.carrier_want_idle = False
            return
        # IDLE ends here.
        if self.symbols_has_prev('IDLE'):
            self.symbols_update_last(None, es, None)
        self.carrier_flush()
        self.carrier_is_idle = False
        self.carrier_idle_ss = None

    def carrier_set_busy(self, on, snum):
        self.carrier_is_busy = on
        if on:
            self.carrier_is_idle = None
            if not self.carrier_busy_ss:
                self.carrier_busy_ss = snum
            return
        if self.carrier_busy_ss:
            self.putg(self.carrier_busy_ss, snum, [ANN_CARRIER_BUSY, ['BUSY']])
        self.carrier_busy_ss = None
        self.carrier_is_busy = False

    def carrier_check(self, level, snum):

        # When HIGH is seen, immediately end IDLE and switch to BUSY.
        if level:
            self.carrier_set_idle(False, snum, snum)
            self.carrier_set_busy(True, snum)
            return

        # LOW is seen. Start tracking an IDLE period if not done yet.
        if not self.carrier_idle_ss:
            self.carrier_idle_ss = int(snum)

        # End BUSY when LOW persisted for an exact data byte's length.
        # Start IDLE when LOW persisted for a data byte's length plus
        # the user specified additional period.
        span = snum - self.carrier_idle_ss
        if span >= self.byte_width:
            self.carrier_set_busy(False, snum)
        if span >= self.idle_width:
            self.carrier_set_idle(True, self.carrier_idle_ss + self.idle_width, snum)

    def span_prepare(self):
        '''Prepare calculation of durations in terms of samples.'''

        # Determine samples per microsecond, and sample counts for
        # several bit types, and sample count for a data byte's
        # length, including optional extra time. Determine ranges
        # for bit widths (tolerance margin).

        # Get times in microseconds.
        mode_times = self.mode_times[self.options['mode']]
        mode_times = [t * 1.0 for t in mode_times]
        self.data_width, self.pad_width = mode_times
        self.byte_width = self.pad_width + 9 * self.data_width
        self.add_idle_width = self.options['idle_add_us']
        self.idle_width = self.byte_width + self.add_idle_width

        # Derive ranges (add tolerance) and scale to sample counts.
        self.usec_width = self.samplerate / 1e6
        self.hold_high_width = 9 * self.time_tol_abs * self.usec_width

        def _get_range(width):
            reladd = self.time_tol_perc / 100
            absadd = self.time_tol_abs
            lower = min(width * (1 - reladd), width - absadd)
            upper = max(width * (1 + reladd), width + absadd)
            lower = floor(lower * self.usec_width)
            upper = ceil(upper * self.usec_width)
            return (lower, upper + 1)

        self.data_bit_1_range = _get_range(self.data_width * 1)
        self.data_bit_2_range = _get_range(self.data_width * 2)
        self.data_bit_3_range = _get_range(self.data_width * 3)
        self.data_bit_4_range = _get_range(self.data_width * 4)
        self.short_data_range = _get_range(self.data_width / 4)
        self.pad_bit_range = _get_range(self.pad_width)

        self.data_width *= self.usec_width
        self.pad_width *= self.usec_width
        self.byte_width *= self.usec_width
        self.idle_width *= self.usec_width

        self.lookahead_width = int(4 * self.data_width)

    def span_snum_to_us(self, count):
        return count / self.usec_width

    def span_is_pad(self, span):
        return span in range(*self.pad_bit_range)

    def span_is_data(self, span):
        if span in range(*self.data_bit_1_range):
            return 1
        if span in range(*self.data_bit_2_range):
            return 2
        if span in range(*self.data_bit_3_range):
            return 3
        if span in range(*self.data_bit_4_range):
            return 4
        return False

    def span_is_short(self, span):
        return span in range(*self.short_data_range)

    def wait_until(self, want):
        '''Wait until a given location, but keep sensing carrier.'''

        # Implementor's note: Avoids skip values below 1. This version
        # "may overshoot" by one sample. Which should be acceptable for
        # this specific use case (can put the sample point of a bit time
        # out of the center by some 4% under worst case conditions).

        want = int(want)
        while True:
            diff = max(want - self.samplenum, 1)
            pins = self.wait([{PIN_DATA: 'e'}, {'skip': diff}])
            self.carrier_check(pins[PIN_DATA], self.samplenum)
            if self.samplenum >= want:
                return pins
        # UNREACH

    def decode(self):
        if not self.samplerate or self.samplerate < 1e6:
            raise SamplerateError('Need a samplerate of at least 1MSa/s')

        # As a special case the first low period in the input capture is
        # saught regardless of whether we can see its falling edge. This
        # approach is also used to recover after synchronization was lost.
        #
        # The important condition here in the main loop is: Get the next
        # edge's position, but time out after a maximum period of four
        # data bits. This allows for the detection of SYNC pulses, also
        # responds "soon enough" to DATA bits where edges can be few
        # within a data byte. Also avoids excessive waits for unexpected
        # communication errors.
        #
        # DATA bits within a byte are taken at fixed intervals relative
        # to the SYNC-PAD's falling edge. It's essential to check the
        # carrier at every edge, also during DATA bit sampling. Simple
        # skips to the desired sample point could break that feature.
        while True:

            # Help kick-start the IDLE condition detection after
            # decoder state reset.
            if not self.edges:
                curr_level, = self.wait({PIN_DATA: 'l'})
                self.carrier_check(curr_level, self.samplenum)
                self.edges = [self.samplenum]
                continue

            # Advance to the next edge, or over a medium span without an
            # edge. Prepare to classify the distance to derive bit types
            # from these details.
            last_snum = self.samplenum
            curr_level, = self.wait([{PIN_DATA: 'e'}, {'skip': self.lookahead_width}])
            self.carrier_check(curr_level, self.samplenum)
            bit_level = curr_level
            edge_seen = self.matched[0]
            if edge_seen:
                bit_level = 1 - bit_level
            if not self.edges:
                self.edges = [self.samplenum]
                continue
            self.edges.append(self.samplenum)
            curr_snum = self.samplenum

            # Check bit width (can also be multiple data bits).
            span = self.edges[-1] - self.edges[-2]
            is_pad = bit_level and self.span_is_pad(span)
            is_data = self.span_is_data(span)
            is_short = bit_level and self.span_is_short(span)

            if is_pad:
                # BEWARE! Use ss value of last edge (genuinely seen, or
                # inserted after a DATA byte) for PAD bit annotations.
                ss, es = self.edges[-2], curr_snum
                texts = ['PAD', '{:d}'.format(bit_level)]
                self.putg(ss, es, [ANN_PAD_BIT, texts])
                self.symbols_append(ss, es, 'PAD_BIT', bit_level)
                ss, es = self.symbols_get_last()[:2]
                self.putpy(ss, es, 'PAD_BIT', bit_level)
                continue

            if is_short:
                ss, es = last_snum, curr_snum
                texts = ['SHORT', '{:d}'.format(bit_level)]
                self.putg(ss, es, [ANN_SHORT_DATA, texts])
                self.symbols_append(ss, es, 'SHORT_BIT', bit_level)
                ss, es = self.symbols_get_last()[:2]
                self.putpy(ss, es, 'SHORT_BIT', bit_level)
                continue

            # Force IDLE period check when the decoder seeks to sync
            # to the input data stream.
            if not bit_level and not self.symbols and self.carrier_want_idle:
                continue

            # Accept arbitrary length LOW phases after DATA bytes(!) or
            # SHORT pulses, but not within a DATA byte or SYNC-PAD etc.
            # This covers the late start of the next SYNC-PAD (byte of
            # a frame, or ACK byte after a frame, or the start of the
            # next frame).
            if not bit_level:
                if self.symbols_has_prev('DATA_BYTE'):
                    continue
                if self.symbols_has_prev('SHORT_BIT'):
                    continue
                if self.symbols_has_prev('WAIT_ACK'):
                    continue

            # Get (consume!) the LOW DATA bit after a PAD.
            took_low = False
            if is_data and not bit_level and self.symbols_has_prev('PAD_BIT'):
                took_low = True
                is_data -= 1
                next_snum = int(last_snum + self.data_width)
                ss, es = last_snum, next_snum
                texts = ['ZERO', '{:d}'.format(bit_level)]
                self.putg(ss, es, [ANN_LOW_BIT, texts])
                self.symbols_append(ss, es, 'ZERO_BIT', bit_level)
                ss, es = self.symbols_get_last()[:2]
                self.putpy(ss, es, 'DATA_BIT', bit_level)
                self.data_fall_time = last_snum
                last_snum = next_snum
            # Turn the combination of PAD and LOW DATA into SYNC-PAD.
            # Start data bit accumulation after a SYNC-PAD was seen.
            sync_pad_seq = ['PAD_BIT', 'ZERO_BIT']
            if self.symbols_has_prev(sync_pad_seq):
                self.symbols_collapse(len(sync_pad_seq), 'SYNC_PAD')
                ss, es = self.symbols_get_last()[:2]
                self.putpy(ss, es, 'SYNC_PAD', True)
                self.data_bits = []
            # Turn three subsequent SYNC-PAD into FRAME-INIT. Start the
            # accumulation of frame bytes when FRAME-INIT was seen.
            frame_init_seq = 3 * ['SYNC_PAD']
            if self.symbols_has_prev(frame_init_seq):
                self.symbols_collapse(len(frame_init_seq), 'FRAME_INIT')
                # Force a flush of the previous frame after we have
                # reliably detected the start of another one. This is a
                # workaround for this decoder's inability to detect the
                # end of a frame after an ACK was seen or byte counts
                # have been reached. We cannot assume perfect input,
                # thus we leave all interpretation of frame content to
                # upper layers. Do keep the recently queued FRAME_INIT
                # symbol across the flush operation.
                if len(self.symbols) > 1:
                    keep = self.symbols.pop(-1)
                    self.frame_flush()
                    self.symbols.clear()
                    self.symbols.append(keep)
                ss, es = self.symbols_get_last()[:2]
                texts = ['FRAME INIT', 'INIT', 'I']
                self.putg(ss, es, [ANN_FRAME_INIT, texts])
                self.putpy(ss, es, 'FRAME_INIT', True)
                self.frame_bytes = []
            # Collapse SYNC-PAD after SHORT+ into a WAIT-ACK. Include
            # all leading SHORT bits in the WAIT as well.
            wait_ack_seq = ['SHORT_BIT', 'SYNC_PAD']
            if self.symbols_has_prev(wait_ack_seq):
                self.symbols_collapse(len(wait_ack_seq), 'WAIT_ACK',
                    squeeze = 'SHORT_BIT')
                ss, es = self.symbols_get_last()[:2]
                texts = ['WAIT for sync response', 'WAIT response', 'WAIT', 'W']
                self.putg(ss, es, [ANN_FRAME_WAIT, texts])
                self.putpy(ss, es, 'SYNC_RESP_WAIT', True)
            if took_low and not is_data:
                # Start at the very next edge if we just consumed a LOW
                # after a PAD bit, and the DATA bit count is exhausted.
                # This improves robustness, deals with inaccurate edge
                # positions. (Motivated by real world captures, the spec
                # would not discuss bit time tolerances.)
                continue

            # When we get here, the only remaining (the only supported)
            # activity is the collection of a data byte's DATA bits.
            # These are not taken by the main loop's "edge search, with
            # a timeout" approach, which is "too tolerant". Instead all
            # DATA bits get sampled at a fixed interval and relative to
            # the SYNC-PAD's falling edge. We expect to have seen the
            # data byte' SYNC-PAD before. If we haven't, the decoder is
            # not yet synchronized to the input data.
            if not is_data:
                fast_cont = edge_seen and curr_level
                ss, es = last_snum, curr_snum
                texts = ['failed pulse length check', 'pulse length', 'length']
                self.putg(ss, es, [ANN_SYNC_LOSS, texts])
                self.frame_flush()
                self.carrier_flush()
                self.reset_state()
                if fast_cont:
                    self.edges = [self.samplenum]
                continue
            if not self.symbols_has_prev('SYNC_PAD'):
                # Fast reponse to the specific combination of: no-sync,
                # edge seen, and current high level. In this case we
                # can reset internal state, but also can continue the
                # interpretation right after the most recently seen
                # rising edge, which could start the next PAD time.
                # Otherwise continue slow interpretation after reset.
                fast_cont = edge_seen and curr_level
                self.frame_flush()
                self.carrier_flush()
                self.reset_state()
                if fast_cont:
                    self.edges = [self.samplenum]
                continue

            # The main loop's "edge search with period timeout" approach
            # can have provided up to three more DATA bits after the LOW
            # bit of the SYNC-PAD. Consume them immediately in that case,
            # otherwise .wait() for their sample point. Stick with float
            # values for bit sample points and bit time boundaries for
            # improved accuracy, only round late to integers when needed.
            bit_field = []
            bit_ss = self.data_fall_time + self.data_width
            for bit_idx in range(8):
                bit_es = bit_ss + self.data_width
                bit_snum = (bit_es + bit_ss) / 2
                if bit_snum > self.samplenum:
                    bit_level, = self.wait_until(bit_snum)
                ss, es = ceil(bit_ss), floor(bit_es)
                texts = ['{:d}'.format(bit_level)]
                self.putg(ss, es, [ANN_DATA_BIT, texts])
                self.symbols_append(ss, es, 'DATA_BIT', bit_level)
                ss, es = self.symbols_get_last()[:2]
                self.putpy(ss, es, 'DATA_BIT', bit_level)
                bit_field.append(bit_level)
                if self.data_bits is not None:
                    self.data_bits.append(bit_level)
                bit_ss = bit_es
            end_snum = bit_es
            curr_level, = self.wait_until(end_snum)
            curr_snum = self.samplenum

            # We are at the exact _calculated_ boundary of the last DATA
            # bit time. Improve robustness for those situations where
            # the transmitter's and the sender's timings differ within a
            # margin, and the transmitter may hold the last DATA bit's
            # HIGH level for a little longer.
            #
            # When no falling edge is seen within the maximum tolerance
            # for the last DATA bit, then this could be the combination
            # of a HIGH DATA bit and a PAD bit without a LOW in between.
            # Fake an edge in that case, to re-use existing code paths.
            # Make sure to keep referencing times to the last SYNC pad's
            # falling edge. This is the last reliable condition we have.
            if curr_level:
                hold = self.hold_high_width
                curr_level, = self.wait([{PIN_DATA: 'l'}, {'skip': int(hold)}])
                self.carrier_check(curr_level, self.samplenum)
                if self.matched[1]:
                    self.edges.append(curr_snum)
                    curr_level = 1 - curr_level
                curr_snum = self.samplenum

            # Get the byte value from the bits (when available).
            # TODO Has the local 'bit_field' become obsolete, or should
            # self.data_bits go away?
            data_byte = bitpack(bit_field)
            if self.data_bits is not None:
                data_byte = bitpack(self.data_bits)
                self.data_bits.clear()
                if self.frame_bytes is not None:
                    self.frame_bytes.append(data_byte)

            # Turn a sequence of a SYNC-PAD and eight DATA bits into a
            # DATA-BYTE symbol.
            byte_seq = ['SYNC_PAD'] + 8 * ['DATA_BIT']
            if self.symbols_has_prev(byte_seq):
                self.symbols_collapse(len(byte_seq), 'DATA_BYTE')
                ss, es = self.symbols_get_last()[:2]
                texts = ['{:02x}'.format(data_byte)]
                self.putg(ss, es, [ANN_DATA_BYTE, texts])
                self.putpy(ss, es, 'DATA_BYTE', data_byte)

            # Optionally terminate the accumulation of a frame when a
            # WAIT-ACK period was followed by a DATA-BYTE? This could
            # flush the current packet before the next FRAME-INIT or
            # IDLE are seen, and increases usability for short input
            # data (aggressive trimming). It won't help when WAIT is
            # not seen, though.
            sync_resp_seq = ['WAIT_ACK'] + ['DATA_BYTE']
            if self.symbols_has_prev(sync_resp_seq):
                self.frame_flush()
