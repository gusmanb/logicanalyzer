##
## This file is part of the libsigrokdecode project.
##
## Copyright (C) 2022 Gerhard Sittig <gerhard.sittig@gmx.net>
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
SBUS by Futaba, a hobby remote control protocol on top of UART.
Sometimes referred to as "Serial BUS" or S-BUS.

UART communication typically runs at 100kbps with 8e2 frame format and
inverted signals (high voltage level is logic low).

SBUS messages take 3ms to transfer, and typically repeat in intervals
of 7ms or 14ms. An SBUS message consists of 25 UART bytes, and carries
16 proportional channels with 11 bits each, and 2 digital channels
(boolean, 1 bit), and flags which represent current communication state.
Proportional channel values typically are in the 192..1792 range, but
individual implementations may differ.
'''

from .pd import Decoder
