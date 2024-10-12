##
## This file is part of the libsigrokdecode project.
##
## Copyright (C) 2014 Sebastien Bourdelin <sebastien.bourdelin@savoirfairelinux.com>
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
This protocol decoder retrieves the timing jitter between two digital signals.

It allows to define a clock source channel and a resulting signal channel.

Each time a significant edge is detected in the clock source, we calculate the
elapsed time before the resulting signal answers and report the timing jitter.
'''

from .pd import Decoder
