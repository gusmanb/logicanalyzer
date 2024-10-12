##
## This file is part of the libsigrokdecode project.
##
## Copyright (C) 2020 Gerhard Sittig <gerhard.sittig@gmx.net>
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
This protocol decoder interprets the PJDL data link of the PJON protocol.
Bytes and frames get extracted from single wire serial communication
(which often is referred to as "software bitbang" because that's what
the Arduino reference implementation happens to do).
'''

from .pd import Decoder
