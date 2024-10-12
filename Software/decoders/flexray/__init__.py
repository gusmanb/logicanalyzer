##
## This file is part of the libsigrokdecode project.
##
## Copyright (C) 2019 Stephan Thiele <stephan.thiele@mailbox.org>
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
FlexRay is a fast, deterministic and fault-tolerant fieldbus system
which is used in cars in high security related areas like X-by-Wire.

It is the result of the FlexRay consortium which consisted of BMW,
Daimler, Motorola (today Freescale) and Philips, with the goal of
working out a common standard automotive bus system.

This decoder assumes that at least one channel of a logic level RX line
of a transceiver is sampled (e.g. NXP TJA1080).
'''

from .pd import Decoder
