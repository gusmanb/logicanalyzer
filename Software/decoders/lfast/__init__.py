##
## This file is part of the libsigrokdecode project.
##
## Copyright (C) 2020 Soeren Apel <soeren@apelpie.net>
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
LFAST is a physical communication interface used mainly by the NXP Zipwire
interface. It's a framed asynchronous serial interface using differential
TX/RX pairs, capable of data rates of up to 320 MBit/s.

This interface is also provided by Infineon as HSCT.

As with most differential signals, it's sufficient to measure TXP or RXP, no
need for a differential probe. The REFCLK used by the hardware isn't needed by
this protocol decoder either.

For details see https://www.nxp.com/docs/en/application-note/AN5134.pdf and
https://hitex.co.uk/fileadmin/uk-files/downloads/ShieldBuddy/tc27xD_um_v2.2.pdf
'''

from .pd import Decoder
