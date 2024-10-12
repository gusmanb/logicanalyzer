##
## This file is part of the libsigrokdecode project.
##
## Copyright (C) 2015-2020 Uwe Hermann <uwe@hermann-uwe.de>
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

from collections import OrderedDict

# OrderedDict which maps command IDs to their names and descriptions.
# Please keep this sorted by command ID.
cmds = OrderedDict([
    (0x01, ('WRSR', 'Write status register')),
    (0x02, ('PP', 'Page program')),
    (0x03, ('READ', 'Read data')),
    (0x04, ('WRDI', 'Write disable')),
    (0x05, ('RDSR', 'Read status register')),
    (0x06, ('WREN', 'Write enable')),
    (0x0b, ('FAST/READ', 'Fast read data')),
    (0x20, ('SE', 'Sector erase')),
    (0x2b, ('RDSCUR', 'Read security register')),
    (0x2f, ('WRSCUR', 'Write security register')),
    (0x35, ('RDSR2', 'Read status register 2')),
    (0x60, ('CE', 'Chip erase')),
    (0x70, ('ESRY', 'Enable SO to output RY/BY#')),
    (0x80, ('DSRY', 'Disable SO to output RY/BY#')),
    (0x82, ('WRITE1', 'Main memory page program through buffer 1 with built-in erase')),
    (0x85, ('WRITE2', 'Main memory page program through buffer 2 with built-in erase')),
    (0x90, ('REMS', 'Read electronic manufacturer & device ID')),
    (0x9f, ('RDID', 'Read identification')),
    (0xab, ('RDP/RES', 'Release from deep powerdown / Read electronic ID')),
    (0xad, ('CP', 'Continuously program mode')),
    (0xb1, ('ENSO', 'Enter secured OTP')),
    (0xb9, ('DP', 'Deep power down')),
    (0xbb, ('2READ', '2x I/O read')), # a.k.a. "Fast read dual I/O".
    (0xc1, ('EXSO', 'Exit secured OTP')),
    (0xc7, ('CE2', 'Chip erase 2')), # Alternative command ID
    (0xd7, ('STATUS', 'Status register read')),
    (0xd8, ('BE', 'Block erase')),
    (0xef, ('REMS2', 'Read ID for 2x I/O mode')),
])

device_name = {
    'adesto': {
        0x00: 'AT45Dxxx family, standard series',
    },
    'fidelix': {
        0x15: 'FM25Q32',
    },
    'macronix': {
        0x13: 'MX25L8006',
        0x14: 'MX25L1605D',
        0x15: 'MX25L3205D',
        0x16: 'MX25L6405D',
    },
    'winbond': {
        0x13: 'W25Q80DV',
    },
}

chips = {
    # Adesto
    'adesto_at45db161e': {
        'vendor': 'Adesto',
        'model': 'AT45DB161E',
        'res_id': None, # The chip doesn't emit an ID here.
        'rems_id': None, # Not supported by the chip.
        'rems2_id': None, # Not supported by the chip.
        'rdid_id': 0x1f26000100, # RDID and 2 extra "EDI" bytes.
        'page_size': 528, # Configurable, could also be 512 bytes.
        'sector_size': 128 * 1024,
        'block_size': 4 * 1024,
    },
    # Atmel
    'atmel_at25128': {
        'vendor': 'Atmel',
        'model': 'AT25128',
        'res_id': None, # Not supported by the chip.
        'rems_id': None, # Not supported by the chip.
        'rems2_id': None, # Not supported by the chip.
        'rdid_id': None, # Not supported by the chip.
        'page_size': 64,
        'sector_size': None, # The chip doesn't have sectors.
        'block_size': None, # The chip doesn't have blocks.
    },
    'atmel_at25256': {
        'vendor': 'Atmel',
        'model': 'AT25256',
        'res_id': None, # Not supported by the chip.
        'rems_id': None, # Not supported by the chip.
        'rems2_id': None, # Not supported by the chip.
        'rdid_id': None, # Not supported by the chip.
        'page_size': 64,
        'sector_size': None, # The chip doesn't have sectors.
        'block_size': None, # The chip doesn't have blocks.
    },
    # FIDELIX
    'fidelix_fm25q32': {
        'vendor': 'FIDELIX',
        'model': 'FM25Q32',
        'res_id': 0x15,
        'rems_id': 0xa115,
        'rems2_id': 0xa115,
        'rdid_id': 0xa14016,
        'page_size': 256,
        'sector_size': 4 * 1024,
        'block_size': 64 * 1024,
    },
    # Macronix
    'macronix_mx25l1605d': {
        'vendor': 'Macronix',
        'model': 'MX25L1605D',
        'res_id': 0x14,
        'rems_id': 0xc214,
        'rems2_id': 0xc214,
        'rdid_id': 0xc22015,
        'page_size': 256,
        'sector_size': 4 * 1024,
        'block_size': 64 * 1024,
    },
    'macronix_mx25l3205d': {
        'vendor': 'Macronix',
        'model': 'MX25L3205D',
        'res_id': 0x15,
        'rems_id': 0xc215,
        'rems2_id': 0xc215,
        'rdid_id': 0xc22016,
        'page_size': 256,
        'sector_size': 4 * 1024,
        'block_size': 64 * 1024,
    },
    'macronix_mx25l6405d': {
        'vendor': 'Macronix',
        'model': 'MX25L6405D',
        'res_id': 0x16,
        'rems_id': 0xc216,
        'rems2_id': 0xc216,
        'rdid_id': 0xc22017,
        'page_size': 256,
        'sector_size': 4 * 1024,
        'block_size': 64 * 1024,
    },
    'macronix_mx25l8006': {
        'vendor': 'Macronix',
        'model': 'MX25L8006',
        'res_id': 0x13,
        'rems_id': 0xc213,
        'rems2_id': 0xc213,
        'rdid_id': 0xc22013,
        'page_size': 256,
        'sector_size': 4 * 1024,
        'block_size': 64 * 1024,
    },
    # Winbond
    'winbond_w25q80dv': {
        'vendor': 'Winbond',
        'model': 'W25Q80DV',
        'res_id': 0x13,
        'rems_id': 0xef13,
        'rems2_id': None, # Not supported by the chip.
        'rdid_id': 0xef4014,
        'page_size': 256,
        'sector_size': 4 * 1024,
        'block_size': 64 * 1024, # Configurable, could also be 32 * 1024 bytes.
    },
}
