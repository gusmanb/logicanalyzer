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
UART (Universal Asynchronous Receiver Transmitter) is a simple serial
communication protocol which allows two devices to talk to each other.

This decoder should work on all "UART-like" async protocols with one
start bit (0), 5-9 databits, an (optional) parity bit, and one or more
stop bits (1), in this order.

It can be run on one signal line (RX or TX) only, or on two lines (RX + TX).

There are various standards for the physical layer specification of the
signals, including RS232, (TTL) UART, RS485, and others. However, the logic
level of the respective pins is only relevant when acquiring the data via
a logic analyzer (you have to select the correct logic analyzer and/or
the correct place where to probe). Once the data is in digital form and
matches the "UART" description above, this protocol decoder can work with
it though, no matter whether the source was on TTL UART levels, or RS232,
or others.
'''

from .pd import Decoder
