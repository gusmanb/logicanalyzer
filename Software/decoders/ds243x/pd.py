##
## This file is part of the libsigrokdecode project.
##
## Copyright (C) 2017 Kevin Redon <kingkevin@cuvoodoo.info>
## Copyright (C) 2017 Soeren Apel <soeren@apelpie.net>
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

# Dictionary of FUNCTION commands and their names.
commands_2432 = {
    0x0f: 'Write scratchpad',
    0xaa: 'Read scratchpad',
    0x55: 'Copy scratchpad',
    0xf0: 'Read memory',
    0x5a: 'Load first secret',
    0x33: 'Compute next secret',
    0xa5: 'Read authenticated page',
}

commands_2433 = {
    0x0f: 'Write scratchpad',
    0xaa: 'Read scratchpad',
    0x55: 'Copy scratchpad',
    0xf0: 'Read memory',
}

# Maxim DS243x family code, present at the end of the ROM code.
family_codes = {
    0x33: ('DS2432', commands_2432),
    0x23: ('DS2433', commands_2433),
}

# Calculate the CRC-16 checksum.
# Initial value: 0x0000, xor-in: 0x0000, polynom 0x8005, xor-out: 0xffff.
def crc16(byte_array):
    reverse = 0xa001 # Use the reverse polynom to make algo simpler.
    crc = 0x0000 # Initial value.
    # Reverse CRC calculation.
    for byte in byte_array:
        for bit in range(8):
            if (byte ^ crc) & 1:
                crc = (crc >> 1) ^ reverse
            else:
                crc >>= 1
            byte >>= 1
    crc ^= 0xffff # Invert CRC.
    return crc

class Decoder(srd.Decoder):
    api_version = 3
    id = 'ds243x'
    name = 'DS243x'
    longname = 'Maxim DS2432/3'
    desc = 'Maxim DS243x series 1-Wire EEPROM protocol.'
    license = 'gplv2+'
    inputs = ['onewire_network']
    outputs = []
    tags = ['IC', 'Memory']
    annotations = (
        ('text', 'Text'),
    )
    binary = (
        ('mem_read', 'Data read from memory'),
    )

    def __init__(self):
        self.reset()

    def reset(self):
        # Bytes for function command.
        self.bytes = []
        self.family_code = None
        self.family = ''
        self.commands = commands_2432 # Use max command set until we know better.

    def start(self):
        self.out_ann = self.register(srd.OUTPUT_ANN)
        self.out_binary = self.register(srd.OUTPUT_BINARY)

    def putx(self, data):
        self.put(self.ss, self.es, self.out_ann, data)

    def decode(self, ss, es, data):
        code, val = data

        if code == 'RESET/PRESENCE':
            self.ss, self.es = ss, es
            self.putx([0, ['Reset/presence: %s'
                           % ('true' if val else 'false')]])
            self.bytes = []
        elif code == 'ROM':
            self.ss, self.es = ss, es
            self.family_code = val & 0xff

            s = None
            if self.family_code in family_codes:
                self.family, self.commands = family_codes[val & 0xff]
                s = 'is 0x%02x, %s detected' % (self.family_code, self.family)
            else:
                s = '0x%02x unknown' % (self.family_code)

            self.putx([0, ['ROM: 0x%016x (%s)' % (val, 'family code ' + s),
                           'ROM: 0x%016x (%s)' % (val, self.family)]])
            self.bytes = []
        elif code == 'DATA':
            self.bytes.append(val)
            if 1 == len(self.bytes):
                self.ss, self.es = ss, es
                if val not in self.commands:
                    self.putx([0, ['Unrecognized command: 0x%02x' % val]])
                else:
                    self.putx([0, ['Function command: %s (0x%02x)'
                                   % (self.commands[val], val)]])
            elif 0x0f == self.bytes[0]: # Write scratchpad
                if 2 == len(self.bytes):
                    self.ss = ss
                elif 3 == len(self.bytes):
                    self.es = es
                    self.putx([0, ['Target address: 0x%04x'
                                   % ((self.bytes[2] << 8) + self.bytes[1])]])
                elif 4 == len(self.bytes):
                    self.ss = ss
                elif 11 == len(self.bytes):
                    self.es = es
                    self.putx([0, ['Data: ' + (','.join(format(n, '#04x')
                                       for n in self.bytes[3:11]))]])
                elif 12 == len(self.bytes):
                    self.ss = ss
                elif 13 == len(self.bytes):
                    self.es = es
                    self.putx([0, ['CRC: '
                        + ('ok' if crc16(self.bytes[0:11]) == (self.bytes[11]
                        + (self.bytes[12] << 8)) else 'error')]])
            elif 0xaa == self.bytes[0]: # Read scratchpad
                if 2 == len(self.bytes):
                    self.ss = ss
                elif 3 == len(self.bytes):
                    self.es = es
                    self.putx([0, ['Target address: 0x%04x'
                                   % ((self.bytes[2] << 8) + self.bytes[1])]])
                elif 4 == len(self.bytes):
                    self.ss, self.es = ss, es
                    self.putx([0, ['Data status (E/S): 0x%02x'
                                   % (self.bytes[3])]])
                elif 5 == len(self.bytes):
                    self.ss = ss
                elif 12 == len(self.bytes):
                    self.es = es
                    self.putx([0, ['Data: ' + (','.join(format(n, '#04x')
                                       for n in self.bytes[4:12]))]])
                elif 13 == len(self.bytes):
                    self.ss = ss
                elif 14 == len(self.bytes):
                    self.es = es
                    self.putx([0, ['CRC: '
                        + ('ok' if crc16(self.bytes[0:12]) == (self.bytes[12]
                        + (self.bytes[13] << 8)) else 'error')]])
            elif 0x5a == self.bytes[0]: # Load first secret
                if 2 == len(self.bytes):
                    self.ss = ss
                elif 4 == len(self.bytes):
                    self.es = es
                    self.putx([0, ['Authorization pattern (TA1, TA2, E/S): '
                        + (','.join(format(n, '#04x')
                            for n in self.bytes[1:4]))]])
                elif 4 < len(self.bytes):
                    self.ss, self.es = ss, es
                    if (0xaa == self.bytes[-1] or 0x55 == self.bytes[-1]):
                        self.putx([0, ['End of operation']])
            elif 0x33 == self.bytes[0]: # Compute next secret
                if 2 == len(self.bytes):
                    self.ss = ss
                elif 3 == len(self.bytes):
                    self.es = es
                    self.putx([0, ['Target address: 0x%04x'
                                   % ((self.bytes[2] << 8) + self.bytes[1])]])
                elif 3 < len(self.bytes):
                    self.ss, self.es = ss, es
                    if (0xaa == self.bytes[-1] or 0x55 == self.bytes[-1]):
                        self.putx([0, ['End of operation']])
            elif 0x55 == self.bytes[0]: # Copy scratchpad
                if 2 == len(self.bytes):
                    self.ss = ss
                elif 4 == len(self.bytes):
                    self.es = es
                    self.putx([0, ['Authorization pattern (TA1, TA2, E/S): '
                        + (','.join(format(n, '#04x')
                            for n in self.bytes[1:4]))]])
                elif 5 == len(self.bytes):
                    self.ss = ss
                elif 24 == len(self.bytes):
                    self.es = es
                    mac = ','.join(format(n, '#04x') for n in self.bytes[4:24])
                    self.putx([0, ['Message authentication code: ' + mac,
                                   'MAC: ' + mac]])
                elif 24 < len(self.bytes):
                    self.ss, self.es = ss, es
                    if (0xaa == self.bytes[-1] or 0x55 == self.bytes[-1]):
                        self.putx([0, ['Operation succeeded']])
                    elif (0 == self.bytes[-1]):
                        self.putx([0, ['Operation failed']])
            elif 0xa5 == self.bytes[0]: # Read authenticated page
                if 2 == len(self.bytes):
                    self.ss = ss
                elif 3 == len(self.bytes):
                    self.es = es
                    self.putx([0, ['Target address: 0x%04x'
                                   % ((self.bytes[2] << 8) + self.bytes[1])]])
                elif 4 == len(self.bytes):
                    self.ss = ss
                elif 35 == len(self.bytes):
                    self.es = es
                    self.putx([0, ['Data: ' + (','.join(format(n, '#04x')
                                       for n in self.bytes[3:35]))]])
                elif 36 == len(self.bytes):
                    self.ss, self.es = ss, es
                    self.putx([0, ['Padding: '
                        + ('ok' if 0xff == self.bytes[-1] else 'error')]])
                elif 37 == len(self.bytes):
                    self.ss = ss
                elif 38 == len(self.bytes):
                    self.es = es
                    self.putx([0, ['CRC: '
                        + ('ok' if crc16(self.bytes[0:36]) == (self.bytes[36]
                        + (self.bytes[37] << 8)) else 'error')]])
                elif 39 == len(self.bytes):
                    self.ss = ss
                elif 58 == len(self.bytes):
                    self.es = es
                    mac = ','.join(format(n, '#04x') for n in self.bytes[38:58])
                    self.putx([0, ['Message authentication code: ' + mac,
                                   'MAC: ' + mac]])
                elif 59 == len(self.bytes):
                    self.ss = ss
                elif 60 == len(self.bytes):
                    self.es = es
                    self.putx([0, ['MAC CRC: '
                        + ('ok' if crc16(self.bytes[38:58]) == (self.bytes[58]
                        + (self.bytes[59] << 8)) else 'error')]])
                elif 60 < len(self.bytes):
                    self.ss, self.es = ss, es
                    if (0xaa == self.bytes[-1] or 0x55 == self.bytes[-1]):
                        self.putx([0, ['Operation completed']])
            elif 0xf0 == self.bytes[0]: # Read memory
                if 2 == len(self.bytes):
                    self.ss = ss
                elif 3 == len(self.bytes):
                    self.es = es
                    self.putx([0, ['Target address: 0x%04x'
                                   % ((self.bytes[2] << 8) + self.bytes[1])]])
                elif 3 < len(self.bytes):
                    self.ss, self.es = ss, es
                    self.putx([0, ['Data: 0x%02x' % (self.bytes[-1])]])

                    bdata = self.bytes[-1].to_bytes(1, byteorder='big')
                    self.put(ss, es, self.out_binary, [0, bdata])
