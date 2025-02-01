##
## This file is part of the libsigrokdecode project.
##
## Copyright (C) 2020 Tom Flanagan <knio@zkpq.ca>
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

NUMBERS = {
    0x00: '1',
    0x01: '2',
    0x02: '3',
    0x03: '4',
    0x04: '5',
    0x05: '6',
    0x06: '7',
    0x07: '8',
    0x08: '9',
    0x09: '0/10',
}

ADDRESSES = {
    # TV
    (0x01, None): (['TV: ', 'TV:'], {
        0x15: 'Power',
        0x25: 'Input',

        0x33: 'Right',
        0x34: 'Left',
        0x3A: 'Display',

        0x60: 'Home',
        0x65: 'Enter',

        0x74: 'Up',
        0x75: 'Down',

    }),

    # Video
    (0x0B, None): (['Video: ', 'V:'], {
        0x18: 'Stop',
        0x19: 'Pause',
        0x1A: 'Play',
        0x1B: 'Rewind',
        0x1C: 'Fast Forward',

        0x42: 'Up',
        0x43: 'Down',
        0x4D: 'Home',

        0x51: 'Enter',
        0x5A: 'Display',

        0x61: 'Right',
        0x62: 'Left',
    }),

    # BR Input select
    (0x10, 0x28): (['BlueRay: ', 'BR:'], {
        0x16: 'BlueRay',
    }),

    # Amp, Game, Sat, Tuner, USB
    (0x10, 0x08): (['Playback: ', 'PB:'], {
        0x2A: 'Shuffle',
        0x2C: 'Repeat',
        0x2E: 'Folder Down',
        0x2F: 'Folder Up',

        0x30: 'Previous',
        0x31: 'Next',
        0x32: 'Play',
        0x33: 'Rewind',
        0x34: 'Fast Forward',
        0x38: 'Stop',
        0x39: 'Pause',

        0x73: 'Options',
        0x7D: 'Return',
    }),

    # CD
    (0x11, None): (['CD: ', 'CD:'], {
        0x28: 'Display',

        0x30: 'Previous',
        0x31: 'Next',
        0x32: 'Play',
        0x33: 'Rewind',
        0x34: 'Fast Forward',
        0x38: 'Stop',
        0x39: 'Pause',
    }),

    # BD
    (0x1A, 0xE2): (['BlueRay: ', 'BD:'], {
        0x18: 'Stop',
        0x19: 'Pause',
        0x1A: 'Play',
        0x1B: 'Rewind',
        0x1C: 'Fast Forward',

        0x29: 'Menu',
        0x2C: 'Top Menu',

        0x39: 'Up',
        0x3A: 'Down',
        0x3B: 'Left',
        0x3C: 'Right',
        0x3D: 'Enter',
        0x3F: 'Options',

        0x41: 'Display',
        0x42: 'Home',
        0x43: 'Return',

        0x56: 'Next',
        0x57: 'Previous',
    }),

    # DVD
    (0x1A, 0x49): (['DVD: ', 'DVD:'], {
        0x0B: 'Enter',
        0x0E: 'Return',
        0x17: 'Options',

        0x1A: 'Top Menu',
        0x1B: 'Menu',

        0x30: 'Previous',
        0x31: 'Next',
        0x32: 'Play',
        0x33: 'Rewind',
        0x34: 'Fast Forward',
        0x38: 'Stop',
        0x39: 'Pause',

        0x54: 'Display',

        0x7B: 'Left',
        0x7C: 'Right',
        0x79: 'Up',
        0x7A: 'Down',
    }),

    # Amp, Game, Sat, Tuner, USB modes
    (0x30, None): (['Keypad: ', 'KP:'], {
        0x0C: 'Enter',

        0x12: 'Volume Up',
        0x13: 'Volume Down',
        0x14: 'Mute',
        0x15: 'Power',

        0x21: 'Tuner',
        0x22: 'Video',
        0x25: 'CD',

        0x4D: 'Home',
        0x4B: 'Display',

        0x60: 'Sleep',
        0x6A: 'TV',

        0x53: 'Home',

        0x7C: 'Game',
        0x7D: 'DVD',
    }),

    # Amp, Game, Sat, Tuner, USB modes
    (0xB0, None): (['Arrows: ', 'Ar:'], {
        0x7A: 'Left',
        0x7B: 'Right',
        0x78: 'Up',
        0x79: 'Down',
        0x77: 'Amp Menu',
    }),

    # TV mode
    (0x97, None): (['TV Extra', 'TV:'], {
        0x23: 'Return',
        0x36: 'Options',

    }),
}

for (address, extended), (name, commands) in ADDRESSES.items():
    commands.update(NUMBERS)
