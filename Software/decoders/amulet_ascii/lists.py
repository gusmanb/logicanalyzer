##
## This file is part of the libsigrokdecode project.
##
## Copyright (C) 2019 Vesa-Pekka Palmu <vpalmu@depili.fi>
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

from collections import OrderedDict

# OrderedDict which maps command IDs to their names and descriptions.
cmds = OrderedDict([
    (0xA0, ('PAGE', 'Jump to page')),
    (0xD0, ('GBV', 'Get byte variable')),
    (0xD1, ('GWV', 'Get word variable')),
    (0xD2, ('GSV', 'Get string variable')),
    (0xD3, ('GLV', 'Get label variable')),
    (0xD4, ('GRPC', 'Get RPC buffer')),
    (0xD5, ('SBV', 'Set byte variable')),
    (0xD6, ('SWV', 'Set word variable')),
    (0xD7, ('SSV', 'Set string variable')),
    (0xD8, ('RPC', 'Invoke RPC')),
    (0xD9, ('LINE', 'Draw line')),
    (0xDA, ('RECT', 'Draw rectangle')),
    (0xDB, ('FRECT', 'Draw filled rectangle')),
    (0xDC, ('PIXEL', 'Draw pixel')),
    (0xDD, ('GBVA', 'Get byte variable array')),
    (0xDE, ('GWVA', 'Get word variable array')),
    (0xDF, ('SBVA', 'Set byte variable array')),
    (0xE0, ('GBVR', 'Get byte variable reply')),
    (0xE1, ('GWVR', 'Get word variable reply')),
    (0xE2, ('GSVR', 'Get string variable reply')),
    (0xE3, ('GLVR', 'Get label variable reply')),
    (0xE4, ('GRPCR', 'Get RPC buffer reply')),
    (0xE5, ('SBVR', 'Set byte variable reply')),
    (0xE6, ('SWVR', 'Set word variable reply')),
    (0xE7, ('SSVR', 'Set string variable reply')),
    (0xE8, ('RPCR', 'Invoke RPC reply')),
    (0xE9, ('LINER', 'Draw line reply')),
    (0xEA, ('RECTR', 'Draw rectangle')),
    (0xEB, ('FRECTR', 'Draw filled rectangle reply')),
    (0xEC, ('PIXELR', 'Draw pixel reply')),
    (0xED, ('GBVAR', 'Get byte variable array reply')),
    (0xEE, ('GWVAR', 'Get word variable array reply')),
    (0xEF, ('SBVAR', 'Set byte variable array reply')),
    (0xF0, ('ACK', 'Acknowledgment')),
    (0xF1, ('NACK', 'Negative acknowledgment')),
    (0xF2, ('SWVA', 'Set word variable array')),
    (0xF3, ('SWVAR', 'Set word variable array reply')),
    (0xF4, ('GCV', 'Get color variable')),
    (0xF5, ('GCVR', 'Get color variable reply')),
    (0xF6, ('SCV', 'Set color variable')),
    (0xF7, ('SCVR', 'Set color variable reply')),
])

cmds_with_high_bytes = [
    0xA0, # PAGE - Page change
    0xD7, # SVV - Set string variable
    0xE7, # SVVR - Set string variable reply
    0xE2, # GSVR - Get string variable reply
    0xE3, # GLVR - Get label variable reply
]
