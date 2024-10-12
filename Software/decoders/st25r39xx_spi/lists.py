##
## This file is part of the libsigrokdecode project.
##
## Copyright (C) 2019-2020 Benjamin Vernoux <bvernoux@gmail.com>
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
## v0.1 - 17 September 2019 B.VERNOUX using ST25R3916 Datasheet DS12484 Rev 1 (January 2019)
## v0.2 - 28 April 2020 B.VERNOUX using ST25R3916 Datasheet DS12484 Rev 2 (December 2019) https://www.st.com/resource/en/datasheet/st25r3916.pdf
## v0.3 - 17 June 2020 B.VERNOUX using ST25R3916 Datasheet DS12484 Rev 3 (04 June 2020) https://www.st.com/resource/en/datasheet/st25r3916.pdf

## ST25R3916 Datasheet DS12484 Rev 3 (04 June 2020) §4.4 Direct commands
dir_cmd = {
#   addr: 'name'
# Set Default
    0xC0: 'SET_DEFAULT',
    0xC1: 'SET_DEFAULT',
# Stop All Activities
    0xC2: 'STOP',
    0xC3: 'STOP',
# Transmit With CRC
    0xC4: 'TXCRC',
# Transmit Without CRC
    0xC5: 'TXNOCRC',
# Transmit REQA
    0xC6: 'TXREQA',
# Transmit WUPA
    0xC7: 'TXWUPA',
# NFC Initial Field ON
    0xC8: 'NFCINITFON',
# NFC Response Field ON
    0xC9: 'NFCRESFON',
# Go to Sense (Idle)
    0xCD: 'GOIDLE',
# Go to Sleep (Halt)
    0xCE: 'GOHALT',
# Mask Receive Data / Stops receivers and RX decoders
    0xD0: 'STOPRX',
# Unmask Receive Data / Starts receivers and RX decoders
    0xD1: 'STARRX',
# Change AM Modulation state
    0xD2: 'SETAMSTATE',
# Measure Amplitude
    0xD3: 'MAMP',
# Reset RX Gain
    0xD5: 'RSTRXGAIN',
# Adjust Regulators
    0xD6: 'ADJREG',
# Calibrate Driver Timing
    0xD8: 'CALDRVTIM',
# Measure Phase
    0xD9: 'MPHASE',
# Clear RSSI
    0xDA: 'CLRRSSI',
# Clear FIFO
    0xDB: 'CLRFIFO',
# Enter Transparent Mode
    0xDC: 'TRMODE',
# Calibrate Capacitive Sensor
    0xDD: 'CALCAPA',
# Measure Capacitance
    0xDE: 'MCAPA',
# Measure Power Supply
    0xDF: 'MPOWER',
# Start General Purpose Timer
    0xE0: 'STARGPTIM',
# Start Wake-up Timer
    0xE1: 'STARWTIM',
# Start Mask-receive Timer
    0xE2: 'STARMSKTIM',
# Start No-response Timer
    0xE3: 'STARNRESPTIM',
# Start PPON2 Timer
    0xE4: 'STARPPON2TIM',
# Stop No-response Timer
    0xE8: 'STOPNRESTIM',
# RFU / Not Used
    0xFA: 'RFU',
# Register Space-B Access
    0xFB: 'REGSPACEB',
# Register Test access
    0xFC: 'TESTACCESS'
# Other codes => RFU / Not Used
}

## ST25R3916 Datasheet DS12484 Rev 2 (December 2019) §4.5 Registers Table 17. List of registers - Space A
## ST25R3916 Datasheet DS12484 Rev 2 (December 2019) §4.3.3 Serial peripheral interface (SPI) Table 11. SPI operation modes
regsSpaceA = {
#   addr: 'name'
# §4.5 Registers Table 17. List of registers - Space A
# IO configuration
    0x00: 'IOCFG1',
    0x01: 'IOCFG2',
# Operation control and mode definition
    0x02: 'OPCTRL',
    0x03: 'MODEDEF',
    0x04: 'BITRATE',
# Protocol configuration
    0x05: 'TYPEA',
    0x06: 'TYPEB',
    0x07: 'TYPEBF',
    0x08: 'NFCIP1',
    0x09: 'STREAM',
    0x0A: 'AUX',
# Receiver configuration
    0x0B: 'RXCFG1',
    0x0C: 'RXCFG2',
    0x0D: 'RXCFG3',
    0x0E: 'RXCFG4',
# Timer definition
    0x0F: 'MSKRXTIM',
    0x10: 'NRESPTIM1',
    0x11: 'NRESPTIM2',
    0x12: 'TIMEMV',
    0x13: 'GPTIM1',
    0x14: 'GPTIM2',
    0x15: 'PPON2',
# Interrupt and associated reporting
    0x16: 'MSKMAINIRQ',
    0x17: 'MSKTIMNFCIRQ',
    0x18: 'MSKERRWAKEIRQ',
    0x19: 'TARGIRQ',
    0x1A: 'MAINIRQ',
    0x1B: 'TIMNFCIRQ',
    0x1C: 'ERRWAKEIRQ',
    0x1D: 'TARGIRQ',
    0x1E: 'FIFOSTAT1',
    0x1F: 'FIFOSTAT2',
    0x20: 'COLLDISP',
    0x21: 'TARGDISP',
# Definition of number of transmitted bytes
    0x22: 'NBTXB1',
    0x23: 'NBTXB2',
    0x24: 'BITRATEDET',
# A/D converter output
    0x25: 'ADCONVOUT',
# Antenna calibration
    0x26: 'ANTTUNECTRL1',
    0x27: 'ANTTUNECTRL2',
# Antenna driver and modulation
    0x28: 'TXDRV',
    0x29: 'TARGMOD',
# External field detector threshold
    0x2A: 'EXTFIELDON',
    0x2B: 'EXTFIELDOFF',
# Regulator
    0x2C: 'REGVDDCTRL',
# Receiver state display
    0x2D: 'RSSIDISP',
    0x2E: 'GAINSTATE',
# Capacitive sensor
    0x2F: 'CAPACTRL',
    0x30: 'CAPADISP',
# Auxiliary display
    0x31: 'AUXDISP',
# Wake-up
    0x32: 'WAKETIMCTRL',
    0x33: 'AMPCFG',
    0x34: 'AMPREF',
    0x35: 'AMPAAVGDISP',
    0x36: 'AMPDISP',
    0x37: 'PHASECFG',
    0x38: 'PHASEREF',
    0x39: 'PHASEAAVGDISP',
    0x3A: 'PHASEDISP',
    0x3B: 'CAPACFG',
    0x3C: 'CAPAREF',
    0x3D: 'CAPAAAVGDISP',
    0x3E: 'CAPADISP',
# IC identity
    0x3F: 'ICIDENT',
## ST25R3916 Datasheet DS12484 Rev 2 (December 2019) §4.3.3 Serial peripheral interface (SPI) Table 11. SPI operation modes
    0xA0: 'PT_memLoadA',
    0xA8: 'PT_memLoadF',
    0xAC: 'PT_memLoadTSN',
    0xBF: 'PT_memRead'
}

## ST25R3916 Datasheet DS12484 Rev 2 (December 2019) §4.5 Registers Table 18. List of registers - Space B
regsSpaceB = {
#   addr: 'name'
# §4.5 Registers Table 18. List of registers - Space B
# Protocol configuration
    0x05: 'EMDSUPPRCONF',
    0x06: 'SUBCSTARTIM',
# Receiver configuration
    0x0B: 'P2PRXCONF',
    0x0C: 'CORRCONF1',
    0x0D: 'CORRCONF2',
# Timer definition
    0x0F: 'SQUELSHTIM',
    0x15: 'NFCGUARDTIM',
# Antenna driver and modulation
    0x28: 'AUXMODSET',
    0x29: 'TXDRVTIM',
# External field detector threshold
    0x2A: 'RESAMMODE',
    0x2B: 'TXDRVTIMDISP',
# Regulator
    0x2C: 'REGDISP',
# Protection
    0x30: 'OSHOOTCONF1',
    0x31: 'OSHOOTCONF2',
    0x32: 'USHOOTCONF1',
    0x33: 'USHOOTCONF2'
}

## ST25R3916 Datasheet DS12484 Rev 2 (December 2019) §4.4.17 Test access
regsTest = {
#   addr: 'name'
# §4.4.17 Test access (Typo in datasheet it is not register 0x00 but 0x01)
    0x01: 'ANTSTOBS'
}

## Optional TODO add important status bit fields / ANN_STATUS
## Interrupt and associated reporting => Registers Space A from Address (hex) 0x16 to 0x21
## §4.5.58 RSSI display register
## §4.5.59 Gain reduction state register
## ...

