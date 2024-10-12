##
## This file is part of the libsigrokdecode project.
##
## Copyright (C) 2012 Uwe Hermann <uwe@hermann-uwe.de>
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
JTAG (Joint Test Action Group), a.k.a. "IEEE 1149.1: Standard Test Access Port
and Boundary-Scan Architecture", is a protocol used for testing, debugging,
and flashing various digital ICs.

Details:
https://en.wikipedia.org/wiki/Joint_Test_Action_Group
http://focus.ti.com/lit/an/ssya002c/ssya002c.pdf
'''

from .pd import Decoder
