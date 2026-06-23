##
## This file is part of the libsigrokdecode project.
##
## Copyright (C) 2024 DShot decoder contributor
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
DShot protocol decoder.

DShot is a digital ESC protocol used in drones/RC, encoding throttle and
control commands as duty-cycle-modulated bits sent at fixed rates
(150/300/600/1200 kbit/s). This decoder handles the FC→ESC command frames.

Details:
https://betaflight.com/docs/wiki/guides/current/Dshot
'''

from .pd import Decoder
