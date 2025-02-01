##
## This file is part of the libsigrokdecode project.
##
## Copyright (C) 2018 Stephan Thiele <stephan.thiele@mailbox.org>
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

class LinFsm:
    class State:
        WaitForBreak = 'WAIT_FOR_BREAK'
        Sync = 'SYNC'
        Pid = 'PID'
        Data = 'DATA'
        Checksum = 'CHECKSUM'
        Error = 'ERROR'

    def transit(self, target_state):
        if not self._transition_allowed(target_state):
            return False
        self.state = target_state
        return True

    def _transition_allowed(self, target_state):
        if target_state == LinFsm.State.Error:
            return True
        return target_state in self.allowed_state[self.state]

    def reset(self):
        self.state = LinFsm.State.WaitForBreak
        self.uart_idle_count = 0

    def __init__(self):
        a = dict()
        a[LinFsm.State.WaitForBreak] = (LinFsm.State.Sync,)
        a[LinFsm.State.Sync]         = (LinFsm.State.Pid,)
        a[LinFsm.State.Pid]          = (LinFsm.State.Data,)
        a[LinFsm.State.Data]         = (LinFsm.State.Data, LinFsm.State.Checksum)
        a[LinFsm.State.Checksum]     = (LinFsm.State.WaitForBreak,)
        a[LinFsm.State.Error]        = (LinFsm.State.Sync,)
        self.allowed_state = a

        self.state = None
        self.uart_idle_count = 0
        self.reset()

class Decoder(srd.Decoder):
    api_version = 3
    id = 'lin'
    name = 'LIN'
    longname = 'Local Interconnect Network'
    desc = 'Local Interconnect Network (LIN) protocol.'
    license = 'gplv2+'
    inputs = ['uart']
    outputs = []
    tags = ['Automotive']
    options = (
        {'id': 'version', 'desc': 'Protocol version', 'default': 2, 'values': (1, 2)},
    )
    annotations = (
        ('data', 'LIN data'),
        ('control', 'Protocol info'),
        ('error', 'Error description'),
        ('inline_error', 'Protocol violation or error'),
    )
    annotation_rows = (
        ('data_vals', 'Data', (0, 1, 3)),
        ('errors', 'Errors', (2,)),
    )

    def __init__(self):
        self.reset()

    def reset(self):
        self.fsm = LinFsm()
        self.lin_header = []
        self.lin_rsp = []
        self.lin_version = None
        self.ss_block = None
        self.es_block = None

    def start(self):
        self.out_ann = self.register(srd.OUTPUT_ANN)
        self.lin_version = self.options['version']

    def putx(self, data):
        self.put(self.ss_block, self.es_block, self.out_ann, data)

    def wipe_break_null_byte(self, value):
        # Upon a break condition a null byte is received which must be ignored.
        if self.fsm.state not in (LinFsm.State.WaitForBreak, LinFsm.State.Error):
            if len(self.lin_rsp):
                value = self.lin_rsp.pop()[2]
            else:
                self.lin_header.pop()

        if value != 0:
            self.fsm.transit(LinFsm.State.Error)
            self.handle_error(None)
            return False

        return True

    def handle_uart_idle(self):
        if self.fsm.state not in (LinFsm.State.WaitForBreak, LinFsm.State.Error):
            self.fsm.uart_idle_count += 1

            if self.fsm.uart_idle_count == 2:
                self.fsm.transit(LinFsm.State.Checksum)
                self.handle_checksum()
                self.fsm.reset()

    def handle_wait_for_break(self, value):
        self.wipe_break_null_byte(value)

    def handle_break(self, value):
        if self.fsm.state not in (LinFsm.State.WaitForBreak, LinFsm.State.Error):
            if self.wipe_break_null_byte(value):
                self.fsm.transit(LinFsm.State.Checksum)
                self.handle_checksum()

        self.fsm.reset()
        self.fsm.transit(LinFsm.State.Sync)

        self.putx([1, ['Break condition', 'Break', 'Brk', 'B']])

    def handle_sync(self, value):
        self.fsm.transit(LinFsm.State.Pid)
        self.lin_header.append((self.ss_block, self.es_block, value))

    def handle_pid(self, value):
        self.fsm.transit(LinFsm.State.Data)
        self.lin_header.append((self.ss_block, self.es_block, value))

    def handle_data(self, value):
        self.lin_rsp.append((self.ss_block, self.es_block, value))

    def handle_checksum(self):
        sync = self.lin_header.pop(0) if len(self.lin_header) else None

        self.put(sync[0], sync[1], self.out_ann, [0, ['Sync', 'S']])

        if sync[2] != 0x55:
            self.put(sync[0], sync[1], self.out_ann,
                     [2, ['Sync is not 0x55', 'Not 0x55', '!= 0x55']])

        pid = self.lin_header.pop(0) if len(self.lin_header) else None
        checksum = self.lin_rsp.pop() if len(self.lin_rsp) else None

        if pid:
            id_ = pid[2] & 0x3F
            parity = pid[2] >> 6

            expected_parity = self.calc_parity(pid[2])
            parity_valid = parity == expected_parity

            if not parity_valid:
                self.put(pid[0], pid[1], self.out_ann, [2, ['P != %d' % expected_parity]])

            ann_class = 0 if parity_valid else 3
            self.put(pid[0], pid[1], self.out_ann, [ann_class, [
                'ID: %02X Parity: %d (%s)' % (id_, parity, 'ok' if parity_valid else 'bad'),
                'ID: 0x%02X' % id_, 'I: %d' % id_
            ]])

        if len(self.lin_rsp):
            checksum_valid = self.checksum_is_valid(pid[2], self.lin_rsp, checksum[2])

            for b in self.lin_rsp:
                self.put(b[0], b[1], self.out_ann, [0, ['Data: 0x%02X' % b[2], 'D: 0x%02X' % b[2]]])

            ann_class = 0 if checksum_valid else 3
            self.put(checksum[0], checksum[1], self.out_ann,
                 [ann_class, ['Checksum: 0x%02X' % checksum[2], 'Checksum', 'Chk', 'C']])

            if not checksum_valid:
                self.put(checksum[0], checksum[1], self.out_ann, [2, ['Checksum invalid']])
        else:
            pass # No response.

        self.lin_header.clear()
        self.lin_rsp.clear()

    def handle_error(self, dummy):
        self.putx([3, ['Error', 'Err', 'E']])

    def checksum_is_valid(self, pid, data, checksum):
        if self.lin_version == 2:
            id_ = pid & 0x3F

            if id_ != 60 and id_ != 61:
                checksum += pid

        for d in data:
            checksum += d[2]

        carry_bits = int(checksum / 256)
        checksum += carry_bits

        return checksum & 0xFF == 0xFF

    @staticmethod
    def calc_parity(pid):
        id_ = [((pid & 0x3F) >> i) & 1 for i in range(8)]

        p0 = id_[0] ^ id_[1] ^ id_[2] ^ id_[4]
        p1 = not (id_[1] ^ id_[3] ^ id_[4] ^ id_[5])

        return (p0 << 0) | (p1 << 1)

    def decode(self, ss, es, data):
        ptype, rxtx, pdata = data

        self.ss_block, self.es_block = ss, es

        # Ignore all UART packets except the actual data packets or BREAK.
        if ptype == 'IDLE':
            self.handle_uart_idle()
        if ptype == 'BREAK':
            self.handle_break(pdata)
        if ptype != 'DATA':
            return

        # We're only interested in the byte value (not individual bits).
        pdata = pdata[0]

        # Short LIN overview:
        #  - Message begins with a BREAK (0x00) for at least 13 bittimes.
        #  - Break is always followed by a SYNC byte (0x55).
        #  - Sync byte is followed by a PID byte (Protected Identifier).
        #  - PID byte is followed by 1 - 8 data bytes and a final checksum byte.

        handler = getattr(self, 'handle_%s' % self.fsm.state.lower())
        handler(pdata)
