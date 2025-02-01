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

'''
This decoder stacks on top of the 'spi' PD and decodes the SD card
(SPI mode) low-level protocol.

Most SD cards can be accessed via two different protocols/modes: SD mode
or SPI mode.

All SD cards are in SD mode upon powerup. They can be switched to SPI mode
using a special method involving CMD0 (see spec). Once in SPI mode, the mode
can no longer be changed without a power-cycle of the card.

SPI mode properties (differences to SD mode):
 * The 'sdcard_spi' PD stacks on top of the 'spi' PD. This is not possible
   for the 'sdcard_sd' PD, as that protocol is not SPI related at all.
   Hence 'sdcard_spi' and 'sdcard_sd' are two separate PDs.
 * The state machines for SPI mode and SD mode are different.
 * In SPI mode, data transfers are byte-oriented (commands/data are multiples
   of 8 bits, with the CS# pin asserted respectively), unlike SD mode where
   commands/data are bit-oriented with parallel transmission of 1 or 4 bits.
 * While the SPI mode command set has some commands in common with the
   SD mode command set, they are not the same and also not a subset/superset.
   Some commands are only available in SD mode (e.g. CMD2), some only
   in SPI mode (e.g. CMD1).
 * Response types of commands also differ between SD mode and SPI mode.
   E.g. CMD9 has an R2 response in SD mode, but R1 in SPI mode.
 * The commands and functions in SD mode defined after version 2.00 of the
   spec are NOT supported in SPI mode.
 * SPI mode: The selected SD card ALWAYS responds to commands (unlike SD mode).
 * Upon data retrieval problems (read operations) the card will respond with
   an error response (and no data), as opposed to a timeout in SD mode.
 * SPI mode: For every data block sent to the card (write operations) the host
   gets a data response token from the card.
 * SDSC: A data block can be max. one card write block, min. 1 byte.
 * SDHC/SDXC: Block length is fixed to 512. The block length set by CMD16
   is only used for CDM42 (not for memory data transfers). Thus, partial
   read/write operations are disabled in SPI mode.
 * SPI mode: Write protected commands (CMD28, CMD29, CMD30) are not supported.
 * The SD mode state machine is NOT used. All commands that are supported
   in SPI mode are always available.
 * Per default the card is in CRC OFF mode. Exception: CMD0 (which is used to
   switch to SPI mode) needs a valid CRC.
 * The APP_CMD status bit is not available in SPI mode.
 * TODO: Switch function command differences.
 * In SPI mode cards cannot guarantee their speed class (the host should
   assume class 0, no matter what the card indicates).
 * The RCA register is not accessible in SPI mode.
'''

from .pd import Decoder
