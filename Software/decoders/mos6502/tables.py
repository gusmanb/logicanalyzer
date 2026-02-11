##
## This file is part of the libsigrokdecode project.
##
## Copyright (C) 2017 David Banks <dave@hoglet.com>
## Update 2025 by Emile <emile@vandelogt.nl>: 
##             - added address- and data format-specifiers
##             - removed non-6502 addressing modes
##
## This program is free software; you can redistribute it and/or modify
## it under the terms of the GNU General Public License as published by
## the Free Software Foundation; either version 3 of the License, or
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
  6502 Addressing Modes

  Map of Addressing Mode to Instruction Length

  Instruction tuple: (string, addressing mode)
'''

# ---------------------------------------------------
# 6502 Addressing modes
# ---------------------------------------------------
class AddrMode:
    IMP, IMPA, BRA, IMM, ZP, ZPX, ZPY, INDX, INDY, ABS, ABSX, ABSY, IND16 = range(13)

# ---------------------------------------------------
# Map of Addressing Mode to Instruction Length
# ---------------------------------------------------
addr_mode_len_map = {
    AddrMode.IMP:   1, # implied mode, just the opcode
    AddrMode.IMPA:  1, # Accumulator mode
    AddrMode.BRA:   2, # Branch type instructions, relative addressing
    AddrMode.IMM:   2, # Immediate mode 
    AddrMode.ZP:    2, # Zero Page mode
    AddrMode.ZPX:   2, # X-indexed Zero Page mode: $nn,Y
    AddrMode.ZPY:   2, # Y-indexed Zero Page mode: $nn,X
    AddrMode.INDX:  2, # X-indexed Zero Page indirect mode: ($nn,X)
    AddrMode.INDY:  2, # Zero Page Indirect Y-indexed mode: ($nn),Y
    AddrMode.ABS:   3, # Absolute: $nnnn
    AddrMode.ABSX:  3, # X-Indexed Absolute: $nnnn,X
    AddrMode.ABSY:  3, # Y-indexed Absolute: $nnnn,Y
    AddrMode.IND16: 3, # Absolute Indirect: ($nnnn)
}

# ---------------------------------------------------
# Instruction tuple: (string, addressing mode)
# ---------------------------------------------------
instr_table = {
    0x00: ( 'BRK'            , AddrMode.IMP  ),
    0x01: ( 'ORA (${:02X},X)', AddrMode.INDX ), # ZP
    0x02: ( '???'            , AddrMode.IMP  ),
    0x03: ( '???'            , AddrMode.IMP  ),
    0x04: ( '???'            , AddrMode.IMP  ),
    0x05: ( 'ORA ${:02X}'    , AddrMode.ZP   ), # ZP
    0x06: ( 'ASL ${:02X}'    , AddrMode.ZP   ), # ZP
    0x07: ( '???'            , AddrMode.IMP  ),
    0x08: ( 'PHP'            , AddrMode.IMP  ),
    0x09: ( 'ORA #${:02X}'   , AddrMode.IMM  ), # ZP
    0x0A: ( 'ASL A'          , AddrMode.IMPA ),
    0x0B: ( '???'            , AddrMode.IMP  ),
    0x0C: ( '???'            , AddrMode.ABS  ),
    0x0D: ( 'ORA ${:04X}'    , AddrMode.ABS  ), # A16
    0x0E: ( 'ASL ${:04X}'    , AddrMode.ABS  ), # A16
    0x0F: ( '???'            , AddrMode.IMP  ),
    0x10: ( 'BPL ${:04X}'    , AddrMode.BRA  ),
    0x11: ( 'ORA (${:02X}),Y', AddrMode.INDY ), # ZP
    0x12: ( '???'            , AddrMode.IMP  ),
    0x13: ( '???'            , AddrMode.IMP  ),
    0x14: ( '???'            , AddrMode.IMP  ),
    0x15: ( 'ORA ${:02X},X'  , AddrMode.ZPX  ), # ZP
    0x16: ( 'ASL ${:02X},X'  , AddrMode.ZPX  ), # ZP
    0x17: ( '???'            , AddrMode.IMP  ),
    0x18: ( 'CLC'            , AddrMode.IMP  ),
    0x19: ( 'ORA ${:04X},Y'  , AddrMode.ABSY ), # A16
    0x1A: ( '???'            , AddrMode.IMP  ),
    0x1B: ( '???'            , AddrMode.IMP  ),
    0x1C: ( '???'            , AddrMode.IMP  ),
    0x1D: ( 'ORA ${:04X},X'  , AddrMode.ABSX ), # A16
    0x1E: ( 'ASL ${:04X},X'  , AddrMode.ABSX ), # A16
    0x1F: ( '???'            , AddrMode.IMP  ),
    0x20: ( 'JSR ${:04X}'    , AddrMode.ABS  ),
    0x21: ( 'AND (${:02X},X)', AddrMode.INDX ), # ZP
    0x22: ( '???'            , AddrMode.IMP  ),
    0x23: ( '???'            , AddrMode.IMP  ),
    0x24: ( 'BIT ${:02X}'    , AddrMode.ZP   ), # ZP
    0x25: ( 'AND ${:02X}'    , AddrMode.ZP   ), # ZP
    0x26: ( 'ROL ${:02X}'    , AddrMode.ZP   ), # ZP
    0x27: ( '???'            , AddrMode.IMP  ),
    0x28: ( 'PLP'            , AddrMode.IMP  ),
    0x29: ( 'AND #${:02X}'   , AddrMode.IMM  ),
    0x2A: ( 'ROL A'          , AddrMode.IMPA ),
    0x2B: ( '???'            , AddrMode.IMP  ),
    0x2C: ( 'BIT ${:04X}'    , AddrMode.ABS  ), # A16
    0x2D: ( 'AND ${:04X}'    , AddrMode.ABS  ), # A16
    0x2E: ( 'ROL ${:04X}'    , AddrMode.ABS  ), # A16
    0x2F: ( '???'            , AddrMode.IMP  ),
    0x30: ( 'BMI ${:04X}'    , AddrMode.BRA  ),
    0x31: ( 'AND (${:02X}),Y', AddrMode.INDY ), # ZP
    0x32: ( '???'            , AddrMode.IMP  ),
    0x33: ( '???'            , AddrMode.IMP  ),
    0x34: ( '???'            , AddrMode.IMP  ),
    0x35: ( 'AND ${:02X},X'  , AddrMode.ZPX  ), # ZP
    0x36: ( 'ROL ${:02X},X'  , AddrMode.ZPX  ), # ZP
    0x37: ( '???'            , AddrMode.IMP  ),
    0x38: ( 'SEC'            , AddrMode.IMP  ),
    0x39: ( 'AND ${:04X},Y'  , AddrMode.ABSY ), # A16
    0x3A: ( '???'            , AddrMode.IMP  ),
    0x3B: ( '???'            , AddrMode.IMP  ),
    0x3C: ( '???'            , AddrMode.IMP  ),
    0x3D: ( 'AND ${:04X},X'  , AddrMode.ABSX ), # A16
    0x3E: ( 'ROL ${:04X},X'  , AddrMode.ABSX ), # A16
    0x3F: ( '???'            , AddrMode.IMP  ),
    0x40: ( 'RTI'            , AddrMode.IMP  ),
    0x41: ( 'EOR (${:02X}),X', AddrMode.INDX ), # ZP
    0x42: ( '???'            , AddrMode.IMP  ),
    0x43: ( '???'            , AddrMode.IMP  ),
    0x44: ( '???'            , AddrMode.IMP  ),
    0x45: ( 'EOR ${:02X}'    , AddrMode.ZP   ), # ZP
    0x46: ( 'LSR ${:02X}'    , AddrMode.ZP   ), # ZP
    0x47: ( '???'            , AddrMode.IMP  ),
    0x48: ( 'PHA'            , AddrMode.IMP  ),
    0x49: ( 'EOR #${:02X}'   , AddrMode.IMM  ),
    0x4A: ( 'LSR A'          , AddrMode.IMPA ),
    0x4B: ( '???'            , AddrMode.IMP  ),
    0x4C: ( 'JMP ${:04X}'    , AddrMode.ABS  ), # A16
    0x4D: ( 'EOR ${:04X}'    , AddrMode.ABS  ), # A16
    0x4E: ( 'LSR ${:04X}'    , AddrMode.ABS  ), # A16
    0x4F: ( '???'            , AddrMode.IMP  ),
    0x50: ( 'BVC ${:04X}'    , AddrMode.BRA  ),
    0x51: ( 'EOR (${:02X}),Y', AddrMode.INDY ), # ZP
    0x52: ( '???'            , AddrMode.IMP  ),
    0x53: ( '???'            , AddrMode.IMP  ),
    0x54: ( '???'            , AddrMode.IMP  ),
    0x55: ( 'EOR ${:02X},X'  , AddrMode.ZPX  ), # ZP
    0x56: ( 'LSR ${:02X},X'  , AddrMode.ZPX  ), # ZP
    0x57: ( '???'            , AddrMode.IMP  ),
    0x58: ( 'CLI'            , AddrMode.IMP  ),
    0x59: ( 'EOR ${:04X},Y'  , AddrMode.ABSY ), # A16
    0x5A: ( '???'            , AddrMode.IMP  ),
    0x5B: ( '???'            , AddrMode.IMP  ),
    0x5C: ( '???'            , AddrMode.IMP  ),
    0x5D: ( 'EOR ${:04X},X'  , AddrMode.ABSX ), # A16
    0x5E: ( 'LSR ${:04X},X'  , AddrMode.ABSX ), # A16
    0x5F: ( '???'            , AddrMode.IMP  ),
    0x60: ( 'RTS'            , AddrMode.IMP  ),
    0x61: ( 'ADC (${:02X},X)', AddrMode.INDX ), # ZP
    0x62: ( '???'            , AddrMode.IMP  ),
    0x63: ( '???'            , AddrMode.IMP  ),
    0x64: ( '???'            , AddrMode.IMP  ),
    0x65: ( 'ADC ${:02X}'    , AddrMode.ZP   ), # ZP
    0x66: ( 'ROR ${:02X}'    , AddrMode.ZP   ), # ZP
    0x67: ( '???'            , AddrMode.IMP  ),
    0x68: ( 'PLA'            , AddrMode.IMP  ),
    0x69: ( 'ADC #${:02X}'   , AddrMode.IMM  ),
    0x6A: ( 'ROR A'          , AddrMode.IMPA ),
    0x6B: ( '???'            , AddrMode.IMP  ),
    0x6C: ( 'JMP (${:04X})'  , AddrMode.IND16), # (A16)
    0x6D: ( 'ADC ${:04X}'    , AddrMode.ABS  ), # A16
    0x6E: ( 'ROR ${:04X}'    , AddrMode.ABS  ), # A16
    0x6F: ( '???'            , AddrMode.IMP  ),
    0x70: ( 'BVS ${:04X}'    , AddrMode.BRA  ),
    0x71: ( 'ADC (${:02X}),Y', AddrMode.INDY ), # ZP
    0x72: ( '???'            , AddrMode.IMP  ),
    0x73: ( '???'            , AddrMode.IMP  ),
    0x74: ( '???'            , AddrMode.IMP  ),
    0x75: ( 'ADC ${:02X},X'  , AddrMode.ZPX  ), # ZP
    0x76: ( 'ROR ${:02X},X'  , AddrMode.ZPX  ), # ZP
    0x77: ( '???'            , AddrMode.IMP  ),
    0x78: ( 'SEI'            , AddrMode.IMP  ),
    0x79: ( 'ADC ${:04X},Y'  , AddrMode.ABSY ), # A16
    0x7A: ( '???'            , AddrMode.IMP  ),
    0x7B: ( '???'            , AddrMode.IMP  ),
    0x7C: ( '???'            , AddrMode.IMP  ),
    0x7D: ( 'ADC ${:04X},X'  , AddrMode.ABSX ), # A16
    0x7E: ( 'ROR ${:04X},X'  , AddrMode.ABSX ), # A16
    0x7F: ( '???'            , AddrMode.IMP  ),
    0x80: ( '???'            , AddrMode.IMP  ),
    0x81: ( 'STA (${:02X},X)', AddrMode.INDX ), # ZP
    0x82: ( '???'            , AddrMode.IMP  ),
    0x83: ( '???'            , AddrMode.IMP  ),
    0x84: ( 'STY ${:02X}'    , AddrMode.ZP   ), # ZP
    0x85: ( 'STA ${:02X}'    , AddrMode.ZP   ), # ZP
    0x86: ( 'STX ${:02X}'    , AddrMode.ZP   ), # ZP
    0x87: ( '???'            , AddrMode.IMP  ),
    0x88: ( 'DEY'            , AddrMode.IMP  ),
    0x89: ( '???'            , AddrMode.IMP  ),
    0x8A: ( 'TXA'            , AddrMode.IMP  ),
    0x8B: ( '???'            , AddrMode.IMP  ),
    0x8C: ( 'STY ${:04X}'    , AddrMode.ABS  ), # A16
    0x8D: ( 'STA ${:04X}'    , AddrMode.ABS  ), # A16
    0x8E: ( 'STX ${:04X}'    , AddrMode.ABS  ), # A16
    0x8F: ( '???'            , AddrMode.IMP  ),
    0x90: ( 'BCC ${:04X}'    , AddrMode.BRA  ),
    0x91: ( 'STA (${:02X}),Y', AddrMode.INDY ), # ZP
    0x92: ( '???'            , AddrMode.IMP  ),
    0x93: ( '???'            , AddrMode.IMP  ),
    0x94: ( 'STY ${:02X},X'  , AddrMode.ZPX  ), # ZP
    0x95: ( 'STA ${:02X},X'  , AddrMode.ZPX  ), # ZP
    0x96: ( 'STX ${:02X},Y'  , AddrMode.ZPY  ), # ZP
    0x97: ( '???'            , AddrMode.IMP  ),
    0x98: ( 'TYA'            , AddrMode.IMP  ),
    0x99: ( 'STA ${:04X},Y'  , AddrMode.ABSY ), # A16
    0x9A: ( 'TXS'            , AddrMode.IMP  ),
    0x9B: ( '???'            , AddrMode.IMP  ),
    0x9C: ( '???'            , AddrMode.IMP  ),
    0x9D: ( 'STA ${:04X},X'  , AddrMode.ABSX ), # A16
    0x9E: ( '???'            , AddrMode.IMP  ),
    0x9F: ( '???'            , AddrMode.IMP  ),
    0xA0: ( 'LDY #${:02X}'   , AddrMode.IMM  ),
    0xA1: ( 'LDA (${:02X},X)', AddrMode.INDX ), # ZP
    0xA2: ( 'LDX #${:02X}'   , AddrMode.IMM  ),
    0xA3: ( '???'            , AddrMode.IMP  ),
    0xA4: ( 'LDY ${:02X}'    , AddrMode.ZP   ), # ZP
    0xA5: ( 'LDA ${:02X}'    , AddrMode.ZP   ), # ZP
    0xA6: ( 'LDX ${:02X}'    , AddrMode.ZP   ), # ZP
    0xA7: ( '???'            , AddrMode.IMP  ),
    0xA8: ( 'TAY'            , AddrMode.IMP  ),
    0xA9: ( 'LDA #${:02X}'   , AddrMode.IMM  ),
    0xAA: ( 'TAX'            , AddrMode.IMP  ),
    0xAB: ( '???'            , AddrMode.IMP  ),
    0xAC: ( 'LDY ${:04X}'    , AddrMode.ABS  ), # A16
    0xAD: ( 'LDA ${:04X}'    , AddrMode.ABS  ), # A16
    0xAE: ( 'LDX ${:04X}'    , AddrMode.ABS  ), # A16
    0xAF: ( '???'            , AddrMode.IMP  ),
    0xB0: ( 'BCS ${:04X}'    , AddrMode.BRA  ),
    0xB1: ( 'LDA (${:02X}),Y', AddrMode.INDY ), # ZP
    0xB2: ( '???'            , AddrMode.IMP  ),
    0xB3: ( '???'            , AddrMode.IMP  ),
    0xB4: ( 'LDY ${:02X},X'  , AddrMode.ZPX  ), # ZP
    0xB5: ( 'LDA ${:02X},X'  , AddrMode.ZPX  ), # ZP
    0xB6: ( 'LDX ${:02X},Y'  , AddrMode.ZPY  ), # ZP
    0xB7: ( '???'            , AddrMode.IMP  ),
    0xB8: ( 'CLV'            , AddrMode.IMP  ),
    0xB9: ( 'LDA ${:04X},Y'  , AddrMode.ABSY ), # A16
    0xBA: ( 'TSX'            , AddrMode.IMP  ),
    0xBB: ( '???'            , AddrMode.IMP  ),
    0xBC: ( 'LDY ${:04X},X'  , AddrMode.ABSX ), # A16
    0xBD: ( 'LDA ${:04X},Y'  , AddrMode.ABSX ), # A16
    0xBE: ( 'LDX ${:04X},Y'  , AddrMode.ABSY ), # A16
    0xBF: ( '???'            , AddrMode.IMP  ),
    0xC0: ( 'CPY #${:02X}'   , AddrMode.IMM  ),
    0xC1: ( 'CMP (${:02X},X)', AddrMode.INDX ), # ZP
    0xC2: ( '???'            , AddrMode.IMP  ),
    0xC3: ( '???'            , AddrMode.IMP  ),
    0xC4: ( 'CPY ${:02X}'    , AddrMode.ZP   ), # ZP
    0xC5: ( 'CMP ${:02X}'    , AddrMode.ZP   ), # ZP
    0xC6: ( 'DEC ${:02X}'    , AddrMode.ZP   ), # ZP
    0xC7: ( '???'            , AddrMode.IMP  ),
    0xC8: ( 'INY'            , AddrMode.IMP  ),
    0xC9: ( 'CMP #${:02X}'   , AddrMode.IMM  ),
    0xCA: ( 'DEX'            , AddrMode.IMP  ),
    0xCB: ( '???'            , AddrMode.IMP  ),
    0xCC: ( 'CPY ${:04X}'    , AddrMode.ABS  ), # A16
    0xCD: ( 'CMP ${:04X}'    , AddrMode.ABS  ), # A16
    0xCE: ( 'DEC ${:04X}'    , AddrMode.ABS  ), # A16
    0xCF: ( '???'            , AddrMode.IMP  ),
    0xD0: ( 'BNE ${:04X}'    , AddrMode.BRA  ),
    0xD1: ( 'CMP (${:02X}),Y', AddrMode.INDY ), # ZP
    0xD2: ( '???'            , AddrMode.IMP  ),
    0xD3: ( '???'            , AddrMode.IMP  ),
    0xD4: ( '???'            , AddrMode.IMP  ),
    0xD5: ( 'CMP ${:02X},X'  , AddrMode.ZPX  ), # ZP
    0xD6: ( 'DEC ${:02X},X'  , AddrMode.ZPX  ), # ZP
    0xD7: ( '???'            , AddrMode.IMP  ),
    0xD8: ( 'CLD'            , AddrMode.IMP  ),
    0xD9: ( 'CMP ${:04X},Y'  , AddrMode.ABSY ), # A16
    0xDA: ( '???'            , AddrMode.IMP  ),
    0xDB: ( '???'            , AddrMode.IMP  ),
    0xDC: ( '???'            , AddrMode.IMP  ),
    0xDD: ( 'CMP ${:04X},X'  , AddrMode.ABSX ), # A16
    0xDE: ( 'DEC ${:04X},X'  , AddrMode.ABSX ), # A16
    0xDF: ( '???'            , AddrMode.IMP  ),
    0xE0: ( 'CPX #${:02X}'   , AddrMode.IMM  ),
    0xE1: ( 'SBC (${:02X},X)', AddrMode.INDX ), # ZP
    0xE2: ( '???'            , AddrMode.IMP  ),
    0xE3: ( '???'            , AddrMode.IMP  ),
    0xE4: ( 'CPX ${:02X}'    , AddrMode.ZP   ), # ZP
    0xE5: ( 'SBC ${:02X}'    , AddrMode.ZP   ), # ZP
    0xE6: ( 'INC ${:02X}'    , AddrMode.ZP   ), # ZP
    0xE7: ( '???'            , AddrMode.IMP  ),
    0xE8: ( 'INX'            , AddrMode.IMP  ),
    0xE9: ( 'SBC #${:02X}'   , AddrMode.IMM  ),
    0xEA: ( 'NOP'            , AddrMode.IMP  ),
    0xEB: ( '???'            , AddrMode.IMP  ),
    0xEC: ( 'CPX ${:04X}'    , AddrMode.ABS  ), # A16
    0xED: ( 'SBC ${:04X}'    , AddrMode.ABS  ), # A16
    0xEE: ( 'INC ${:04X}'    , AddrMode.ABS  ), # A16
    0xEF: ( '???'            , AddrMode.IMP  ),
    0xF0: ( 'BEQ ${:04X}'    , AddrMode.BRA  ),
    0xF1: ( 'SBC (${:02X}),Y', AddrMode.INDY ),
    0xF2: ( '???'            , AddrMode.IMP  ),
    0xF3: ( '???'            , AddrMode.IMP  ),
    0xF4: ( '???'            , AddrMode.IMP  ),
    0xF5: ( 'SBC ${:02X},X'  , AddrMode.ZPX  ), # ZP
    0xF6: ( 'INC ${:02X},X'  , AddrMode.ZPX  ), # ZP
    0xF7: ( '???'            , AddrMode.IMP  ),
    0xF8: ( 'SED'            , AddrMode.IMP  ),
    0xF9: ( 'SBC ${:04X},Y'  , AddrMode.ABSY ), # A16
    0xFA: ( '???'            , AddrMode.IMP  ),
    0xFB: ( '???'            , AddrMode.IMP  ),
    0xFC: ( '???'            , AddrMode.IMP  ),
    0xFD: ( 'SBC ${:04X},X'  , AddrMode.ABSX ), # A16
    0xFE: ( 'INC ${:04X},X'  , AddrMode.ABSX ), # A16
    0xFF: ( '???'            , AddrMode.IMP  ),
}
