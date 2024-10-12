##
## This file is part of the libsigrokdecode project.
##
## Copyright (C) 2018 fenugrec <fenugrec@users.sourceforge.net>
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
This protocol decoder de-multiplexes Intel MCS-48 (8039, 8048, etc.) external
program memory accesses.

This requires 14 channels: 8 for D0-D7 (data and lower 8 bits of address),
4 for A8-A11 (output on port P2), ALE and PSEN.

An optional A12 is supported, which may be an arbitrary I/O pin driven by
software (use case is dumping ROM of an HP 3478A).
'''

from .pd import Decoder
