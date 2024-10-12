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
This decoder stacks on top of the 'onewire_link' PD and decodes the
1-Wire protocol (network layer).

The 1-Wire protocol enables bidirectional communication over a single wire
(and ground) between a single master and one or multiple slaves. The protocol
is layered:

 - Link layer (reset, presence detection, reading/writing bits)
 - Network layer (skip/search/match device ROM addresses)
 - Transport layer (transport data between 1-Wire master and device)

Network layer:

The following link layer annotations are shown:

 - RESET/PRESENCE True/False
   The event is marked from the signal negative edge to the end of the reset
   high period. It is also reported if there are any devices attached to the
   bus.

The following network layer annotations are shown:

 - ROM command <val> <name>
   The requested ROM command is displayed as an 8bit hex value and by name.
 - ROM <val>
   The 64bit value of the addressed device is displayed:
   Family code (1 byte) + serial number (6 bytes) + CRC (1 byte)
 - Data <val>
   Data intended for the transport layer is displayed as an 8bit hex value.

TODO:
 - Add CRC checks, to see if there were communication errors on the wire.
 - Add reporting original/complement address values from the search algorithm.
'''

from .pd import Decoder
