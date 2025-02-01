##
## This file is part of the libsigrokdecode project.
##
## Copyright (C) 2018 Steve R <steversig@virginmedia.com>
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

# Most of the info here comes from "434MHz RF Protocol Descriptions for
# Wireless Weather Sensors - October 2015" Known Sensor ID Codes - p25.

# Format is 4 hex digit ID code followed by a LIST of models that use that
# ID and the type of sensor.
# SensorID is used as the hash in a Python hash table, so it must be upper case.
# The type of sensor is used to decode and display readings in the L2 decode,
# it's case-sensitive.
# Be very careful with the formatting ' [] and commas.

sensor = {
#   'SensorID': [['model1', 'model2'], 'type'],
    '1984': [['WGR800'], 'Wind'], # The newer anemometer with no temperature/RH sensor.
    '1994': [['WGR800'], 'Wind'], # The original anemometer which included a temperature/RH sensor.
    '1A2D': [['THGR228N'], 'Temp_Hum1'],
    '1A3D': [['THGR918'], ''],
    '1D20': [['THGN123N', 'THGR122NX', 'THGN123N', 'THGR228N'], 'Temp_Hum'],
    '1D30': [['THGN500', 'THGN132N'], ''],
    '2914': [['PCR800'], 'Rain'],
    '2A19': [['PCR800'], 'Rain1'],
    '2A1D': [['RGR918'], 'Rain'],
    '2D10': [['RGR968', 'PGR968 '], 'Rain1'],
    '3A0D': [['STR918', 'WGR918'], 'Wind'],
    '5A5D': [['BTHR918'], ''],
    '5A6D': [['BTHR918N'], 'Temp_Hum_Baro'],
    '5D53': [['BTHGN129'], 'Baro'],
    '5D60': [['BTHR968'], 'Temp_Hum_Baro'],
    'C844': [['THWR800'], 'Temp'],
    'CC13': [['RTGR328N'], 'Temp_Hum'],
    'CC23': [['THGR328N'], 'Temp_Hum'],
    'CD39': [['RTHR328N'], 'Temp'],
    'D874': [['UVN800'], 'UV1'],
    'EA4C': [['THWR288A'], 'Temp'],
    'EC40': [['THN132N', 'THR238NF'], 'Temp'],
    'EC70': [['UVR128'], 'UV'],
    'F824': [['THGN800', 'THGN801', 'THGR810'], 'Temp_Hum'],
    'F8B4': [['THGR810'], 'Temp_Hum'],
#    '': ['PSR01'], '', ''],
#    '': ['RTGR328NA'], '', ''],
#    '': ['THC268'], '', ''],
#    '': ['THWR288A-JD'], '', ''],
#    '': ['THGR268'], '', ''],
#    '': ['THR268'], '', ''],
}

# The sensor checksum exceptions are used to calculate the right checksum for
# sensors that don't follow the v1, v2.1 and v3 methods. For instance a v2.1
# sensor that has a v3 checksum.
sensor_checksum = {
#   'SensorID': ['checksum_method', 'comment'],
    '1D20': ['v3', 'THGR228N'],
    '5D60': ['v3', 'BTHR918N'],
    'EC40': ['v3', 'THN132N'],
}

dir_table = ['N', 'NNE', 'NE', 'ENE', 'E', 'ESE', 'SE', 'SSE', 'S', 'SSW', 'SW', 'WSW', 'W', 'WNW', 'NW', 'NNW', 'N']
