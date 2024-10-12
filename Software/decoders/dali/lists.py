##
## This file is part of the libsigrokdecode project.
##
## Copyright (C) 2015 Jeremy Swanson <jeremy@rakocontrols.com>
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
## along with this program.  If not, see <http://www.gnu.org/licenses/>.
##

# DALI extended commands
extended_commands = {
    0xA1: ['Terminate special processes', 'Terminate'],
    0xA3: ['DTR = DATA', 'DTR'],
    0xA5: ['INITIALISE', 'INIT'],
    0xA7: ['RANDOMISE', 'RAND'],
    0xA9: ['COMPARE', 'COMP'],
    0xAB: ['WITHDRAW', 'WDRAW'],
    0xB1: ['SET SEARCH H', 'SAH'],
    0xB3: ['SET SEARCH M', 'SAM'],
    0xB5: ['SET SEARCH L', 'SAL'],
    0xB7: ['Program Short Address', 'ProgSA'],
    0xB9: ['Verify Short Address', 'VfySA'],
    0xBB: ['Query Short Address', 'QryShort'],
    0xBD: ['Physical Selection', 'PysSel'],
    0xC1: ['Enable Device Type X', 'EnTyp'],
    0xC3: ['DTR1 = DATA', 'DTR1'],
    0xC5: ['DTR2 = DATA', 'DTR2'],
    0xC7: ['Write Memory Location', 'WRI'],
}

# List of commands
dali_commands = {
    0x00: ['Immediate Off', 'IOFF'],
    0x01: ['Up 200ms', 'Up'],
    0x02: ['Down 200ms', 'Down'],
    0x03: ['Step Up', 'Step+'],
    0x04: ['Step Down', 'Step-'],
    0x05: ['Recall Maximum Level', 'Recall Max'],
    0x06: ['Recall Minimum Level', 'Recall Min'],
    0x07: ['Step down and off', 'Down Off'],
    0x08: ['Step ON and UP', 'On Up'],
    0x20: ['Reset', 'Rst'],
    0x21: ['Store Dim Level in DTR', 'Level -> DTR'],
    0x2A: ['Store DTR as Max Level', 'DTR->Max'],
    0x2B: ['Store DTR as Min Level', 'DTR->Min'],
    0x2C: ['Store DTR as Fail Level', 'DTR->Fail'],
    0x2D: ['Store DTR as Power On Level', 'DTR->Poweron'],
    0x2E: ['Store DTR as Fade Time', 'DTR->Fade'],
    0x2F: ['Store DTR as Fade Rate', 'DTR->Rate'],
    0x80: ['Store DTR as Short Address', 'DTR->Add'],
    0x81: ['Enable Memory Write', 'WEn'],
    0x90: ['Query Status', 'Status'],
    0x91: ['Query Ballast', 'Ballast'],
    0x92: ['Query Lamp Failure', 'LmpFail'],
    0x93: ['Query Power On', 'Power On'],
    0x94: ['Query Limit Error', 'Limit Err'],
    0x95: ['Query Reset', 'Reset State'],
    0x96: ['Query Missing Short Address', 'NoSrt'],
    0x97: ['Query Version', 'Ver'],
    0x98: ['Query DTR', 'GetDTR'],
    0x99: ['Query Device Type', 'Type'],
    0x9A: ['Query Physical Minimum', 'PhysMin'],
    0x9B: ['Query Power Fail', 'PowerFailed'],
    0x9C: ['Query DTR1', 'GetDTR1'],
    0x9D: ['Query DTR2', 'GetDTR2'],
    0xA0: ['Query Level', 'GetLevel'],
    0xA1: ['Query Max Level', 'GetMax'],
    0xA2: ['Query Min Level', 'GetMin'],
    0xA3: ['Query Power On', 'GetPwrOn'],
    0xA4: ['Query Fail Level', 'GetFail'],
    0xA5: ['Query Fade Rate', 'GetRate'],
    0xA6: ['Query Power Fail', 'PwrFail'],
    0xC0: ['Query Groups 0-7', 'GetGrpsL'],
    0xC1: ['Query Groups 7-15', 'GetGrpsH'],
    0xC2: ['Query BRNH', 'BRNH'],
    0xC3: ['Query BRNM', 'BRNM'],
    0xC4: ['Query BRNL', 'BRNL'],
    0xC5: ['Query Memory', 'GetMem'],
}

# DALI device type 8
dali_device_type8 = {
    0xE0: ['Set Temp X-Y Coordinate', 'Set X-Y'],
    0xE2: ['Activate Colour Set point', 'Activate SetPoint'],
    0xE7: ['Set Colour Temperature Tc', 'DTRs->ColTemp'],
    0xF9: ['Query Features', 'QryFeats'],
    0xFA: ['Query Current Setpoint Colour', 'GetSetPoint'],
}
