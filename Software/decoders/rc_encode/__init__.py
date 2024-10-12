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
This PD decodes the remote control protocol which is frequently used
within key fobs and power socket remotes.

They contain encoding chips like the PT2262 which converts the button
pressed and address settings into a series of pulses which is then
transmitted over whatever frequency and modulation that the designer
chooses. These devices operate at a number of frequencies including 433MHz.

This PD should also decode the HX2262 and SC5262 which are equivalents, as
well as the 2272 variants of these ICs. Support for the EV1527, RT1527, FP1527
and HS1527 is also present.

The decoder can additionaly decoding the Maplin L95AR remote control and will
turn the received signal into which button was pressed and what the address
code DIP switches are set to.
Please contact the sigrok team if you want decoding for further remote
controls to be added.
'''

from .pd import Decoder
