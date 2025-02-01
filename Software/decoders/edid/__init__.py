##
## This file is part of the libsigrokdecode project.
##
## Copyright (C) 2012 Bert Vermeulen <bert@biot.com>
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
Extended Display Identification Data (EDID) 1.3 structure decoder.

The three-character vendor ID as specified in the EDID standard refers to
a Plug and Play ID (PNPID). The list of PNPID assignments is done by Microsoft.

The 'pnpids.txt' file included with this protocol decoder is derived from
the list of assignments downloadable from that page. It was retrieved in
January 2012.

Details:
https://en.wikipedia.org/wiki/Extended_display_identification_data
http://msdn.microsoft.com/en-us/windows/hardware/gg463195
'''

from .pd import Decoder
