##
## This file is part of the libsigrokdecode project.
##
## Copyright (C) 2012 Uwe Hermann <uwe@hermann-uwe.de>
## Copyright (C) 2017 Kevin Redon <kingkevin@cuvoodoo.info>
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
This protocol decoder handles the 1-Wire link layer.

The 1-Wire protocol enables bidirectional communication over a single wire
(and ground) between a single master and one or multiple slaves. The protocol
is layered:

 - Link layer (reset, presence detection, reading/writing bits)
 - Network layer (skip/search/match device ROM addresses)
 - Transport layer (transport data between 1-Wire master and device)

Sample rate:
A sufficiently high samplerate is required to properly detect all the elements
of the protocol. A lower samplerate can be used if the master does not use
overdrive communication speed. The following minimal values should be used:

 - overdrive available: 2MHz minimum, 5MHz suggested
 - overdrive not available: 400kHz minimum, 1MHz suggested

Channels:
1-Wire requires a single signal, but some master implementations might have a
separate signal used to deliver power to the bus during temperature conversion
as an example.

 - owr (1-Wire signal line)

Options:
1-Wire is an asynchronous protocol with fixed timing values, so the decoder
must know the samplerate.
Two speeds are available: normal and overdrive. The decoder detects when
switching speed, but the user can set which to start decoding with:

 - overdrive (to decode starting with overdrive speed)
'''

from .pd import Decoder
