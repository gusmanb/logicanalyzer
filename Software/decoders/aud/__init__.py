##
## This file is part of the libsigrokdecode project.
##
## Copyright (C) 2016 fenugrec <fenugrec users.sourceforge.net>
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
This protocol decoder decodes the AUD (Advanced User Debugger) interface
of certain Renesas / Hitachi microcontrollers, when set in Branch Trace mode.

AUD has two modes, this PD currently only supports "Branch Trace" mode.

Details:
http://www.renesas.eu/products/mpumcu/superh/sh7050/sh7058/Documentation.jsp
("rej09b0046 - SH7058 Hardware manual")
'''

from .pd import Decoder
