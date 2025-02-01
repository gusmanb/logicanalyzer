##
## This file is part of the libsigrokdecode project.
##
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
Microwire is a 3-wire half-duplex synchronous serial communication protocol.

Originally from National Semiconductor, it is often used in EEPROM chips with
device specific commands on top of the bit stream.

Channels:

 - CS: chip select, active high
 - SK: clock line, for the synchronous communication (idle low)
 - SI: slave data input, output by the master and parsed by the selected slave
       on rising edge of clock line (idle low)
 - SO: slave data output, output by the selected slave and changed on rising
       edge of clock line, or goes from low to high when ready during status
       check (idle high impedance)

The channel names might vary from chip to chip but the underlying function is
the same.
'''

from .pd import Decoder
