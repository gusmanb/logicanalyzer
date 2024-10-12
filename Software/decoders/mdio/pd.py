##
## This file is part of the libsigrokdecode project.
##
## Copyright (C) 2016 Elias Oenal <sigrok@eliasoenal.com>
## All rights reserved.
##
## Redistribution and use in source and binary forms, with or without
## modification, are permitted provided that the following conditions are met:
##
## 1. Redistributions of source code must retain the above copyright notice,
##    this list of conditions and the following disclaimer.
## 2. Redistributions in binary form must reproduce the above copyright notice,
##    this list of conditions and the following disclaimer in the documentation
##    and/or other materials provided with the distribution.
##
## THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS"
## AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE
## IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE
## ARE DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT OWNER OR CONTRIBUTORS BE
## LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR
## CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF
## SUBSTITUTE GOODS OR SERVICES; LOSS OF USE, DATA, OR PROFITS; OR BUSINESS
## INTERRUPTION) HOWEVER CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN
## CONTRACT, STRICT LIABILITY, OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE)
## ARISING IN ANY WAY OUT OF THE USE OF THIS SOFTWARE, EVEN IF ADVISED OF THE
## POSSIBILITY OF SUCH DAMAGE.
##

import sigrokdecode as srd

class Decoder(srd.Decoder):
    api_version = 3
    id = 'mdio'
    name = 'MDIO'
    longname = 'Management Data Input/Output'
    desc = 'MII management bus between MAC and PHY.'
    license = 'bsd'
    inputs = ['logic']
    outputs = ['mdio']
    tags = ['Networking']
    channels = (
        {'id': 'mdc', 'name': 'MDC', 'desc': 'Clock'},
        {'id': 'mdio', 'name': 'MDIO', 'desc': 'Data'},
    )
    options = (
        {'id': 'show_debug_bits', 'desc': 'Show debug bits',
            'default': 'no', 'values': ('yes', 'no')},
    )
    annotations = (
        ('bit-val', 'Bit value'),
        ('bit-num', 'Bit number'),
        ('frame', 'Frame'),
        ('frame-idle', 'Bus idle state'),
        ('frame-error', 'Frame error'),
        ('decode', 'Decode'),
    )
    annotation_rows = (
        ('bit-vals', 'Bit values', (0,)),
        ('bit-nums', 'Bit numbers', (1,)),
        ('frames', 'Frames', (2, 3)),
        ('frame-errors', 'Frame errors', (4,)),
        ('decode-vals', 'Decode', (5,)),
    )

    def __init__(self):
        self.reset()

    def reset(self):
        self.illegal_bus = 0
        self.clause45_addr = -1 # Clause 45 is context sensitive.
        self.reset_decoder_state()

    def start(self):
        self.out_python = self.register(srd.OUTPUT_PYTHON)
        self.out_ann = self.register(srd.OUTPUT_ANN)

    def putbit(self, mdio, ss, es):
        self.put(ss, es, self.out_ann, [0, ['%d' % mdio]])
        if self.options['show_debug_bits'] == 'yes':
            self.put(ss, es, self.out_ann, [1, ['%d' % (self.bitcount - 1), '%d' % ((self.bitcount - 1) % 10)]])

    def putff(self, data):
        self.put(self.ss_frame_field, self.samplenum, self.out_ann, data)

    def putdata(self):
        self.put(self.ss_frame_field, self.mdiobits[0][2], self.out_ann,
                 [2, ['DATA: %04X' % self.data, 'DATA', 'D']])

        if self.clause45 and self.opcode == 0:
            self.clause45_addr = self.data

        # Decode data.
        if self.opcode > 0 or not self.clause45:
            decoded_min = ''
            if self.clause45 and self.clause45_addr != -1:
                decoded_min += str.format('ADDR: %04X ' % self.clause45_addr)
            elif self.clause45:
                decoded_min += str.format('ADDR: UKWN ')

            if self.clause45 and self.opcode > 1 \
            or (not self.clause45 and self.opcode):
                decoded_min += str.format('READ:  %04X' % self.data)
                is_read = 1
            else:
                decoded_min += str.format('WRITE: %04X' % self.data)
                is_read = 0
            decoded_ext = str.format(' %s: %02d' % \
                        ('PRTAD' if self.clause45 else 'PHYAD', self.portad))
            decoded_ext += str.format(' %s: %02d' % \
                        ('DEVAD' if self.clause45 else 'REGAD', self.devad))
            if self.ta_invalid or self.op_invalid:
                decoded_ext += ' ERROR'
            self.put(self.ss_frame, self.mdiobits[0][2], self.out_ann,
                     [5, [decoded_min + decoded_ext, decoded_min]])

            self.put(self.ss_frame, self.mdiobits[0][2], self.out_python,
                     [(bool(self.clause45), int(self.clause45_addr), \
                       bool(is_read), int(self.portad), int(self.devad), \
                       int(self.data))])

        # Post read increment address.
        if self.clause45 and self.opcode == 2 and self.clause45_addr != -1:
            self.clause45_addr += 1

    def reset_decoder_state(self):
        self.mdiobits = []
        self.bitcount = -1
        self.opcode = -1
        self.clause45 = 0
        self.ss_frame = -1
        self.ss_frame_field = -1
        self.preamble_len = 0
        self.ta_invalid = -1
        self.op_invalid = ''
        self.portad = -1
        self.portad_bits = 5
        self.devad = -1
        self.devad_bits = 5
        self.data = -1
        self.data_bits = 16
        self.state = 'PRE'

    def state_PRE(self, mdio):
        if self.illegal_bus:
            if mdio == 0:   # Stay in illegal bus state.
                return
            else:           # Leave and continue parsing.
                self.illegal_bus = 0
                self.put(self.ss_illegal, self.samplenum, self.out_ann,
                         [4, ['ILLEGAL BUS STATE', 'ILL']])
                self.ss_frame = self.samplenum

        if self.ss_frame == -1:
            self.ss_frame = self.samplenum

        if mdio == 1:
            self.preamble_len += 1

        # Valid MDIO can't clock more than 16 succeeding ones without being
        # in either IDLE or PRE.
        if self.preamble_len > 16:
            if self.preamble_len >= 10000 + 32:
                self.put(self.ss_frame, self.mdiobits[32][1], self.out_ann,
                    [3, ['IDLE #%d' % (self.preamble_len - 32), 'IDLE', 'I']])
                self.ss_frame = self.mdiobits[32][1]
                self.preamble_len = 32
                # This is getting out of hand, free some memory.
                del self.mdiobits[33:-1]
            if mdio == 0:
                if self.preamble_len < 32:
                    self.ss_frame = self.mdiobits[self.preamble_len][1]
                    self.put(self.ss_frame, self.samplenum, self.out_ann,
                             [4, ['SHORT PREAMBLE', 'SHRT PRE']])
                elif self.preamble_len > 32:
                    self.ss_frame = self.mdiobits[32][1]
                    self.put(self.mdiobits[self.preamble_len][1],
                             self.mdiobits[32][1], self.out_ann,
                             [3, ['IDLE #%d' % (self.preamble_len - 32),
                             'IDLE', 'I']])
                    self.preamble_len = 32
                else:
                    self.ss_frame = self.mdiobits[32][1]
                self.put(self.ss_frame, self.samplenum, self.out_ann,
                         [2, ['PRE #%d' % self.preamble_len, 'PRE', 'P']])
                self.ss_frame_field = self.samplenum
                self.state = 'ST'
        elif mdio == 0:
                self.ss_illegal = self.ss_frame
                self.illegal_bus = 1

    def state_ST(self, mdio):
        if mdio == 0:
            self.clause45 = 1
        self.state = 'OP'

    def state_OP(self, mdio):
        if self.opcode == -1:
            if self.clause45:
                st = ['ST (Clause 45)', 'ST 45']
            else:
                st = ['ST (Clause 22)', 'ST 22']
            self.putff([2, st + ['ST', 'S']])
            self.ss_frame_field = self.samplenum

            if mdio:
                self.opcode = 2
            else:
                self.opcode = 0
        else:
            if self.clause45:
                self.state = 'PRTAD'
                self.opcode += mdio
            else:
                if mdio == self.opcode:
                    self.op_invalid = 'invalid for Clause 22'
                self.state = 'PRTAD'

    def state_PRTAD(self, mdio):
        if self.portad == -1:
            self.portad = 0
            if self.clause45:
                if self.opcode == 0:
                    op = ['OP: ADDR', 'OP: A']
                elif self.opcode == 1:
                    op = ['OP: WRITE', 'OP: W']
                elif self.opcode == 2:
                    op = ['OP: READINC', 'OP: RI']
                elif self.opcode == 3:
                    op = ['OP: READ', 'OP: R']
            else:
                op = ['OP: READ', 'OP: R'] if self.opcode else ['OP: WRITE', 'OP: W']
            self.putff([2, op + ['OP', 'O']])
            if self.op_invalid:
                self.putff([4, ['OP %s' % self.op_invalid, 'OP', 'O']])
            self.ss_frame_field = self.samplenum
        self.portad_bits -= 1
        self.portad |= mdio << self.portad_bits
        if not self.portad_bits:
            self.state = 'DEVAD'

    def state_DEVAD(self, mdio):
        if self.devad == -1:
            self.devad = 0
            if self.clause45:
                prtad = ['PRTAD: %02d' % self.portad, 'PRT', 'P']
            else:
                prtad = ['PHYAD: %02d' % self.portad, 'PHY', 'P']
            self.putff([2, prtad])
            self.ss_frame_field = self.samplenum
        self.devad_bits -= 1
        self.devad |= mdio << self.devad_bits
        if not self.devad_bits:
            self.state = 'TA'

    def state_TA(self, mdio):
        if self.ta_invalid == -1:
            self.ta_invalid = ''
            if self.clause45:
                regad = ['DEVAD: %02d' % self.devad, 'DEV', 'D']
            else:
                regad = ['REGAD: %02d' % self.devad, 'REG', 'R']
            self.putff([2, regad])
            self.ss_frame_field = self.samplenum
            if mdio != 1 and ((self.clause45 and self.opcode < 2)
            or (not self.clause45 and self.opcode == 0)):
                self.ta_invalid = ' invalid (bit1)'
        else:
            if mdio != 0:
                if self.ta_invalid:
                    self.ta_invalid = ' invalid (bit1 and bit2)'
                else:
                    self.ta_invalid = ' invalid (bit2)'
            self.state = 'DATA'

    def state_DATA(self, mdio):
        if self.data == -1:
            self.data = 0
            self.putff([2, ['TA', 'T']])
            if self.ta_invalid:
                self.putff([4, ['TA%s' % self.ta_invalid, 'TA', 'T']])
            self.ss_frame_field = self.samplenum
        self.data_bits -= 1
        self.data |= mdio << self.data_bits
        if not self.data_bits:
            # Output final bit.
            self.mdiobits[0][2] = self.mdiobits[0][1] + self.quartile_cycle_length()
            self.bitcount += 1
            self.putbit(self.mdiobits[0][0], self.mdiobits[0][1], self.mdiobits[0][2])
            self.putdata()
            self.reset_decoder_state()

    def process_state(self, argument, mdio):
        method_name = 'state_' + str(argument)
        method = getattr(self, method_name)
        return method(mdio)

    # Returns the first quartile point of the frames cycle lengths. This is a
    # conservative guess for the end of the last cycle. On average it will be
    # more likely to fall short, than being too long, which makes for better
    # readability in GUIs.
    def quartile_cycle_length(self):
        # 48 is the minimum number of samples we have to have at the end of a
        # frame. The last sample only has a leading clock edge and is ignored.
        bitlen = []
        for i in range(1, 49):
            bitlen.append(self.mdiobits[i][2] - self.mdiobits[i][1])
        bitlen = sorted(bitlen)
        return bitlen[12]

    def handle_bit(self, mdio):
        self.bitcount += 1
        self.mdiobits.insert(0, [mdio, self.samplenum, -1])

        if self.bitcount > 0:
            self.mdiobits[1][2] = self.samplenum # Note end of last cycle.
            # Output the last bit we processed.
            self.putbit(self.mdiobits[1][0], self.mdiobits[1][1], self.mdiobits[1][2])

        self.process_state(self.state, mdio)

    def decode(self):
        while True:
            # Process pin state upon rising MDC edge.
            pins = self.wait({0: 'r'})
            self.handle_bit(pins[1])
