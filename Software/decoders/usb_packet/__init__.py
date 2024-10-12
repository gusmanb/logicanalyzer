##
## This file is part of the libsigrokdecode project.
##
## Copyright (C) 2012 Uwe Hermann <uwe@hermann-uwe.de>
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
This decoder stacks on top of the 'usb_signalling' PD and decodes the USB
(low-speed and full-speed) packet protocol.

Protocol layer (USB spec, chapter 8):

Bit/byte ordering: Bits are sent onto the bus LSB-first. Multibyte fields
are transmitted in little-endian order (i.e., LSB to MSB).

SYNC field: All packets begin with a SYNC field (8 bits).

Packet field format: Packets start with an SOP (Start Of Packet) delimiter
that is part of the SYNC field, and end with an EOP (End Of Packet).

PID: A PID (packet identifier) follows the SYNC field of every packet. A PID
consists of a 4-bit packet type field, and a 4 bit check field.
The check field is the one's complement of the packet type field.

Details:
https://en.wikipedia.org/wiki/USB
http://www.usb.org/developers/docs/
'''

from .pd import Decoder
