##
## This file is part of the libsigrokdecode project.
##
## Copyright (C) 2018 Mike Jagdis <mjagdis@eris-associates.co.uk>
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
SWIM is a single wire interface for STM8 series 8-bit microcontrollers
that allows non-intrusive read/wite access to be performed on-the-fly
to the memory and registers of the MCU for debug and flashing purposes.

See the STMicroelectronics document UM0470 for details.
'''

from .pd import Decoder
