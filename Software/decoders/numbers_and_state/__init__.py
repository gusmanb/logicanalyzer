##
## This file is part of the libsigrokdecode project.
##
## Copyright (C) 2019 Comlab AG
## Copyright (C) 2020 Gerhard Sittig <gerhard.sittig@gmx.net>
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
This protocol decoder takes a set of logic input signals, and interprets
their bit pattern according to user specifications as different kinds of
numbers, or an enumeration of e.g. machine states.

Supported formats are: signed and unsigned integers, fixed point numbers,
IEEE754 floating point numbers, and number to text mapping controlled by
external data files. (Support for half precision floats depends on the
Python runtime, and may not universally be available.)

User provided text mapping files can either use the JSON format:
  {"one": 1, "two": 2, "four": 4}
or the Python programming language:
  enumtext = { 1: "one", 2: "two", 3: "three", }

In addition to all enum values on one row (sequential presentation of
the data), a limited number of enum values also are shown in tabular
presentation, which can help visualize state machines or task switches.
'''

from .pd import Decoder
