##
## This file is part of the libsigrokdecode project.
##
## Copyright (C) 2018 Elias Oenal <sigrok@eliasoenal.com>
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

MODULE_ID = {
    0x00: 'Unknown or unspecified',
    0x01: 'GBIC',
    0x02: 'Module/connector soldered to motherboard',
    0x03: 'SFP',
    0x04: '300 pin XSBI',
    0x05: 'XENPAK',
    0x06: 'XFP',
    0x07: 'XFF',
    0x08: 'XFP-E',
    0x09: 'XPAK',
    0x0a: 'X2',
    0x0B: 'DWDM-SFP',
    0x0C: 'QSFP',
    0x0D: 'QSFP+',
    0x0E: 'CFP',
    0x0F: 'CXP (TBD)',
    0x11: 'CFP2',
    0x12: 'CFP4',
}

class Decoder(srd.Decoder):
    api_version = 3
    id = 'cfp'
    name = 'CFP'
    longname = '100 Gigabit C form-factor pluggable'
    desc = '100 Gigabit C form-factor pluggable (CFP) protocol.'
    license = 'BSD'
    inputs = ['mdio']
    outputs = []
    tags = ['Networking']
    annotations = (
        ('register', 'Register'),
        ('decode', 'Decode'),
    )
    annotation_rows = (
        ('registers', 'Registers', (0,)),
        ('decodes', 'Decodes', (1,)),
    )

    def __init__(self):
        self.reset()

    def reset(self):
        pass

    def start(self):
        self.out_ann = self.register(srd.OUTPUT_ANN)

    def putx(self, data):
        self.put(self.ss, self.es, self.out_ann, data)

    def decode(self, ss, es, data):
        self.ss, self.es = ss, es
        for (clause45, clause45_addr, is_read, portad, devad, reg) in data:
            if not is_read:
                continue
            if clause45_addr in range(0x8000, 0x807F + 1):
                self.putx([0, ['CFP NVR 1: Basic ID register', 'NVR1']])
                if clause45_addr == 0x8000:
                    self.putx([1, ['Module identifier: %s' % \
                              MODULE_ID.get(reg, 'Reserved')]])
            elif clause45_addr in range(0x8080, 0x80FF + 1):
                self.putx([0, ['CFP NVR 2: Extended ID register', 'NVR2']])
            elif clause45_addr in range(0x8100, 0x817F + 1):
                self.putx([0, ['CFP NVR 3: Network lane specific register', 'NVR3']])
            elif clause45_addr in range(0x8180, 0x81FF + 1):
                self.putx([0, ['CFP NVR 4', 'NVR4']])
            elif clause45_addr in range(0x8400, 0x847F + 1):
                self.putx([0, ['Vendor NVR 1: Vendor data register', 'V-NVR1']])
            elif clause45_addr in range(0x8480, 0x84FF + 1):
                self.putx([0, ['Vendor NVR 2: Vendor data register', 'V-NVR2']])
            elif clause45_addr in range(0x8800, 0x887F + 1):
                self.putx([0, ['User NVR 1: User data register', 'U-NVR1']])
            elif clause45_addr in range(0x8880, 0x88FF + 1):
                self.putx([0, ['User NVR 2: User data register', 'U-NVR2']])
            elif clause45_addr in range(0xA000, 0xA07F + 1):
                self.putx([0, ['CFP Module VR 1: CFP Module level control and DDM register', 'Mod-VR1']])
            elif clause45_addr in range(0xA080, 0xA0FF + 1):
                self.putx([0, ['MLG VR 1: MLG Management Interface register', 'MLG-VR1']])
