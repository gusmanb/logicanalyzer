##
## This file is part of the libsigrokdecode project.
##
## Copyright (C) 2019 Marco Geisler <m-sigrok@mageis.de>
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

regs = {
#   addr: 'name'
    0x00: 'IOCFG2',
    0x01: 'IOCFG1',
    0x02: 'IOCFG0',
    0x03: 'FIFOTHR',
    0x04: 'SYNC1',
    0x05: 'SYNC0',
    0x06: 'PKTLEN',
    0x07: 'PKTCTRL1',
    0x08: 'PKTCTRL0',
    0x09: 'ADDR',
    0x0A: 'CHANNR',
    0x0B: 'FSCTRL1',
    0x0C: 'FSCTRL0',
    0x0D: 'FREQ2',
    0x0E: 'FREQ1',
    0x0F: 'FREQ0',
    0x10: 'MDMCFG4',
    0x11: 'MDMCFG3',
    0x12: 'MDMCFG2',
    0x13: 'MDMCFG1',
    0x14: 'MDMCFG0',
    0x15: 'DEVIATN',
    0x16: 'MCSM2',
    0x17: 'MCSM1',
    0x18: 'MCSM0',
    0x19: 'FOCCFG',
    0x1A: 'BSCFG',
    0x1B: 'AGCTRL2',
    0x1C: 'AGCTRL1',
    0x1D: 'AGCTRL0',
    0x1E: 'WOREVT1',
    0x1F: 'WOREVT0',
    0x20: 'WORCTRL',
    0x21: 'FREND1',
    0x22: 'FREND0',
    0x23: 'FSCAL3',
    0x24: 'FSCAL2',
    0x25: 'FSCAL1',
    0x26: 'FSCAL0',
    0x27: 'RCCTRL1',
    0x28: 'RCCTRL0',
    0x29: 'FSTEST',
    0x2A: 'PTEST',
    0x2B: 'AGCTEST',
    0x2C: 'TEST2',
    0x2D: 'TEST1',
    0x2E: 'TEST0',
    0x30: 'PARTNUM',
    0x31: 'VERSION',
    0x32: 'FREQEST',
    0x33: 'LQI',
    0x34: 'RSSI',
    0x35: 'MARCSTATE',
    0x36: 'WORTIME1',
    0x37: 'WORTIME0',
    0x38: 'PKTSTATUS',
    0x39: 'VCO_VC_DAC',
    0x3A: 'TXBYTES',
    0x3B: 'RXBYTES',
    0x3C: 'RCCTRL1_STATUS',
    0x3D: 'RCCTRL0_STATUS',
    0x3E: 'PATABLE',
    0x3F: 'FIFO'
}

strobes = {
#   addr: 'name'
    0x30: 'SRES',
    0x31: 'SFSTXON',
    0x32: 'SXOFF',
    0x33: 'SCAL',
    0x34: 'SRX',
    0x35: 'STX',
    0x36: 'SIDLE',
    0x37: '',
    0x38: 'SWOR',
    0x39: 'SPWD',
    0x3A: 'SFRX',
    0x3B: 'SFTX',
    0x3C: 'SWORRST',
    0x3D: 'SNOP'
}

status_reg_states = {
#   value: 'state name'
    0b000: 'IDLE',
    0b001: 'RX',
    0b010: 'TX',
    0b011: 'FSTXON',
    0b100: 'CALIBRATE',
    0b101: 'SETTLING',
    0b110: 'RXFIFO_OVERFLOW',
    0b111: 'TXFIFO_OVERFLOW'
}
