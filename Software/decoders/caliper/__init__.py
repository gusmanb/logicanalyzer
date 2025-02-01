##
## This file is part of the libsigrokdecode project.
##
## Copyright (C) 2020 Tomas Mudrunka <harvie@github>
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
This decoder interprets the digital output of cheap generic calipers
(usually made in China), and shows the measured value in millimeters
or inches.

Notice that these devices often communicate on voltage levels below
3.3V and may require additional circuitry to capture the signal.

This decoder does not work for calipers using the Digimatic protocol
(eg. Mitutoyo and similar brands).

For more information see:
http://www.shumatech.com/support/chinese_scales.htm
https://www.instructables.com/id/Reading-Digital-Callipers-with-an-Arduino-USB/
'''

from .pd import Decoder
