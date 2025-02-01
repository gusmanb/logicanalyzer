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
The Serial Inter-Processor Interface (SIPI) is a higher-level protocol that runs
over the LFAST physical interface. Together, they form the NXP Zipwire interface.

The SIPI interface is also provided by Infineon as HSST, using HSCT for transport.

For details see https://www.nxp.com/docs/en/application-note/AN5134.pdf and
https://hitex.co.uk/fileadmin/uk-files/downloads/ShieldBuddy/tc27xD_um_v2.2.pdf
'''

from .pd import Decoder
