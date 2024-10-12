##
## This file is part of the libsigrokdecode project.
##
## Copyright (C) 2018 Steve R <steversig@virginmedia.com>
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
import math
from .lists import *

class Decoder(srd.Decoder):
    api_version = 3
    id = 'ook_oregon'
    name = 'Oregon'
    longname = 'Oregon Scientific'
    desc = 'Oregon Scientific weather sensor protocol.'
    license = 'gplv2+'
    inputs = ['ook']
    outputs = []
    tags = ['Sensor']
    annotations = (
        ('bit', 'Bit'),
        ('field', 'Field'),
        ('l2', 'Level 2'),
        ('pre', 'Preamble'),
        ('syn', 'Sync'),
        ('id', 'SensorID'),
        ('ch', 'Channel'),
        ('roll', 'Rolling code'),
        ('f1', 'Flags1'),
    )
    annotation_rows = (
        ('bits', 'Bits', (0,)),
        ('fields', 'Fields', (1, 3, 4)),
        ('l2vals', 'Level 2', (2,)),
    )
    binary = (
        ('data-hex', 'Hex data'),
    )
    options = (
        {'id': 'unknown', 'desc': 'Unknown type is', 'default': 'Unknown',
         'values': ('Unknown', 'Temp', 'Temp_Hum', 'Temp_Hum1', 'Temp_Hum_Baro',
                    'Temp_Hum_Baro1', 'UV', 'UV1', 'Wind', 'Rain', 'Rain1')},
    )

    def __init__(self):
        self.reset()

    def reset(self):
        self.decoded = [] # Local cache of decoded OOK.
        self.skip = None

    def start(self):
        self.out_ann = self.register(srd.OUTPUT_ANN)
        self.out_binary = self.register(srd.OUTPUT_BINARY)
        self.unknown = self.options['unknown']

    def putx(self, data):
        self.put(self.ss, self.es, self.out_ann, data)

    def dump_oregon_hex(self, start, finish):
        nib = self.decoded_nibbles
        hexstring = ''
        for x in nib:
            hexstring += str(x[3]) if x[3] != '' else ' '
        s = 'Oregon ' + self.ver + ' \"' + hexstring.upper() + '\"\n'
        self.put(start, finish, self.out_binary,
                [0, bytes([ord(c) for c in s])])

    def oregon_put_pre_and_sync(self, len_pream, len_sync, ver):
        ook = self.decoded
        self.decode_pos = len_pream
        self.ss, self.es = ook[0][0], ook[self.decode_pos][0]
        self.putx([1, ['Oregon ' + ver + ' Preamble', ver + ' Preamble',
                        ver + ' Pre', ver]])
        self.decode_pos += len_sync
        self.ss, self.es = ook[len_pream][0], ook[self.decode_pos][0]
        self.putx([1, ['Sync', 'Syn', 'S']])

        # Strip off preamble and sync bits.
        self.decoded = self.decoded[self.decode_pos:]
        self.ookstring = self.ookstring[self.decode_pos:]
        self.ver = ver

    def oregon(self):
        self.ookstring = ''
        self.decode_pos = 0
        ook = self.decoded
        for i in range(len(ook)):
            self.ookstring += ook[i][2]
        if '10011001' in self.ookstring[:40]:
            (preamble, data) = self.ookstring.split('10011001', 1)
            if len(data) > 0 and len(preamble) > 16:
                self.oregon_put_pre_and_sync(len(preamble), 8, 'v2.1')
                self.oregon_v2()
        elif 'E1100' in self.ookstring[:17]:
            (preamble, data) = self.ookstring.split('E1100', 1)
            if len(data) > 0 and len(preamble) <= 12:
                self.oregon_put_pre_and_sync(len(preamble), 5, 'v1')
                self.oregon_v1()
        elif '0101' in self.ookstring[:28]:
            (preamble, data) = self.ookstring.split('0101', 1)
            if len(data) > 0 and len(preamble) > 12:
                self.oregon_put_pre_and_sync(len(preamble), 4, 'v3')
                self.oregon_v3()
        elif len(self.ookstring) > 16: # Ignore short packets.
            error_message = 'Not Oregon or wrong preamble'
            self.ss, self.es = ook[0][0], ook[len(ook) - 1][1]
            self.putx([1,[error_message]])

    def oregon_v1(self):
        ook = self.decoded
        self.decode_pos = 0
        self.decoded_nibbles = []
        if len(self.decoded) >= 32: # Check there are at least 8 nibbles.
            self.oregon_put_nib('RollingCode', ook[self.decode_pos][0],
                                ook[self.decode_pos + 3][1], 4)
            self.oregon_put_nib('Ch', ook[self.decode_pos][0],
                                ook[self.decode_pos + 3][1], 4)
            self.oregon_put_nib('Temp', ook[self.decode_pos][0],
                                ook[self.decode_pos + 15][1], 16)
            self.oregon_put_nib('Checksum', ook[self.decode_pos][0],
                                ook[self.decode_pos + 7][1], 8)

            self.dump_oregon_hex(ook[0][0], ook[len(ook) - 1][1])

            # L2 decode.
            self.oregon_temp(2)
            self.oregon_channel(1)
            self.oregon_battery(2)
            self.oregon_checksum_v1()

    def oregon_v2(self): # Convert to v3 format - discard odd bits.
        self.decode_pos = 0
        self.ookstring = self.ookstring[1::2]
        for i in range(len(self.decoded)):
            if i % 2 == 1:
                self.decoded[i][0] = self.decoded[i - 1][0] # Re-align start pos.
        self.decoded = self.decoded[1::2] # Discard left hand bits.
        self.oregon_v3() # Decode with v3 decoder.

    def oregon_nibbles(self, ookstring):
        num_nibbles = int(len(ookstring) / 4)
        nibbles = []
        for i in range(num_nibbles):
            nibble = ookstring[4 * i : 4 * i + 4]
            nibble = nibble[::-1] # Reversed from right.
            nibbles.append(nibble)
        return nibbles

    def oregon_put_nib(self, label, start, finish, numbits):
        param = self.ookstring[self.decode_pos:self.decode_pos + numbits]
        param = self.oregon_nibbles(param)
        if 'E' in ''.join(param): # Blank out fields with errors.
            result = ''
        else:
            result = hex(int(''.join(param), 2))[2:]
            if len(result) < numbits / 4: # Reinstate leading zeros.
                result = '0' * (int(numbits / 4) - len(result)) + result
        if label != '':
            label += ': '
        self.put(start, finish, self.out_ann, [1, [label + result, result]])
        if label == '': # No label - use nibble position.
            label = int(self.decode_pos / 4)
        for i in range(len(param)):
            ss = self.decoded[self.decode_pos + (4 * i)][0]
            es = self.decoded[self.decode_pos + (4 * i) + 3][1]
            # Blank out nibbles with errors.
            result = '' if ('E' in param[i]) else hex(int(param[i], 2))[2:]
            # Save nibbles for L2 decoder.
            self.decoded_nibbles.append([ss, es, label, result])
        self.decode_pos += numbits

    def oregon_v3(self):
        self.decode_pos = 0
        self.decoded_nibbles = []
        ook = self.decoded

        if len(self.decoded) >= 32: # Check there are at least 8 nibbles.
            self.oregon_put_nib('SensorID', ook[self.decode_pos][0],
                                ook[self.decode_pos + 16][0], 16)
            self.oregon_put_nib('Ch', ook[self.decode_pos][0],
                                ook[self.decode_pos + 3][1], 4)
            self.oregon_put_nib('RollingCode', ook[self.decode_pos][0],
                                ook[self.decode_pos + 7][1], 8)
            self.oregon_put_nib('Flags1', ook[self.decode_pos][0],
                                ook[self.decode_pos + 3][1], 4)

            rem_nibbles = len(self.ookstring[self.decode_pos:]) // 4
            for i in range(rem_nibbles): # Display and save rest of nibbles.
                self.oregon_put_nib('', ook[self.decode_pos][0],
                                    ook[self.decode_pos + 3][1], 4)
            self.dump_oregon_hex(ook[0][0], ook[len(ook) - 1][1])
            self.oregon_level2() # Level 2 decode.
        else:
            error_message = 'Too short to decode'
            self.put(ook[0][0], ook[-1][1], self.out_ann, [1, [error_message]])

    def oregon_put_l2_param(self, offset, digits, dec_point, pre_label, label):
        nib = self.decoded_nibbles
        result = 0
        out_string = ''.join(str(x[3]) for x in nib[offset:offset + digits])
        if len(out_string) == digits:
            for i in range(dec_point, 0, -1):
                result += int(nib[offset + dec_point - i][3], 16) / pow(10, i)
            for i in range(dec_point, digits):
                result += int(nib[offset + i][3], 16) * pow(10, i - dec_point)
            result = '%g' % (result)
        else:
            result = ''
        es = nib[offset + digits - 1][1]
        if label == '\u2103':
            es = nib[offset + digits][1] # Align temp to include +/- nibble.
        self.put(nib[offset][0], es, self.out_ann,
                [2, [pre_label + result + label, result]])

    def oregon_temp(self, offset):
        nib = self.decoded_nibbles
        if nib[offset + 3][3] != '':
            temp_sign = str(int(nib[offset + 3][3], 16))
            temp_sign = '-' if temp_sign != '0' else '+'
        else:
            temp_sign = '?'
        self.oregon_put_l2_param(offset, 3, 1, temp_sign, '\u2103')

    def oregon_baro(self, offset):
        nib = self.decoded_nibbles
        baro = ''
        if not (nib[offset + 2][3] == '' or nib[offset + 1][3] == ''
           or nib[offset][3] == ''):
            baro = str(int(nib[offset + 1][3] + nib[offset][3], 16) + 856)
        self.put(nib[offset][0], nib[offset + 3][1],
                 self.out_ann, [2, [baro + ' mb', baro]])

    def oregon_wind_dir(self, offset):
        nib = self.decoded_nibbles
        if nib[offset][3] != '':
            w_dir = int(int(nib[offset][3], 16) * 22.5)
            w_compass = dir_table[math.floor((w_dir + 11.25) / 22.5)]
            self.put(nib[offset][0], nib[offset][1], self.out_ann,
                [2, [w_compass + ' (' + str(w_dir) + '\u00b0)', w_compass]])

    def oregon_channel(self, offset):
        nib = self.decoded_nibbles
        channel = ''
        if nib[offset][3] != '':
            ch = int(nib[offset][3], 16)
            if self.ver != 'v3': # May not be true for all v2.1 sensors.
                if ch != 0:
                    bit_pos = 0
                    while ((ch & 1) == 0):
                        bit_pos += 1
                        ch = ch >> 1
                    if self.ver == 'v2.1':
                        bit_pos += 1
                    channel = str(bit_pos)
            elif self.ver == 'v3': # Not sure if this applies to all v3's.
                channel = str(ch)
        if channel != '':
            self.put(nib[offset][0], nib[offset][1],
                     self.out_ann, [2, ['Ch ' + channel, channel]])

    def oregon_battery(self, offset):
        nib = self.decoded_nibbles
        batt = 'OK'
        if nib[offset][3] != '':
            if (int(nib[offset][3], 16) >> 2) & 0x1 == 1:
                batt = 'Low'
            self.put(nib[offset][0], nib[offset][1],
                     self.out_ann, [2, ['Batt ' + batt, batt]])

    def oregon_level2(self): # v2 and v3 level 2 decoder.
        nib = self.decoded_nibbles
        self.sensor_id = (nib[0][3] + nib[1][3] + nib[2][3] + nib[3][3]).upper()
        nl, sensor_type = sensor.get(self.sensor_id, [['Unknown'], 'Unknown'])
        names = ','.join(nl)
        # Allow user to try decoding an unknown sensor.
        if sensor_type == 'Unknown' and self.unknown != 'Unknown':
            sensor_type = self.unknown
        self.put(nib[0][0], nib[3][1], self.out_ann,
            [2, [names + ' - ' + sensor_type, names, nl[0]]])
        self.oregon_channel(4)
        self.oregon_battery(7)
        if sensor_type == 'Rain':
            self.oregon_put_l2_param(8, 4, 2, '', ' in/hr')     # Rain rate
            self.oregon_put_l2_param(12, 6, 3, 'Total ', ' in') # Rain total
            self.oregon_checksum(18)
        if sensor_type == 'Rain1':
            self.oregon_put_l2_param(8, 3, 1, '', ' mm/hr')     # Rain rate
            self.oregon_put_l2_param(11, 5, 1, 'Total ', ' mm') # Rain total
            self.oregon_checksum(18)
        if sensor_type == 'Temp':
            self.oregon_temp(8)
            self.oregon_checksum(12)
        if sensor_type == 'Temp_Hum_Baro':
            self.oregon_temp(8)
            self.oregon_put_l2_param(12, 2, 0, 'Hum ', '%') # Hum
            self.oregon_baro(15)                            # Baro
            self.oregon_checksum(19)
        if sensor_type == 'Temp_Hum_Baro1':
            self.oregon_temp(8)
            self.oregon_put_l2_param(12, 2, 0, 'Hum ', '%') # Hum
            self.oregon_baro(14)                            # Baro
        if sensor_type == 'Temp_Hum':
            self.oregon_temp(8)
            self.oregon_put_l2_param(12, 2, 0, 'Hum ', '%') # Hum
            self.oregon_checksum(15)
        if sensor_type == 'Temp_Hum1':
            self.oregon_temp(8)
            self.oregon_put_l2_param(12, 2, 0, 'Hum ', '%') # Hum
            self.oregon_checksum(14)
        if sensor_type == 'UV':
            self.oregon_put_l2_param(8, 2, 0, '', '') # UV
        if sensor_type == 'UV1':
            self.oregon_put_l2_param(11, 2, 0,'' ,'') # UV
        if sensor_type == 'Wind':
            self.oregon_wind_dir(8)
            self.oregon_put_l2_param(11, 3, 1, 'Gust ', ' m/s')  # Wind gust
            self.oregon_put_l2_param(14, 3, 1, 'Speed ', ' m/s') # Wind speed
            self.oregon_checksum(17)

    def oregon_put_checksum(self, nibbles, checksum):
        nib = self.decoded_nibbles
        result = 'BAD'
        if (nibbles + 1) < len(nib):
            if (nib[nibbles + 1][3] != '' and nib[nibbles][3] != ''
                 and checksum != -1):
                if self.ver != 'v1':
                    if checksum == (int(nib[nibbles + 1][3], 16) * 16 +
                                    int(nib[nibbles][3], 16)):
                        result = 'OK'
                else:
                    if checksum == (int(nib[nibbles][3], 16) * 16 +
                                    int(nib[nibbles + 1][3], 16)):
                        result = 'OK'
            rx_check = (nib[nibbles + 1][3] + nib[nibbles][3]).upper()
            details = '%s Calc %s Rx %s ' % (result, hex(checksum)[2:].upper(),
                                             rx_check)
            self.put(nib[nibbles][0], nib[nibbles + 1][1],
                     self.out_ann, [2, ['Checksum ' + details, result]])

    def oregon_checksum(self, nibbles):
        checksum = 0
        for i in range(nibbles):        # Add reversed nibbles.
            nibble = self.ookstring[i * 4 : i * 4 + 4]
            nibble = nibble[::-1]       # Reversed from right.
            if 'E' in nibble:           # Abort checksum if there are errors.
                checksum = -1
                break
            checksum += int(nibble, 2)
            if checksum > 255:
                checksum -= 255         # Make it roll over at 255.
        chk_ver, comment = sensor_checksum.get(self.sensor_id,
                                               ['Unknown', 'Unknown'])
        if chk_ver != 'Unknown':
            self.ver = chk_ver
        if self.ver == 'v2.1':
            checksum -= 10              # Subtract 10 from v2 checksums.
        self.oregon_put_checksum(nibbles, checksum)

    def oregon_checksum_v1(self):
        nib = self.decoded_nibbles
        checksum = 0
        for i in range(3):              # Add the first three bytes.
            if nib[2 * i][3] == '' or nib[2 * i + 1][3] == '': # Abort if blank.
                checksum = -1
                break
            checksum += ((int(nib[2 * i][3], 16) & 0xF) << 4 |
                         (int(nib[2 * i + 1][3], 16) & 0xF))
            if checksum > 255:
                checksum -= 255         # Make it roll over at 255.
        self.oregon_put_checksum(6, checksum)

    def decode(self, ss, es, data):
        self.decoded = data
        self.oregon()
