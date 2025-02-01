##
## This file is part of the libsigrokdecode project.
##
## Copyright (C) 2014 Angus Gratton <gus@projectgus.com>
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
This PD decodes the ARM SWD (version 1) protocol, as described in the
"ARM Debug Interface v5.2" Architecture Specification.

Not supported:
 * Turnaround periods other than the default 1, as set in DLCR.TURNROUND
   (should be trivial to add)
 * SWD protocol version 2 (multi-drop support, etc.)

Details:
http://infocenter.arm.com/help/index.jsp?topic=/com.arm.doc.ihi0031c/index.html
(Registration required)
'''

from .pd import Decoder
