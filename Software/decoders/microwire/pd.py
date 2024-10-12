##
## This file is part of the libsigrokdecode project.
##
## Copyright (C) 2017 Kevin Redon <kingkevin@cuvoodoo.info>
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

import sigrokdecode as srd
from collections import namedtuple

'''
OUTPUT_PYTHON format:

Packet:
[namedtuple('ss': bit start sample number,
  'es': bit end sample number,
  'si': SI bit,
  'so': SO bit,
 ), ...]

Since address and word size are variable, a list of all bits in each packet
need to be output. Since Microwire is a synchronous protocol with separate
input and output lines (SI and SO) they are provided together, but because
Microwire is half-duplex only the SI or SO bits will be considered at once.
To be able to annotate correctly the instructions formed by the bit, the start
and end sample number of each bit (pair of SI/SO bit) are provided.
'''

PyPacket = namedtuple('PyPacket', 'ss es si so')
Packet = namedtuple('Packet', 'samplenum matched cs sk si so')

class Decoder(srd.Decoder):
    api_version = 3
    id = 'microwire'
    name = 'Microwire'
    longname = 'Microwire'
    desc = '3-wire, half-duplex, synchronous serial bus.'
    license = 'gplv2+'
    inputs = ['logic']
    outputs = ['microwire']
    tags = ['Embedded/industrial']
    channels = (
        {'id': 'cs', 'name': 'CS', 'desc': 'Chip select'},
        {'id': 'sk', 'name': 'SK', 'desc': 'Clock'},
        {'id': 'si', 'name': 'SI', 'desc': 'Slave in'},
        {'id': 'so', 'name': 'SO', 'desc': 'Slave out'},
    )
    annotations = (
        ('start-bit', 'Start bit'),
        ('si-bit', 'SI bit'),
        ('so-bit', 'SO bit'),
        ('status-check-ready', 'Status check ready'),
        ('status-check-busy', 'Status check busy'),
        ('warning', 'Warning'),
    )
    annotation_rows = (
        ('si-bits', 'SI bits', (0, 1)),
        ('so-bits', 'SO bits', (2,)),
        ('status', 'Status', (3, 4)),
        ('warnings', 'Warnings', (5,)),
    )

    def __init__(self):
        self.reset()

    def reset(self):
        pass

    def start(self):
        self.out_python = self.register(srd.OUTPUT_PYTHON)
        self.out_ann = self.register(srd.OUTPUT_ANN)

    def decode(self):
        while True:
            # Wait for slave to be selected on rising CS.
            cs, sk, si, so = self.wait({0: 'r'})
            if sk:
                self.put(self.samplenum, self.samplenum, self.out_ann,
                     [5, ['Clock should be low on start',
                     'Clock high on start', 'Clock high', 'SK high']])
                sk = 0 # Enforce correct state for correct clock handling.
                # Because we don't know if this is bit communication or a
                # status check we have to collect the SI and SO values on SK
                # edges while the chip is selected and figure out afterwards.
            packet = []
            while cs:
                # Save change.
                packet.append(Packet(self.samplenum, self.matched, cs, sk, si, so))
                edge = 'r' if sk == 0 else 'f'
                cs, sk, si, so = self.wait([{0: 'l'}, {1: edge}, {3: 'e'}])
            # Save last change.
            packet.append(Packet(self.samplenum, self.matched, cs, sk, si, so))

            # Figure out if this is a status check.
            # Either there is no clock or no start bit (on first rising edge).
            status_check = True
            for change in packet:
                # Get first clock rising edge.
                if len(change.matched) > 1 and change.matched[1] and change.sk:
                    if change.si:
                        status_check = False
                    break

            # The packet is for a status check.
            # SO low = busy, SO high = ready.
            # The SO signal might be noisy in the beginning because it starts
            # in high impedance.
            if status_check:
                start_samplenum = packet[0].samplenum
                bit_so = packet[0].so
                # Check for SO edges.
                for change in packet:
                    if len(change.matched) > 2 and change.matched[2]:
                        if bit_so == 0 and change.so:
                            # Rising edge Busy -> Ready.
                            self.put(start_samplenum, change.samplenum,
                                     self.out_ann, [4, ['Busy', 'B']])
                        start_samplenum = change.samplenum
                        bit_so = change.so
                # Put last state.
                if bit_so == 0:
                    self.put(start_samplenum, packet[-1].samplenum,
                             self.out_ann, [4, ['Busy', 'B']])
                else:
                    self.put(start_samplenum, packet[-1].samplenum,
                             self.out_ann, [3, ['Ready', 'R']])
            else:
                # Bit communication.
                # Since the slave samples SI on clock rising edge we do the
                # same. Because the slave changes SO on clock rising edge we
                # sample on the falling edge.
                bit_start = 0 # Rising clock sample of bit start.
                bit_si = 0 # SI value at rising clock edge.
                bit_so = 0 # SO value at falling clock edge.
                start_bit = True # Start bit incoming (first bit).
                pydata = [] # Python output data.
                for change in packet:
                    if len(change.matched) > 1 and change.matched[1]:
                        # Clock edge.
                        if change.sk: # Rising clock edge.
                            if bit_start > 0: # Bit completed.
                                if start_bit:
                                    if bit_si == 0: # Start bit missing.
                                        self.put(bit_start, change.samplenum,
                                                 self.out_ann,
                                                 [5, ['Start bit not high',
                                                 'Start bit low']])
                                    else:
                                        self.put(bit_start, change.samplenum,
                                                 self.out_ann,
                                                 [0, ['Start bit', 'S']])
                                    start_bit = False
                                else:
                                    self.put(bit_start, change.samplenum,
                                             self.out_ann,
                                             [1, ['SI bit: %d' % bit_si,
                                                  'SI: %d' % bit_si,
                                                  '%d' % bit_si]])
                                    self.put(bit_start, change.samplenum,
                                             self.out_ann,
                                             [2, ['SO bit: %d' % bit_so,
                                                  'SO: %d' % bit_so,
                                                  '%d' % bit_so]])
                                    pydata.append(PyPacket(bit_start,
                                        change.samplenum, bit_si, bit_so))
                            bit_start = change.samplenum
                            bit_si = change.si
                        else: # Falling clock edge.
                            bit_so = change.so
                    elif change.matched[0] and \
                                    change.cs == 0 and change.sk == 0:
                        # End of packet.
                        self.put(bit_start, change.samplenum, self.out_ann,
                                 [1, ['SI bit: %d' % bit_si,
                                      'SI: %d' % bit_si, '%d' % bit_si]])
                        self.put(bit_start, change.samplenum, self.out_ann,
                                 [2, ['SO bit: %d' % bit_so,
                                      'SO: %d' % bit_so, '%d' % bit_so]])
                        pydata.append(PyPacket(bit_start, change.samplenum,
                                      bit_si, bit_so))
                self.put(packet[0].samplenum, packet[len(packet) - 1].samplenum,
                         self.out_python, pydata)
