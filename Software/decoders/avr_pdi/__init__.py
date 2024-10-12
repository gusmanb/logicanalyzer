##
## This file is part of the libsigrokdecode project.
##
## Copyright (C) 2016 Gerhard Sittig <gerhard.sittig@gmx.net>
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
PDI (Program and Debug Interface) is an Atmel proprietary interface for
external programming and on-chip debugging of the device.

See the Atmel Application Note AVR1612 "PDI programming driver" and the
"Program and Debug Interface" section in the Xmega A manual for details.

The protocol uses two pins: the RESET pin and one dedicated DATA pin.
The RESET pin provides a clock, the DATA pin communicates serial frames
with a start bit, eight data bits, an even parity bit, and two stop bits.
Data communication is bidirectional and half duplex, the device will
provide response data after reception of a respective request.

Protocol frames communicate opcodes and their arguments, which provides
random and sequential access to the device's address space. By accessing
the registers of internal peripherals, especially the NVM controller,
it's possible to identify the device, read from and write to several
kinds of memory (signature rows, fuses and lock bits, internal flash and
EEPROM, memory mapped peripherals), and to control execution of software
on the device.
'''

from .pd import Decoder
