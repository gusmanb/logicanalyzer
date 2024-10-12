##
## This file is part of the libsigrokdecode project.
##
## Copyright (C) 2018 Steve R <steversig@virginmedia.com>
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
OOK decodes On-off keying based remote control protocols.

It is aimed at 433MHz but should also work with other common RC frequencies.
The input can be captured directly from a transmitter (before the modulation
stage) or demodulated by an RF receiver.

Over the air captured traces will be a lot noisier and will probably need the
area of interest to be zoomed onto, then selected with the "Cursors" and the
"Save Selected Range As" feature to be used to extract it from the noise.

There is a limited amount of pre-filtering and garbage removal built into the
decoder which can sometimes extract signals directly from a larger over the air
trace. It depends heavily on your environment.
'''

from .pd import Decoder
