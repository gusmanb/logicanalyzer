##
## This file is part of the libsigrokdecode project.
##
## Copyright (C) 2012-2013 Uwe Hermann <uwe@hermann-uwe.de>
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

# ...
RX = 0
TX = 1

class Decoder(srd.Decoder):
    api_version = 3
    id = 'pan1321'
    name = 'PAN1321'
    longname = 'Panasonic PAN1321'
    desc = 'Bluetooth RF module with Serial Port Profile (SPP).'
    license = 'gplv2+'
    inputs = ['uart']
    outputs = []
    tags = ['Wireless/RF']
    annotations = (
        ('text-verbose', 'Text (verbose)'),
        ('text', 'Text'),
        ('warning', 'Warning'),
    )

    def __init__(self):
        self.reset()

    def reset(self):
        self.cmd = ['', '']
        self.ss_block = None

    def start(self):
        self.out_ann = self.register(srd.OUTPUT_ANN)

    def putx(self, data):
        self.put(self.ss_block, self.es_block, self.out_ann, data)

    def handle_host_command(self, rxtx, s):
        if s.startswith('AT+JAAC'):
            # AT+JAAC=<auto_accept> (0 or 1)
            p = s[s.find('=') + 1:]
            if p not in ('0', '1'):
                self.putx([2, ['Warning: Invalid JAAC parameter "%s"' % p]])
                return
            x = 'Auto' if (p == '1') else 'Don\'t auto'
            self.putx([0, ['%s-accept new connections' % x]])
            self.putx([1, ['%s-accept connections' % x]])
        elif s.startswith('AT+JPRO'):
            # AT+JPRO=<mode> (0 or 1)
            p = s[s.find('=') + 1:]
            if p not in ('0', '1'):
                self.putx([2, ['Warning: Invalid JPRO parameter "%s"' % p]])
                return
            onoff = 'off' if (p == '0') else 'on'
            x = 'Leaving' if (p == '0') else 'Entering'
            self.putx([0, ['%s production mode' % x]])
            self.putx([1, ['Production mode = %s' % onoff]])
        elif s.startswith('AT+JRES'):
            # AT+JRES
            if s != 'AT+JRES': # JRES has no params.
                self.putx([2, ['Warning: Invalid JRES usage.']])
                return
            self.putx([0, ['Triggering a software reset']])
            self.putx([1, ['Reset']])
        elif s.startswith('AT+JSDA'):
            # AT+JSDA=<l>,<d> (l: length in bytes, d: data)
            # l is (max?) 3 decimal digits and ranges from 1 to MTU size.
            # Data can be ASCII or binary values (l bytes total).
            l, d = s[s.find('=') + 1:].split(',')
            if not l.isnumeric():
                self.putx([2, ['Warning: Invalid data length "%s".' % l]])
            if int(l) != len(d):
                self.putx([2, ['Warning: Data length mismatch (%d != %d).' % \
                          (int(l), len(d))]])
            # TODO: Warn if length > MTU size (which is firmware-dependent
            # and is negotiated by both Bluetooth devices upon connection).
            b = ''.join(['%02x ' % ord(c) for c in d])[:-1]
            self.putx([0, ['Sending %d data bytes: %s' % (int(l), b)]])
            self.putx([1, ['Send %d = %s' % (int(l), b)]])
        elif s.startswith('AT+JSEC'):
            # AT+JSEC=<secmode>,<linkkey_info>,<pintype>,<pinlen>,<pin>
            # secmode: Security mode 1 or 3 (default).
            # linkkey_info: Must be 1 or 2. Has no function according to docs.
            # pintype: 1: variable pin (default), 2: fixed pin.
            # pinlen: PIN length (2 decimal digits). Max. PIN length is 16.
            # pin: The Bluetooth PIN ('pinlen' chars). Used if pintype=2.
            # Note: AT+JSEC (if used) must be the first command after reset.
            # TODO: Parse all the other parameters.
            pin = s[-4:]
            self.putx([0, ['Host set the Bluetooth PIN to "' + pin + '"']])
            self.putx([1, ['PIN = ' + pin]])
        elif s.startswith('AT+JSLN'):
            # AT+JSLN=<namelen>,<name>
            # namelen: Friendly name length (2 decimal digits). Max. len is 18.
            # name: The Bluetooth "friendly name" ('namelen' ASCII characters).
            name = s[s.find(',') + 1:]
            self.putx([0, ['Host set the Bluetooth name to "' + name + '"']])
            self.putx([1, ['BT name = ' + name]])
        else:
            self.putx([0, ['Host sent unsupported command: %s' % s]])
            self.putx([1, ['Unsupported command: %s' % s]])

    def handle_device_reply(self, rxtx, s):
        if s == 'ROK':
            self.putx([0, ['Device initialized correctly']])
            self.putx([1, ['Init']])
        elif s == 'OK':
            self.putx([0, ['Device acknowledged last command']])
            self.putx([1, ['ACK']])
        elif s.startswith('ERR'):
            error = s[s.find('=') + 1:]
            self.putx([0, ['Device sent error code ' + error]])
            self.putx([1, ['ERR = ' + error]])
        else:
            self.putx([0, ['Device sent an unknown reply: %s' % s]])
            self.putx([1, ['Unknown reply: %s' % s]])

    def decode(self, ss, es, data):
        ptype, rxtx, pdata = data

        # For now, ignore all UART packets except the actual data packets.
        if ptype != 'DATA':
            return

        # We're only interested in the byte value (not individual bits).
        pdata = pdata[0]

        # If this is the start of a command/reply, remember the start sample.
        if self.cmd[rxtx] == '':
            self.ss_block = ss

        # Append a new (ASCII) byte to the currently built/parsed command.
        self.cmd[rxtx] += chr(pdata)

        # Get packets/bytes until an \r\n sequence is found (end of command).
        if self.cmd[rxtx][-2:] != '\r\n':
            return

        # Handle host commands and device replies.
        # We remove trailing \r\n from the strings before handling them.
        self.es_block = es
        if rxtx == RX:
            self.handle_device_reply(rxtx, self.cmd[rxtx][:-2])
        elif rxtx == TX:
            self.handle_host_command(rxtx, self.cmd[rxtx][:-2])

        self.cmd[rxtx] = ''
