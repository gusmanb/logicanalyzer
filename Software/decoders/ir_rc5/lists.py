##
## This file is part of the libsigrokdecode project.
##
## Copyright (C) 2014 Uwe Hermann <uwe@hermann-uwe.de>
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

# Systems/addresses (0..31). Items that are not listed are reserved/unknown.
system = {
    0: ['TV receiver 1', 'TV1'],
    1: ['TV receiver 2', 'TV2'],
    2: ['Teletext', 'Txt'],
    3: ['Extension to TV1 and TV2', 'Ext TV1/TV2'],
    4: ['LaserVision player', 'LV'],
    5: ['Video cassette recorder 1', 'VCR1'],
    6: ['Video cassette recorder 2', 'VCR2'],
    7: ['Experimental', 'Exp'],
    8: ['Satellite TV receiver 1', 'Sat1'],
    9: ['Extension to VCR1 and VCR2', 'Ext VCR1/VCR2'],
    10: ['Satellite TV receiver 2', 'Sat2'],
    12: ['Compact disc video player', 'CD-Video'],
    13: ['Camcorder', 'Cam'],
    14: ['Photo on compact disc player', 'CD-Photo'],
    16: ['Audio preamplifier 1', 'Preamp1'],
    17: ['Radio tuner', 'Tuner'],
    18: ['Analog cassette recoder 1', 'Rec1'],
    19: ['Audio preamplifier 2', 'Preamp2'],
    20: ['Compact disc player', 'CD'],
    21: ['Audio stack or record player', 'Combi'],
    22: ['Audio satellite', 'Sat'],
    23: ['Analog cassette recoder 2', 'Rec2'],
    26: ['Compact disc recorder', 'CD-R'],
    29: ['Lighting 1', 'Light1'],
    30: ['Lighting 2', 'Light2'],
    31: ['Telephone', 'Phone'],
}

digits = {
    0: ['0', '0'],
    1: ['1', '1'],
    2: ['2', '2'],
    3: ['3', '3'],
    4: ['4', '4'],
    5: ['5', '5'],
    6: ['6', '6'],
    7: ['7', '7'],
    8: ['8', '8'],
    9: ['9', '9'],
}

# Commands (0..63 for RC-5, and 0..127 for Extended RC-5).
# Items that are not listed are reserved/unknown.
command = {
    'TV': dict(list(digits.items()) + list({
        10: ['-/--', '-/--'],
        11: ['Channel/program', 'Ch/P'],
        12: ['Standby', 'StBy'],
        13: ['Mute', 'M'],
        14: ['Personal preferences', 'PP'],
        15: ['Display', 'Disp'],
        16: ['Volume up', 'Vol+'],
        17: ['Volume down', 'Vol-'],
        18: ['Brightness up', 'Br+'],
        19: ['Brightness down', 'Br-'],
        20: ['Saturation up', 'S+'],
        21: ['Saturation down', 'S-'],
        32: ['Program up', 'P+'],
        33: ['Program down', 'P-'],
    }.items())),
    'VCR': dict(list(digits.items()) + list({
        10: ['-/--', '-/--'],
        12: ['Standby', 'StBy'],
        32: ['Program up', 'P+'],
        33: ['Program down', 'P-'],
        50: ['Fast rewind', 'FRW'],
        52: ['Fast forward', 'FFW'],
        53: ['Play', 'Pl'],
        54: ['Stop', 'St'],
        55: ['Recording', 'Rec'],
    }.items())),
}
