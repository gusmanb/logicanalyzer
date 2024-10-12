##
## This file is part of the libsigrokdecode project.
##
## Copyright (C) 2019 Ben Dooks <ben.dooks@codethink.co.uk>
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
TDM Audio is an audio serial bus for moving audio data between devices
(usually on the same board) which can carry one or more channels of data.
'''

from .pd import Decoder
