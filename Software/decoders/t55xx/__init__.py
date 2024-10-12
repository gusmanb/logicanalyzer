##
## This file is part of the libsigrokdecode project.
##
## Copyright (C) 2015 Benjamin Larsson <benjamin@southpole.se>
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
T55xx is a 100-150kHz RFID protocol according to the Atmel e555x
downlink/write protocol (pulse interval coding).
'''

from .pd import Decoder
