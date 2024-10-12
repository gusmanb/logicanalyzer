##
## This file is part of the libsigrokdecode project.
##
## Copyright (C) 2013 Bert Vermeulen <bert@biot.com>
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
This PD decodes the XFP I²C management interface structures/protocol.

XFP modules include an I²C interface, used to monitor and control various
aspects of the module. The specification defines an I²C slave at address
0x50 (0xa0) which returns 128 bytes of a standard structure ("lower memory"),
and, after setting a table number in lower memory, a set of 256 "higher
memory" tables, which can be mapped to different subdevices on the XFP.

Only one table is defined in the specification: table 0x01, the default on
module startup. Other table are either reserved for future expansion, or
available for vendor-specific extensions. This decoder supports both lower
memory and table 0x01.

Details:
ftp://ftp.seagate.com/sff/INF-8077.PDF (XFP specification)
'''

from .pd import Decoder
