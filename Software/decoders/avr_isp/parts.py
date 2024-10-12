##
## This file is part of the libsigrokdecode project.
##
## Copyright (C) 2012 Uwe Hermann <uwe@hermann-uwe.de>
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

# Device code addresses:
# 0x00: vendor code, 0x01: part family + flash size, 0x02: part number

# Vendor code
vendor_code = {
    0x1E: 'Atmel',
    0x00: 'Device locked',
}

# (Part family + flash size, part number)
part = {
    (0x90, 0x01): 'AT90S1200',
    (0x90, 0x05): 'ATtiny12',
    (0x90, 0x06): 'ATtiny15',
    (0x90, 0x07): 'ATtiny13',
    (0x91, 0x01): 'AT90S2313',
    (0x91, 0x02): 'AT90S2323',
    (0x91, 0x03): 'AT90S2343',
    (0x91, 0x05): 'AT90S2333',
    (0x91, 0x06): 'ATtiny22',
    (0x91, 0x07): 'ATtiny28',
    (0x91, 0x08): 'ATtiny25',
    (0x91, 0x09): 'ATtiny26',
    (0x91, 0x0A): 'ATtiny2313',
    (0x91, 0x0B): 'ATtiny24',
    (0x91, 0x0C): 'ATtiny261',
    (0x92, 0x01): 'AT90S4414',
    (0x92, 0x03): 'AT90S4433',
    (0x92, 0x05): 'ATmega48(A)',
    (0x92, 0x06): 'ATtiny45',
    (0x92, 0x08): 'ATtiny461',
    (0x92, 0x09): 'ATtiny48',
    (0x92, 0x0A): 'ATmega48PA',
    (0x92, 0x0D): 'ATtiny4313',
    (0x92, 0x10): 'ATmega48PB',
    (0x93, 0x01): 'AT90S8515',
    (0x93, 0x03): 'AT90S8535',
    (0x93, 0x07): 'ATmega8',
    (0x93, 0x0A): 'ATmega88(A)',
    (0x93, 0x0B): 'ATtiny85',
    (0x93, 0x0D): 'ATtiny861',
    (0x93, 0x0F): 'ATmega88PA',
    (0x93, 0x11): 'ATtiny88',
    (0x93, 0x16): 'ATmega88PB',
    (0x93, 0x89): 'ATmega8U2',
    (0x94, 0x01): 'ATmega161',
    (0x94, 0x02): 'ATmega163',
    (0x94, 0x03): 'ATmega16',
    (0x94, 0x04): 'ATmega162',
    (0x94, 0x06): 'ATmega168(A)',
    (0x94, 0x0A): 'ATmega164PA',
    (0x94, 0x0B): 'ATmega168PA',
    (0x94, 0x0F): 'ATmega164A',
    (0x94, 0x12): 'ATtiny1634',
    (0x94, 0x15): 'ATmega168PB',
    (0x94, 0x88): 'ATmega16U4',
    (0x94, 0x89): 'ATmega16U2',
    (0x95, 0x01): 'ATmega32',
    (0x95, 0x01): 'ATmega323',
    (0x95, 0x0F): 'ATmega328P',
    (0x95, 0x11): 'ATmega324PA',
    (0x95, 0x14): 'ATmega328',
    (0x95, 0x15): 'ATmega324A',
    (0x95, 0x87): 'ATmega32U4',
    (0x95, 0x8A): 'ATmega32U2',
    (0x96, 0x08): 'ATmega640',
    (0x96, 0x09): 'ATmega644(A)',
    (0x96, 0x0A): 'ATmega644PA',
    (0x97, 0x01): 'ATmega103',
    (0x97, 0x03): 'ATmega1280',
    (0x97, 0x04): 'ATmega1281',
    (0x97, 0x05): 'ATmega1284P',
    (0x97, 0x06): 'ATmega1284',
    (0x98, 0x01): 'ATmega2560',
    (0x98, 0x02): 'ATmega2561',
    (0xFF, 0xFF): 'Device code erased, or target missing',
    (0x01, 0x02): 'Device locked',
}
