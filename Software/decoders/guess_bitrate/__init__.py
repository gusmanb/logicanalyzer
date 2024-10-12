##
## This file is part of the libsigrokdecode project.
##
## Copyright (C) 2013 Uwe Hermann <uwe@hermann-uwe.de>
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
This protocol decoder tries to guess the bitrate / baudrate of the
communication on the specified channel.

Typically this will be used to guess / detect the baudrate used in a UART
communication snippet, but it could also be used to guess bitrates of certain
other protocols or buses.

It should be noted that this is nothing more than a simple guess / heuristic,
and that there are various cases in practice where the detection of the
bitrate or baudrate will not necessarily have the expected result.

The precision of the estimated bitrate / baudrate will also depend on the
samplerate used to sample the respective channel. For good results it is
recommended to use a logic analyzer samplerate that is much higher than
the expected bitrate/baudrate that might be used on the channel.

The last annotation emitted by the decoder will be the best bitrate guess.
'''

from .pd import Decoder
