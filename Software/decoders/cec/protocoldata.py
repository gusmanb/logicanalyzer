##
## This file is part of the libsigrokdecode project.
##
## Copyright (C) 2018 Jorge Solla Rubiales <jorgesolla@gmail.com>
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

logical_adresses = [
    'TV',
    'Recording_1',
    'Recording_2',
    'Tuner_1',
    'Playback_1',
    'AudioSystem',
    'Tuner2',
    'Tuner3',
    'Playback_2',
    'Recording_3',
    'Tuner_4',
    'Playback_3',
    'Backup_1',
    'Backup_2',
    'FreeUse',
]

# List taken from LibCEC.
opcodes = {
    0x82: 'ACTIVE_SOURCE',
    0x04: 'IMAGE_VIEW_ON',
    0x0D: 'TEXT_VIEW_ON',
    0x9D: 'INACTIVE_SOURCE',
    0x85: 'REQUEST_ACTIVE_SOURCE',
    0x80: 'ROUTING_CHANGE',
    0x81: 'ROUTING_INFORMATION',
    0x86: 'SET_STREAM_PATH',
    0x36: 'STANDBY',
    0x0B: 'RECORD_OFF',
    0x09: 'RECORD_ON',
    0x0A: 'RECORD_STATUS',
    0x0F: 'RECORD_TV_SCREEN',
    0x33: 'CLEAR_ANALOGUE_TIMER',
    0x99: 'CLEAR_DIGITAL_TIMER',
    0xA1: 'CLEAR_EXTERNAL_TIMER',
    0x34: 'SET_ANALOGUE_TIMER',
    0x97: 'SET_DIGITAL_TIMER',
    0xA2: 'SET_EXTERNAL_TIMER',
    0x67: 'SET_TIMER_PROGRAM_TITLE',
    0x43: 'TIMER_CLEARED_STATUS',
    0x35: 'TIMER_STATUS',
    0x9E: 'CEC_VERSION',
    0x9F: 'GET_CEC_VERSION',
    0x83: 'GIVE_PHYSICAL_ADDRESS',
    0x91: 'GET_MENU_LANGUAGE',
    0x84: 'REPORT_PHYSICAL_ADDRESS',
    0x32: 'SET_MENU_LANGUAGE',
    0x42: 'DECK_CONTROL',
    0x1B: 'DECK_STATUS',
    0x1A: 'GIVE_DECK_STATUS',
    0x41: 'PLAY',
    0x08: 'GIVE_TUNER_DEVICE_STATUS',
    0x92: 'SELECT_ANALOGUE_SERVICE',
    0x93: 'SELECT_DIGITAL_SERVICE',
    0x07: 'TUNER_DEVICE_STATUS',
    0x06: 'TUNER_STEP_DECREMENT',
    0x05: 'TUNER_STEP_INCREMENT',
    0x87: 'DEVICE_VENDOR_ID',
    0x8C: 'GIVE_DEVICE_VENDOR_ID',
    0x89: 'VENDOR_COMMAND',
    0xA0: 'VENDOR_COMMAND_WITH_ID',
    0x8A: 'VENDOR_REMOTE_BUTTON_DOWN',
    0x8B: 'VENDOR_REMOTE_BUTTON_UP',
    0x64: 'SET_OSD_STRING',
    0x46: 'GIVE_OSD_NAME',
    0x47: 'SET_OSD_NAME',
    0x8D: 'MENU_REQUEST',
    0x8E: 'MENU_STATUS',
    0x44: 'USER_CONTROL_PRESSED',
    0x45: 'USER_CONTROL_RELEASE',
    0x8F: 'GIVE_DEVICE_POWER_STATUS',
    0x90: 'REPORT_POWER_STATUS',
    0x00: 'FEATURE_ABORT',
    0xFF: 'ABORT',
    0x71: 'GIVE_AUDIO_STATUS',
    0x7D: 'GIVE_SYSTEM_AUDIO_MODE_STATUS',
    0x7A: 'REPORT_AUDIO_STATUS',
    0x72: 'SET_SYSTEM_AUDIO_MODE',
    0x70: 'SYSTEM_AUDIO_MODE_REQUEST',
    0x7E: 'SYSTEM_AUDIO_MODE_STATUS',
    0x9A: 'SET_AUDIO_RATE',
}

def resolve_logical_address(id_, is_initiator):
    if id_ < 0 or id_ > 0x0F:
        return 'Invalid'

    # Special handling of 0x0F.
    if id_ == 0x0F:
        return 'Unregistered' if is_initiator else 'Broadcast'

    return logical_adresses[id_]

def decode_header(header):
    src = (header & 0xF0) >> 4
    dst = (header & 0x0F)
    return (resolve_logical_address(src, 1), resolve_logical_address(dst, 0))
