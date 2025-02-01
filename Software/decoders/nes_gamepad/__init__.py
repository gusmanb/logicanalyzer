##
## This file is part of the libsigrokdecode project.
##
## Copyright (C) 2019 Stephan Thiele <stephan.thiele@mailbox.org>
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

'''
This decoder stacks on top of the 'spi' PD and decodes the button states
of an NES gamepad.

The SPI decoder needs to be configured as follows:

Clock polarity = 1
Clock phase    = 0
Bit order      = msb-first
Word size      = 8

Chip-select is not used and must not be assigned to any channel.

Hardware setup is as follows:
        ___
   GND |o  \
   CUP |o o| VCC
 OUT 0 |o o| D3
    D1 |o o| D4
       -----
NES Gamepad Connector

VCC   - Power 5V
GND   - Ground
CUP   - Shift register clock (CLK)
OUT 0 - Shift register latch (optional)
D1    - Gamepad data (MOSI)
D3    - Data (unused)
D4    - Data (unused)

Data pins D3 and D4 are not used by the standard gamepad but
by special controllers like the Nintento Zapper light gun.
'''

from .pd import Decoder
