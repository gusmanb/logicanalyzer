##
## This file is part of the libsigrokdecode project.
##
## Copyright (C) 2017 Joel Holdsworth <joel@airwebreathe.org.uk>
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
by the Analog Devices ADF4350 and ADF4351 RF synthesizer chips.

Details:
http://www.analog.com/media/en/technical-documentation/data-sheets/ADF4350.pdf
http://www.analog.com/media/en/technical-documentation/data-sheets/ADF4351.pdf
'''

from .pd import Decoder
