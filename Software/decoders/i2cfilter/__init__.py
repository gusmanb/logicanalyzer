##
## This file is part of the libsigrokdecode project.
##
## Copyright (C) 2012 Bert Vermeulen <bert@biot.com>
##
## This program is free software; you can redistribute it and/or modify
## it under the terms of the GNU General Public License as published by
## the Free Software Foundation; either version 3 of the License, or
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
This is a generic I²C filtering protocol decoder.

It takes input from the I²C protocol decoder and removes all traffic
except that from/to the specified slave address and/or direction.

It then outputs the filtered data again as OUTPUT_PROTO of type/format 'i2c'
(up the protocol decoder stack). No annotations are output.

The I²C slave address to filter out should be passed in as an option
'address', as an integer. A specific read or write operation can be selected
with the 'direction' option, which should be 'read', 'write', or 'both'.

Both of these are optional; if no options are specified the entire payload
of the I²C session will be output.
'''

from .pd import Decoder
