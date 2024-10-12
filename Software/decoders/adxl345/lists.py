##
## This file is part of the libsigrokdecode project.
##
## Copyright (C) 2020 Analog Devices Inc.
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
## along with this program; if not, write to the Free Software
## Foundation, Inc., 51 Franklin St, Fifth Floor, Boston, MA  02110-1301 USA
##

error_messages = {
    'interrupt': ['Interrupt'],
    'undesirable':  ['Undesirable behavior'],
    'dis_single': ['Disable single tap'],
    'dis_double': ['Disable double tap'],
    'dis_single_double': ['Disable single/double tap'],
}

rate_code = {
    0x00: 0.1,
    0x01: 0.2,
    0x02: 0.39,
    0x03: 0.78,
    0x04: 1.56,
    0x05: 3.13,
    0x06: 6.25,
    0x07: 12.5,
    0x08: 25,
    0x09: 50,
    0x0A: 100,
    0x0B: 200,
    0x0C: 400,
    0x0D: 800,
    0x0E: 1600,
    0x0F: 3200,
}

fifo_modes = {
    0x00: 'Bypass',
    0x01: 'FIFO',
    0x02: 'Stream',
    0x03: 'Trigger',
}

operations = {
    0x00: ['WRITE REG', 'WRITE', 'W'],
    0x01: ['READ REG', 'READ', 'R'],
}

number_bytes = {
    0x00: ['SINGLE BYTE', 'SING BYTE', '1 BYTE', '1B'],
    0x01: ['MULTIPLE BYTES', 'MULTI BYTES', 'n*BYTES', 'n*B'],
}

registers = {
    0x00: ['DEVID', 'DID', 'ID'],
    0x1D: ['THRESH_TAP', 'TH_TAP', 'TH_T'],
    0x1E: ['OFSX', 'OFX'],
    0x1F: ['OFSY', 'OFY'],
    0x20: ['OFSZ', 'OFZ'],
    0x21: ['DUR'],
    0x22: ['Latent', 'Lat'],
    0x23: ['Window', 'Win'],
    0x24: ['THRESH_ACT', 'TH_ACT', 'TH_A'],
    0x25: ['THRESH_INACT', 'TH_INACT', 'TH_I'],
    0x26: ['TIME_INACT', 'TI_INACT', 'TI_I'],
    0x27: ['ACT_INACT_CTL', 'ACT_I_CTL', 'A_I_C'],
    0x28: ['THRESH_FF', 'TH_FF'],
    0x29: ['TIME_FF', 'TI_FF'],
    0x2A: ['TAP_AXES', 'TAP_AX', 'TP_AX'],
    0x2B: ['ACT_TAP_STATUS', 'ACT_TAP_STAT', 'ACT_TP_ST', 'A_T_S'],
    0x2C: ['BW_RATE', 'BW_R'],
    0x2D: ['POWER_CTL', 'PW_CTL', 'PW_C'],
    0x2E: ['INT_ENABLE', 'INT_EN', 'I_EN'],
    0x2F: ['INT_MAP', 'I_M'],
    0x30: ['INT_SOURCE', 'INT_SRC', 'I_SRC', 'I_S'],
    0x31: ['DATA_FORMAT', 'DATA_FRM', 'D_FRM', 'D_F'],
    0x32: ['DATAX0', 'DX0', 'X0'],
    0x33: ['DATAX1', 'DX1', 'X1'],
    0x34: ['DATAY0', 'DY0', 'Y0'],
    0x35: ['DATAY1', 'DY1', 'Y1'],
    0x36: ['DATAZ0', 'DZ0', 'Z0'],
    0x37: ['DATAZ1', 'DZ1', 'Z1'],
    0x38: ['FIFO_CTL', 'FIF_CT', 'F_C'],
    0x39: ['FIFO_STATUS', 'FIFO_STAT', 'FIF_ST', 'F_S'],
}
