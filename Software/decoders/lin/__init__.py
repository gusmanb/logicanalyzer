##
## This file is part of the libsigrokdecode project.
##
## Copyright (C) 2018 Stephan Thiele <stephan.thiele@mailbox.org>
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
This decoder stacks on top of the 'uart' PD and decodes the LIN
(Local Interconnect Network) protocol.

LIN is layered on top of the UART (async serial) protocol, with 8n1 settings.
Bytes are sent LSB-first.
'''

from .pd import Decoder
