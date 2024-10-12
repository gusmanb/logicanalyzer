##
## This file is part of the libsigrokdecode project.
##
## Copyright (C) 2019 Gerhard Sittig <gerhard.sittig@gmx.net>
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
This protocol decoder can decode the GPIB (IEEE-488) protocol. Both variants
of (up to) 16 parallel lines as well as serial communication (IEC bus) are
supported in this implementation.
'''

from .pd import Decoder
