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
This protocol decoder can decode synchronous parallel buses with various
data bits/channels counts, an (optional) clock line, and an (optional)
select/enable/reset line.

Data bits are taken from the decoder's lowest connected input pins. The
input signal's data lines count need not span the full amount of the
decoder's maximum supported data lines count. Not connected data lines
are assumed to be low.

Example use cases are: Connect D3/D2/D1/D0 (and CLK) to a 4-bit bus.
Connect D7 and D6 to inspect the two most significant bits of an 8-bit
bus (and have 8-bit values shown instead of just 2-bit values).

When provided, the specified clock edge determines when data lines get
sampled. Without a clock spec, each transition on any of the data lines
will be shown, which can become busy/noisy depending on the input data.

Another signal optionally can control the period of time within which
the data lines' bit pattern gets interpreted. Typical use cases would be
reset, or select, or enable signals that are related to the bus' data
communication. This optional signal can also improve synchronization to
wider payload data which spans several bus cycles (multiplexing).
'''

from .pd import Decoder
