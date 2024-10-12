##
## This file is part of the libsigrokdecode project.
##
## Copyright (C) 2017 Gerhard Sittig <gerhard.sittig@gmx.net>
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
AC'97 (Audio Codec '97) is a protocol for audio and modem I/O functionality
in mainstream PC systems.

AC'97 communicates full duplex data (SDATA_IN, SDATA_OUT), where bits
are clocked by the BIT_CLK and frames are signalled by the SYNC signals.
A low active RESET# line completes the set of signals.

Frames repeat at a nominal frequency of 48kHz, and consist of 256 bits
each. One 16bit slot contains management information, twelve 20bit slots
follow which carry data for three management and nine audio/modem channels.
Optionally two slots of one frame can get combined for higher resolution
on fewer channels, or double data rate.

Details:
http://download.intel.com/support/motherboards/desktop/sb/ac97_r23.pdf
'''

from .pd import Decoder
