##
## This file is part of the libsigrokdecode project.
##
## Copyright (C) 2014 Jens Steinhauser <jens.steinhauser@gmail.com>
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
This decoder stacks on top of the 'spi' PD and decodes the protocol spoken
by the Nordic Semiconductor nRF24L01 and nRF24L01+ 2.4GHz transceiver chips.

Details:
http://www.nordicsemi.com/eng/Products/2.4GHz-RF/nRF24L01
http://www.nordicsemi.com/eng/Products/2.4GHz-RF/nRF24L01P
'''

from .pd import Decoder
