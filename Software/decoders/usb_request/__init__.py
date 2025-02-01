##
## This file is part of the libsigrokdecode project.
##
## Copyright (C) 2015 Stefan Brüns <stefan.bruens@rwth-aachen.de>
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
This decoder stacks on top of the 'usb_packet' PD and decodes the USB
(low-speed and full-speed) transactions.

Transactions and requests are tracked per device address and endpoint.

Tracking of CONTROL requests is quite accurate, as these always start with
a SETUP token and are completed by an IN or OUT transaction, the status
packet. All transactions during the DATA stage are combined.

For BULK and INTERRUPT requests, each transaction starts with an IN or OUT
request, and is considered completed after the first transaction containing
data has been ACKed. Normally a request is only completed after a short or
zero length packet, but this would require knowledge about the max packet
size of an endpoint.

All INTERRUPT requests are treated as BULK requests, as on the link layer
both are identical.

The PCAP binary output contains 'SUBMIT' and 'COMPLETE' records. For
CONTROL request, the SUBMIT contains the SETUP request, the data is
either contained in the SUBMIT (Host-to-Device) or the COMPLETE
(Device-to-Host) record.

Details:
https://en.wikipedia.org/wiki/USB
http://www.usb.org/developers/docs/
'''

from .pd import Decoder
