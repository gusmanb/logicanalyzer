##
## This file is part of the libsigrokdecode project.
##
## Copyright (C) 2012 Joel Holdsworth <uwe@hermann-uwe.de>
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
I²S (Integrated Interchip Sound) is a serial bus for connecting digital
audio devices (usually on the same device/board).

Details:
http://www.nxp.com/acrobat_download/various/I2SBUS.pdf
http://en.wikipedia.org/wiki/I2s
'''

from .pd import Decoder
