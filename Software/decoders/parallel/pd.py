##
## This file is part of the libsigrokdecode project.
##
## Copyright (C) 2013-2016 Uwe Hermann <uwe@hermann-uwe.de>
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
from common.srdhelper import bitpack

'''
OUTPUT_PYTHON format:

Packet:
[<ptype>, <pdata>]

<ptype>, <pdata>
 - 'ITEM', [<item>, <itembitsize>]
 - 'WORD', [<word>, <wordbitsize>, <worditemcount>]

<item>:
 - A single item (a number). It can be of arbitrary size. The max. number
   of bits in this item is specified in <itembitsize>.

<itembitsize>:
 - The size of an item (in bits). For a 4-bit parallel bus this is 4,
   for a 16-bit parallel bus this is 16, and so on.

<word>:
 - A single word (a number). It can be of arbitrary size. The max. number
   of bits in this word is specified in <wordbitsize>. The (exact) number
   of items in this word is specified in <worditemcount>.

<wordbitsize>:
 - The size of a word (in bits). For a 2-item word with 8-bit items
   <wordbitsize> is 16, for a 3-item word with 4-bit items <wordbitsize>
   is 12, and so on.

<worditemcount>:
 - The size of a word (in number of items). For a 4-item word (no matter
   how many bits each item consists of) <worditemcount> is 4, for a 7-item
   word <worditemcount> is 7, and so on.
'''

NUM_CHANNELS = 16

class Pin:
    CLOCK = 0
    DATA_0 = CLOCK + 1
    DATA_N = DATA_0 + NUM_CHANNELS
    # BEWARE! DATA_N points _beyond_ the data partition (Python range(3)
    # semantics, useful to have to simplify other code locations).
    RESET = DATA_N

class Ann:
    ITEM, WORD, WARN = range(3)

class ChannelError(Exception):
    pass

class Decoder(srd.Decoder):
    api_version = 3
    id = 'parallel'
    name = 'Parallel'
    longname = 'Parallel sync bus'
    desc = 'Generic parallel synchronous bus.'
    license = 'gplv2+'
    inputs = ['logic']
    outputs = ['parallel']
    tags = ['Util']
    optional_channels = tuple(
        [{'id': 'clk', 'name': 'CLK', 'desc': 'Clock line'}] +
        [
            {'id': 'd%d' % i, 'name': 'D%d' % i, 'desc': 'Data line %d' % i}
            for i in range(NUM_CHANNELS)
        ] +
        [{'id': 'rst', 'name': 'RST', 'desc': 'RESET line'}]
    )
    options = (
        {'id': 'clock_edge', 'desc': 'Clock edge to sample on',
            'default': 'rising', 'values': ('rising', 'falling', 'either')},
        {'id': 'reset_polarity', 'desc': 'Reset line polarity',
            'default': 'low-active', 'values': ('low-active', 'high-active')},
        {'id': 'wordsize', 'desc': 'Data wordsize (# bus cycles)',
            'default': 0},
        {'id': 'endianness', 'desc': 'Data endianness',
            'default': 'little', 'values': ('little', 'big')},
    )
    annotations = (
        ('item', 'Item'),
        ('word', 'Word'),
        ('warning', 'Warning'),
    )
    annotation_rows = (
        ('items', 'Items', (Ann.ITEM,)),
        ('words', 'Words', (Ann.WORD,)),
        ('warnings', 'Warnings', (Ann.WARN,)),
    )
    binary = (
        ('binary', 'Binary'),
    )

    def __init__(self):
        self.reset()

    def reset(self):
        self.pend_item = None
        self.word_items = []

    def start(self):
        self.out_python = self.register(srd.OUTPUT_PYTHON)
        self.out_binary = self.register(srd.OUTPUT_BINARY)
        self.out_ann = self.register(srd.OUTPUT_ANN)

    def putg(self, ss, es, ann, txts):
        self.put(ss, es, self.out_ann, [ann, txts])

    def putpy(self, ss, es, ann, data):
        self.put(ss, es, self.out_python, [ann, data])

    def putbin(self, ss, es, ann_class, data):
        self.put(ss, es, self.out_binary, [ann_class, data])

    def flush_word(self, bus_width):
        if not self.word_items:
            return
        word_size = self.options['wordsize']

        items = self.word_items
        ss, es = items[0][0], items[-1][1]
        items = [i[2] for i in items]
        if self.options['endianness'] == 'big':
            items.reverse()
        word = sum([d << (i * bus_width) for i, d in enumerate(items)])

        txts = [self.fmt_word.format(word)]
        self.putg(ss, es, Ann.WORD, txts)
        self.putpy(ss, es, 'WORD', (word, bus_width, word_size))

        if len(items) != word_size:
            txts = ['incomplete word size', 'word size', 'ws']
            self.putg(ss, es, Ann.WARN, txts)

        self.word_items.clear()

    def queue_word(self, now, item, bus_width):
        wordsize = self.options['wordsize']
        if not wordsize:
            return

        # Terminate a previously seen item of a word first. Emit the
        # word's annotation when the last item's end was seen.
        if self.word_items:
            ss, _, data = self.word_items[-1]
            es = now
            self.word_items[-1] = (ss, es, data)
            if len(self.word_items) == wordsize:
                self.flush_word(bus_width)

        # Start tracking the currently seen item (yet unknown end time).
        if item is not None:
            pend = (now, None, item)
            self.word_items.append(pend)

    def handle_bits(self, now, item, bus_width):

        # Optionally flush a previously started item.
        if self.pend_item:
            ss, _, data = self.pend_item
            self.pend_item = None
            es = now
            txts = [self.fmt_item.format(data)]
            self.putg(ss, es, Ann.ITEM, txts)
            self.putpy(ss, es, 'ITEM', (data, bus_width))
            self.putbin(ss, es, 0, data.to_bytes(1, byteorder='big'))

        # Optionally queue the currently seen item.
        if item is not None:
            self.pend_item = (now, None, item)

        # Pass the current item to the word accumulation logic.
        self.queue_word(now, item, bus_width)

    def decode(self):
        # Determine which (optional) channels have input data. Insist in
        # a non-empty input data set. Cope with sparse connection maps.
        # Store enough state to later "compress" sampled input data.
        data_indices = [
            idx if self.has_channel(idx) else None
            for idx in range(Pin.DATA_0, Pin.DATA_N)
        ]
        has_data = [idx for idx in data_indices if idx is not None]
        if not has_data:
            raise ChannelError('Need at least one data channel.')
        max_connected = max(has_data)

        # Pre-determine which input data to strip off, the width of
        # individual items and multiplexed words, as well as format
        # strings here. This simplifies call sites which run in tight
        # loops later.
        upper_data_bound = max_connected + 1
        num_item_bits = upper_data_bound - Pin.DATA_0
        num_word_items = self.options['wordsize']
        num_word_bits = num_item_bits * num_word_items
        num_digits = (num_item_bits + 4 - 1) // 4
        self.fmt_item = "{{:0{}x}}".format(num_digits)
        num_digits = (num_word_bits + 4 - 1) // 4
        self.fmt_word = "{{:0{}x}}".format(num_digits)

        # Determine .wait() conditions, depending on the presence of a
        # clock signal. Either inspect samples on the configured edge of
        # the clock, or inspect samples upon ANY edge of ANY of the pins
        # which provide input data.
        conds = []
        cond_idx_clock = None
        cond_idx_data_0 = None
        cond_idx_data_N = None
        cond_idx_reset = None
        has_clock = self.has_channel(Pin.CLOCK)
        if has_clock:
            cond_idx_clock = len(conds)
            edge = {
                'rising': 'r',
                'falling': 'f',
                'either': 'e',
            }.get(self.options['clock_edge'])
            conds.append({Pin.CLOCK: edge})
        else:
            cond_idx_data_0 = len(conds)
            conds.extend([{idx: 'e'} for idx in has_data])
            cond_idx_data_N = len(conds)
        has_reset = self.has_channel(Pin.RESET)
        if has_reset:
            cond_idx_reset = len(conds)
            conds.append({Pin.RESET: 'e'})
            reset_active = {
                'low-active': 0,
                'high-active': 1,
            }.get(self.options['reset_polarity'])

        # Keep processing the input stream. Assume "always zero" for
        # not-connected input lines. Pass data bits (all inputs except
        # clock and reset) to the handle_bits() method. Handle reset
        # edges first and data changes then, within the same iteration.
        # This results in robust operation for low-oversampled input.
        in_reset = False
        while True:
            try:
                pins = self.wait(conds)
            except EOFError as e:
                break
            clock_edge = cond_idx_clock is not None and self.matched[cond_idx_clock]
            data_edge = cond_idx_data_0 is not None and [idx for idx in range(cond_idx_data_0, cond_idx_data_N) if self.matched[idx]]
            reset_edge = cond_idx_reset is not None and self.matched[cond_idx_reset]

            if reset_edge:
                in_reset = pins[Pin.RESET] == reset_active
                if in_reset:
                    self.handle_bits(self.samplenum, None, num_item_bits)
                    self.flush_word(num_item_bits)
            if in_reset:
                continue

            if clock_edge or data_edge:
                data_bits = [0 if idx is None else pins[idx] for idx in data_indices]
                data_bits = data_bits[:num_item_bits]
                item = bitpack(data_bits)
                self.handle_bits(self.samplenum, item, num_item_bits)

        self.handle_bits(self.samplenum, None, num_item_bits)
        # TODO Determine whether a WARN annotation needs to get emitted.
        # The decoder has not seen the end of the last accumulated item.
        # Instead it just ran out of input data.
