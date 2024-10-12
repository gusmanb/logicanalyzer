##
## This file is part of the libsigrokdecode project.
##
## Copyright (C) 2016 Bert Vermeulen <bert@biot.com>
##
## This program is free software; you can redistribute it and/or modify
## it under the terms of the GNU General Public License as published by
## the Free Software Foundation; either version 3 of the License, or
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

# This module contains definitions for use by pluggable network adapters,
# such as SFP, XFP etc.

MODULE_ID = {
    0x01: 'GBIC',
    0x02: 'Integrated module/connector',
    0x03: 'SFP',
    0x04: '300-pin XBI',
    0x05: 'XENPAK',
    0x06: 'XFP',
    0x07: 'XFF',
    0x08: 'XFP-E',
    0x09: 'XPAK',
    0x0a: 'X2',
}

ALARM_THRESHOLDS = {
    0:  'Temp high alarm',
    2:  'Temp low alarm',
    4:  'Temp high warning',
    6:  'Temp low warning',
    16: 'Bias high alarm',
    18: 'Bias low alarm',
    20: 'Bias high warning',
    22: 'Bias low warning',
    24: 'TX power high alarm',
    26: 'TX power low alarm',
    28: 'TX power high warning',
    30: 'TX power low warning',
    32: 'RX power high alarm',
    34: 'RX power low alarm',
    36: 'RX power high warning',
    38: 'RX power low warning',
    40: 'AUX 1 high alarm',
    42: 'AUX 1 low alarm',
    44: 'AUX 1 high warning',
    46: 'AUX 1 low warning',
    48: 'AUX 2 high alarm',
    50: 'AUX 2 low alarm',
    52: 'AUX 2 high warning',
    54: 'AUX 2 low warning',
}

AD_READOUTS = {
    0:  'Module temperature',
    4:  'TX bias current',
    6:  'Measured TX output power',
    8:  'Measured RX input power',
    10: 'AUX 1 measurement',
    12: 'AUX 2 measurement',
}

GCS_BITS = [
    'TX disable',
    'Soft TX disable',
    'MOD_NR',
    'P_Down',
    'Soft P_Down',
    'Interrupt',
    'RX_LOS',
    'Data_Not_Ready',
    'TX_NR',
    'TX_Fault',
    'TX_CDR not locked',
    'RX_NR',
    'RX_CDR not locked',
]

CONNECTOR = {
    0x01:   'SC',
    0x02:   'Fibre Channel style 1 copper',
    0x03:   'Fibre Channel style 2 copper',
    0x04:   'BNC/TNC',
    0x05:   'Fibre Channel coax',
    0x06:   'FiberJack',
    0x07:   'LC',
    0x08:   'MT-RJ',
    0x09:   'MU',
    0x0a:   'SG',
    0x0b:   'Optical pigtail',
    0x20:   'HSSDC II',
    0x21:   'Copper pigtail',
}

TRANSCEIVER = [
    # 10GB Ethernet
    ['10GBASE-SR', '10GBASE-LR', '10GBASE-ER', '10GBASE-LRM', '10GBASE-SW',
        '10GBASE-LW',   '10GBASE-EW'],
    # 10GB Fibre Channel
    ['1200-MX-SN-I', '1200-SM-LL-L', 'Extended Reach 1550 nm',
        'Intermediate reach 1300 nm FP'],
    # 10GB Copper
    [],
    # 10GB low speed
    ['1000BASE-SX / 1xFC MMF', '1000BASE-LX / 1xFC SMF', '2xFC MMF',
        '2xFC SMF', 'OC48-SR', 'OC48-IR', 'OC48-LR'],
    # 10GB SONET/SDH interconnect
    ['I-64.1r', 'I-64.1', 'I-64.2r', 'I-64.2', 'I-64.3', 'I-64.5'],
    # 10GB SONET/SDH short haul
    ['S-64.1', 'S-64.2a', 'S-64.2b', 'S-64.3a', 'S-64.3b', 'S-64.5a', 'S-64.5b'],
    # 10GB SONET/SDH long haul
    ['L-64.1', 'L-64.2a', 'L-64.2b', 'L-64.2c', 'L-64.3', 'G.959.1 P1L1-2D2'],
    # 10GB SONET/SDH very long haul
    ['V-64.2a', 'V-64.2b', 'V-64.3'],
]

SERIAL_ENCODING = [
    '64B/66B',
    '8B/10B',
    'SONET scrambled',
    'NRZ',
    'RZ',
]

XMIT_TECH = [
    '850 nm VCSEL',
    '1310 nm VCSEL',
    '1550 nm VCSEL',
    '1310 nm FP',
    '1310 nm DFB',
    '1550 nm DFB',
    '1310 nm EML'
    '1550 nm EML'
    'copper',
]

CDR = [
    '9.95Gb/s',
    '10.3Gb/s',
    '10.5Gb/s',
    '10.7Gb/s',
    '11.1Gb/s',
    '(unknown)',
    'lineside loopback mode',
    'XFI loopback mode',
]

DEVICE_TECH = [
    ['no wavelength control', 'sctive wavelength control'],
    ['uncooled transmitter device', 'cooled transmitter'],
    ['PIN detector', 'APD detector'],
    ['transmitter not tunable', 'transmitter tunable'],
]

ENHANCED_OPTS = [
    'VPS',
    'soft TX_DISABLE',
    'soft P_Down',
    'VPS LV regulator mode',
    'VPS bypassed regulator mode',
    'active FEC control',
    'wavelength tunability',
    'CMU',
]

AUX_TYPES = [
    'not implemented',
    'APD bias voltage',
    '(unknown)',
    'TEC current',
    'laser temperature',
    'laser wavelength',
    '5V supply voltage',
    '3.3V supply voltage',
    '1.8V supply voltage',
    '-5.2V supply voltage',
    '5V supply current',
    '(unknown)',
    '(unknown)',
    '3.3V supply current',
    '1.8V supply current',
    '-5.2V supply current',
]
