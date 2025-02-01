##
## This file is part of the libsigrokdecode project.
##
## Copyright (C) 2012 Uwe Hermann <uwe@hermann-uwe.de>
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

# Definitions of various bits in MXC6225XU registers.
status = {
    # SH[1:0]
    'sh': {
        0b00: 'none',
        0b01: 'shake left',
        0b10: 'shake right',
        0b11: 'undefined',
    },
    # ORI[1:0] and OR[1:0] (same format)
    'ori': {
        0b00: 'vertical in upright orientation',
        0b01: 'rotated 90 degrees clockwise',
        0b10: 'vertical in inverted orientation',
        0b11: 'rotated 90 degrees counterclockwise',
    },
    # SHTH[1:0]
    'shth': {
        0b00: '0.5g',
        0b01: '1.0g',
        0b10: '1.5g',
        0b11: '2.0g',
    },
    # SHC[1:0]
    'shc': {
        0b00: '16',
        0b01: '32',
        0b10: '64',
        0b11: '128',
    },
    # ORC[1:0]
    'orc': {
        0b00: '16',
        0b01: '32',
        0b10: '64',
        0b11: '128',
    },
}

class Decoder(srd.Decoder):
    api_version = 3
    id = 'mxc6225xu'
    name = 'MXC6225XU'
    longname = 'MEMSIC MXC6225XU'
    desc = 'Digital Thermal Orientation Sensor (DTOS) protocol.'
    license = 'gplv2+'
    inputs = ['i2c']
    outputs = []
    tags = ['IC', 'Sensor']
    annotations = (
        ('text', 'Text'),
    )

    def __init__(self):
        self.reset()

    def reset(self):
        self.state = 'IDLE'

    def start(self):
        self.out_ann = self.register(srd.OUTPUT_ANN)

    def putx(self, data):
        self.put(self.ss, self.es, self.out_ann, data)

    def handle_reg_0x00(self, b):
        # XOUT: 8-bit x-axis acceleration output.
        # Data is in 2's complement, values range from -128 to 127.
        self.putx([0, ['XOUT: %d' % b]])

    def handle_reg_0x01(self, b):
        # YOUT: 8-bit y-axis acceleration output.
        # Data is in 2's complement, values range from -128 to 127.
        self.putx([0, ['YOUT: %d' % b]])

    def handle_reg_0x02(self, b):
        # STATUS: Orientation and shake status.

        # Bits[7:7]: INT
        int_val = (b >> 7) & 1
        s = 'unchanged and no' if (int_val == 0) else 'changed or'
        ann = 'INT = %d: Orientation %s shake event occurred\n' % (int_val, s)

        # Bits[6:5]: SH[1:0]
        sh = (((b >> 6) & 1) << 1) | ((b >> 5) & 1)
        ann += 'SH[1:0] = %s: Shake event: %s\n' % \
               (bin(sh)[2:], status['sh'][sh])

        # Bits[4:4]: TILT
        tilt = (b >> 4) & 1
        s = '' if (tilt == 0) else 'not '
        ann += 'TILT = %d: Orientation measurement is %svalid\n' % (tilt, s)

        # Bits[3:2]: ORI[1:0]
        ori = (((b >> 3) & 1) << 1) | ((b >> 2) & 1)
        ann += 'ORI[1:0] = %s: %s\n' % (bin(ori)[2:], status['ori'][ori])

        # Bits[1:0]: OR[1:0]
        or_val = (((b >> 1) & 1) << 1) | ((b >> 0) & 1)
        ann += 'OR[1:0] = %s: %s\n' % (bin(or_val)[2:], status['ori'][or_val])

        # ann += 'b = %s\n' % (bin(b))

        self.putx([0, [ann]])

    def handle_reg_0x03(self, b):
        # DETECTION: Powerdown, orientation and shake detection parameters.
        # Note: This is a write-only register.

        # Bits[7:7]: PD
        pd = (b >> 7) & 1
        s = 'Do not power down' if (pd == 0) else 'Power down'
        ann = 'PD = %d: %s the device (into a low-power state)\n' % (pd, s)

        # Bits[6:6]: SHM
        shm = (b >> 6) & 1
        ann = 'SHM = %d: Set shake mode to %d\n' % (shm, shm)

        # Bits[5:4]: SHTH[1:0]
        shth = (((b >> 5) & 1) << 1) | ((b >> 4) & 1)
        ann += 'SHTH[1:0] = %s: Set shake threshold to %s\n' \
               % (bin(shth)[2:], status['shth'][shth])

        # Bits[3:2]: SHC[1:0]
        shc = (((b >> 3) & 1) << 1) | ((b >> 2) & 1)
        ann += 'SHC[1:0] = %s: Set shake count to %s readings\n' \
               % (bin(shc)[2:], status['shc'][shc])

        # Bits[1:0]: ORC[1:0]
        orc = (((b >> 1) & 1) << 1) | ((b >> 0) & 1)
        ann += 'ORC[1:0] = %s: Set orientation count to %s readings\n' \
               % (bin(orc)[2:], status['orc'][orc])

        self.putx([0, [ann]])

    # TODO: Fixup, this is copy-pasted from another PD.
    # TODO: Handle/check the ACKs/NACKs.
    def decode(self, ss, es, data):
        cmd, databyte = data

        # Store the start/end samples of this I²C packet.
        self.ss, self.es = ss, es

        # State machine.
        if self.state == 'IDLE':
            # Wait for an I²C START condition.
            if cmd != 'START':
                return
            self.state = 'GET SLAVE ADDR'
        elif self.state == 'GET SLAVE ADDR':
            # Wait for an address write operation.
            # TODO: We should only handle packets to the slave(?)
            if cmd != 'ADDRESS WRITE':
                return
            self.state = 'GET REG ADDR'
        elif self.state == 'GET REG ADDR':
            # Wait for a data write (master selects the slave register).
            if cmd != 'DATA WRITE':
                return
            self.reg = databyte
            self.state = 'WRITE REGS'
        elif self.state == 'WRITE REGS':
            # If we see a Repeated Start here, it's a multi-byte read.
            if cmd == 'START REPEAT':
                self.state = 'READ REGS'
                return
            # Otherwise: Get data bytes until a STOP condition occurs.
            if cmd == 'DATA WRITE':
                handle_reg = getattr(self, 'handle_reg_0x%02x' % self.reg)
                handle_reg(databyte)
                self.reg += 1
                # TODO: Check for NACK!
            elif cmd == 'STOP':
                # TODO
                self.state = 'IDLE'
            else:
                pass # TODO
        elif self.state == 'READ REGS':
            # Wait for an address read operation.
            # TODO: We should only handle packets to the slave(?)
            if cmd == 'ADDRESS READ':
                self.state = 'READ REGS2'
                return
            else:
                pass # TODO
        elif self.state == 'READ REGS2':
            if cmd == 'DATA READ':
                handle_reg = getattr(self, 'handle_reg_0x%02x' % self.reg)
                handle_reg(databyte)
                self.reg += 1
                # TODO: Check for NACK!
            elif cmd == 'STOP':
                # TODO
                self.state = 'IDLE'
            else:
                pass # TODO?
