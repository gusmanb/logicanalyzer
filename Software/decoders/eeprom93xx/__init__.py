##
## This file is part of the libsigrokdecode project.
##
## Copyright (C) 2017 Kevin Redon <kingkevin@cuvoodoo.info>
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
This decoder stacks on top of the 'microwire' PD and decodes the 93xx EEPROM
specific instructions.

The implemented instructions come from the STMicroelectronics M93Cx6 EEPROM
datasheet. They are compatible with the Atmel AT93Cxx EEPROM with slightly
different names.

Warning: Other EEPROMs using Microwire might have different operation codes
and instructions.
'''

from .pd import Decoder
