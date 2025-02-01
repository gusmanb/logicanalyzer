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

#
# Chip specific properties:
#
# - vendor: chip manufacturer
# - model: chip model
# - size: total EEPROM size (in number of bytes)
# - page_size: page size (in number of bytes)
# - page_wraparound: Whether writes wrap-around at page boundaries
# - addr_bytes: number of EEPROM address bytes used
# - addr_pins: number of address pins (A0/A1/A2) on this chip
# - max_speed: max. supported I²C speed (in kHz)
#
chips = {
    # Generic chip (128 bytes, 8 bytes page size)
    'generic': {
        'vendor': '',
        'model': 'Generic',
        'size': 128,
        'page_size': 8,
        'page_wraparound': True,
        'addr_bytes': 1,
        'addr_pins': 3,
        'max_speed': 400,
    },

    # Microchip
    'microchip_24aa65': {
        'vendor': 'Microchip',
        'model': '24AA65',
        'size': 8 * 1024,
        'page_size': 64, # Actually 8, but there are 8 pages of "input cache"
        'page_wraparound': True,
        'addr_bytes': 2,
        'addr_pins': 3,
        'max_speed': 400,
    },
    'microchip_24lc65': {
        'vendor': 'Microchip',
        'model': '24LC65',
        'size': 8 * 1024,
        'page_size': 64, # Actually 8, but there are 8 pages of "input cache"
        'page_wraparound': True,
        'addr_bytes': 2,
        'addr_pins': 3,
        'max_speed': 400,
    },
    'microchip_24c65': {
        'vendor': 'Microchip',
        'model': '24C65',
        'size': 8 * 1024,
        'page_size': 64, # Actually 8, but there are 8 pages of "input cache"
        'page_wraparound': True,
        'addr_bytes': 2,
        'addr_pins': 3,
        'max_speed': 400,
    },
    'microchip_24aa64': {
        'vendor': 'Microchip',
        'model': '24AA64',
        'size': 8 * 1024,
        'page_size': 32,
        'page_wraparound': True,
        'addr_bytes': 2,
        'addr_pins': 3,
        'max_speed': 400, # 100 for VCC < 2.5V
    },
    'microchip_24lc64': {
        'vendor': 'Microchip',
        'model': '24LC64',
        'size': 8 * 1024,
        'page_size': 32,
        'page_wraparound': True,
        'addr_bytes': 2,
        'addr_pins': 3,
        'max_speed': 400,
    },
    'microchip_24aa02uid': {
        'vendor': 'Microchip',
        'model': '24AA02UID',
        'size': 256,
        'page_size': 8,
        'page_wraparound': True,
        'addr_bytes': 1,
        'addr_pins': 0, # Pins A0, A1, A2 not used
        'max_speed': 400,
    },
    'microchip_24aa025uid': {
        'vendor': 'Microchip',
        'model': '24AA025UID',
        'size': 256,
        'page_size': 16,
        'page_wraparound': True,
        'addr_bytes': 1,
        'addr_pins': 3,
        'max_speed': 400,
    },
    'microchip_24aa025uid_sot23': {
        'vendor': 'Microchip',
        'model': '24AA025UID (SOT-23)',
        'size': 256,
        'page_size': 16,
        'page_wraparound': True,
        'addr_bytes': 1,
        'addr_pins': 2, # SOT-23 package: A2 not available
        'max_speed': 400,
    },

    # ON Semiconductor
    'onsemi_cat24c256': {
        'vendor': 'ON Semiconductor',
        'model': 'CAT24C256',
        'size': 32 * 1024,
        'page_size': 64,
        'page_wraparound': True,
        'addr_bytes': 2,
        'addr_pins': 3,
        'max_speed': 1000,
    },
    'onsemi_cat24m01': {
        'vendor': 'ON Semiconductor',
        'model': 'CAT24M01',
        'size': 128 * 1024,
        'page_size': 256,
        'page_wraparound': True,
        'addr_bytes': 2,
        'addr_pins': 2, # Pin A0 not connected
        'max_speed': 1000,
    },

    # Siemens
    'siemens_slx_24c01': {
        'vendor': 'Siemens',
        'model': 'SLx 24C01',
        'size': 128,
        'page_size': 8,
        'page_wraparound': True,
        'addr_bytes': 1,
        'addr_pins': 0, # Pins A0, A1, A2 are not connected (NC)
        'max_speed': 400,
    },
    'siemens_slx_24c02': {
        'vendor': 'Siemens',
        'model': 'SLx 24C02',
        'size': 256,
        'page_size': 8,
        'page_wraparound': True,
        'addr_bytes': 1,
        'addr_pins': 0, # Pins A0, A1, A2 are not connected (NC)
        'max_speed': 400,
    },

    # ST
    'st_m24c01': {
        'vendor': 'ST',
        'model': 'M24C01',
        'size': 128,
        'page_size': 16,
        'page_wraparound': True,
        'addr_bytes': 1,
        'addr_pins': 3, # Called E0, E1, E2 on this chip.
        'max_speed': 400,
    },
    'st_m24c02': {
        'vendor': 'ST',
        'model': 'M24C02',
        'size': 256,
        'page_size': 16,
        'page_wraparound': True,
        'addr_bytes': 1,
        'addr_pins': 3, # Called E0, E1, E2 on this chip.
        'max_speed': 400,
    },
    'st_m24c32': {
        'vendor': 'ST',
        'model': 'M24C32',
        'size': 4 * 1024,
        'page_size': 32,
        'page_wraparound': True,
        'addr_bytes': 2,
        'addr_pins': 3, # Called E0, E1, E2 on this chip.
        'max_speed': 1000,
    },

    # Xicor
    'xicor_x24c02': {
        'vendor': 'Xicor',
        'model': 'X24C02',
        'size': 256,
        'page_size': 4,
        'page_wraparound': True,
        'addr_bytes': 1,
        'addr_pins': 3,
        'max_speed': 100,
    },
}
