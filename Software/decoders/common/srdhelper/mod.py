##
## This file is part of the libsigrokdecode project.
##
## Copyright (C) 2012-2020 Uwe Hermann <uwe@hermann-uwe.de>
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

from enum import Enum, IntEnum, unique
from itertools import chain
import re

# Return the specified BCD number (max. 8 bits) as integer.
def bcd2int(b):
    return (b & 0x0f) + ((b >> 4) * 10)

def bin2int(s: str):
    return int('0b' + s, 2)

def bitpack(bits):
    return sum([b << i for i, b in enumerate(bits)])

def bitpack_lsb(bits, idx=None):
    '''Conversion from LSB first bit sequence to integer.'''
    if idx is not None:
        bits = [b[idx] for b in bits]
    return bitpack(bits)

def bitpack_msb(bits, idx=None):
    '''Conversion from MSB first bit sequence to integer.'''
    bits = bits[:]
    if idx is not None:
        bits = [b[idx] for b in bits]
    bits.reverse()
    return bitpack(bits)

def bitunpack(num, minbits=0):
    res = []
    while num or minbits > 0:
        res.append(num & 1)
        num >>= 1
        minbits -= 1
    return tuple(res)

@unique
class SrdStrEnum(Enum):
    @classmethod
    def from_list(cls, name, l):
        # Keys are limited/converted to [A-Z0-9_], values can be any string.
        items = [(re.sub('[^A-Z0-9_]', '_', l[i]), l[i]) for i in range(len(l))]
        return cls(name, items)

    @classmethod
    def from_str(cls, name, s):
        return cls.from_list(name, s.split())

@unique
class SrdIntEnum(IntEnum):
    @classmethod
    def _prefix(cls, p):
        return tuple([a.value for a in cls if a.name.startswith(p)])

    @classmethod
    def prefixes(cls, prefix_list):
        if isinstance(prefix_list, str):
            prefix_list = prefix_list.split()
        return tuple(chain(*[cls._prefix(p) for p in prefix_list]))

    @classmethod
    def _suffix(cls, s):
        return tuple([a.value for a in cls if a.name.endswith(s)])

    @classmethod
    def suffixes(cls, suffix_list):
        if isinstance(suffix_list, str):
            suffix_list = suffix_list.split()
        return tuple(chain(*[cls._suffix(s) for s in suffix_list]))

    @classmethod
    def from_list(cls, name, l):
        # Manually construct (Python 3.4 is missing the 'start' argument).
        # Python defaults to start=1, but we want start=0.
        return cls(name, [(l[i], i) for i in range(len(l))])

    @classmethod
    def from_str(cls, name, s):
        return cls.from_list(name, s.split())
