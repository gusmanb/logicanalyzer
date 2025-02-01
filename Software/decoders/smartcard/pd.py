##
## Copyright (C) 2020 Sven Soltermann <sven@handyman.ch>
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
import struct
import sys
import codecs
import ctypes

class pcap_udp_pkt():
    # GSM TAP
    h  = b''

    # layer_2
    h += b'\x00\x00\x00\x00\x00\x00' # destination_mac
    h += b'\x00\x00\x00\x00\x00\x00' # source_mac
    h += b'\x08\x00' # layer_3_protocol

    # layer_3
    h += b'\x45' # version
    h += b'\x00' # DiffServField
    h += b'\xFF\xFF' # total_length
    h += b'\x2B\x0D' # Identification
    h += b'\x40\x00' # Flags
    h += b'\x40' # TTL
    h += b'\x11' # layer_4_protocol
    h += b'\x00\x00' # header_checksum
    h += b'\x7F\x00\x00\x01' # source_ip
    h += b'\x7F\x00\x00\x01' # dest_ip
    
    # layer_4
    h += b'\xcc\x46' # source_port
    h += b'\x12\x79' # dest_port
    h += b'\x00\x00' # datagram_length
    h += b'\x00\x00' # checksum

    def __init__(self, ts, data):
        self.header = bytearray(pcap_udp_pkt.h)
        self.data = b''
        self.set_timestamp(ts)
        self.set_data(data)

    def set_timestamp(self, ts):
        self.timestamp = ts

    def set_data(self, data):
        self.data = list(b'\x02\x04\x04\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00' + bytes(data));
        self.header[16:18] = struct.pack('>H', len(self.data) + 28)
        self.header[38:40] = struct.pack('>H', len(self.data) + 8)

    def packet(self):
        return bytes(self.header) + bytes(self.data)

    def record_header(self):
        # See https://wiki.wireshark.org/Development/LibpcapFileFormat.
        (secs, usecs) = self.timestamp
        h  = struct.pack('<I', secs) # TS seconds
        h += struct.pack('<I', usecs) # TS microseconds
        # No truncation, so both lengths are the same.
        h += struct.pack('<I', len(self)) # Captured len
        h += struct.pack('<I', len(self)) # Original len
        return h

    def __len__(self):
        return len(self.h) + len(self.data)

class Decoder(srd.Decoder):
    api_version = 3
    id = 'iso7816'
    name = 'ISO 7816'
    longname = 'Smartcard'
    desc = 'ISO 7816 decoder (smartcard)'
    license = 'gplv2+'
    inputs = ['logic']
    outputs = ['iso7816']
    tags = ['Embedded/industrial']
    channels = (
        {'id': 'clk', 'name': 'CLK', 'desc': 'clock'},
        {'id': 'data', 'name': 'data', 'desc': 'data'},
    )
    options = (
        {'id': 'clock_option', 'desc': 'Clock option',
            'default': 'native', 'values': ('native', 'detect', 'sample_as_clock')},
        {'id': 'protocol', 'desc': 'Protocol',
            'default': 'auto', 'values': ('auto', 'T=0', 'T=1')},
        {'id': 'starts_with_atr', 'desc': 'Starts with ATR',
            'default': 'true', 'values': ('true', 'false')},
    )
    annotations = (
        ('warnings', 'Human-readable warnings'),
        ('byte', 'Byte'),
        ('atr', 'ATR (Answer to Reset)'),
        ('pps', 'PPS (Protocol and parameters selection)'),
        ('t0', 'T=0 packet'),
        ('t1', 'T=1 packet'),
        ('t1-iblock', 'T=1 I-Block'),
        ('t1-rblock', 'T=1 R-Block'),
        ('t1-sblock', 'T=1 S-Block'),
        ('apdu', 'APDU'),
    )
    annotation_rows = (
        ('warnings', 'Warnings', (0,)),
        ('byte', 'Bytes', (1,)),
        ('type', 'Type', (2,3,4,5,)),
        ('t1', 'T=1 Decode', (6,7,8,)),
        ('apdu', 'apdu', (9,)),
    )
    binary = (
        ('pcap', 'PCAP format'),
    )

    clock_rate = {
        0: 372,
        1: 372,
        2: 558,
        3: 744,
        4: 1116,
        5: 1488,
        6: 1860,
        9: 512,
        10: 768,
        11: 1024,
        12: 1536,
        13: 2048
    }
    baud_rate = {
        0: 1,
        1: 1,
        2: 2,
        3: 4,
        4: 8,
        5: 16,
        6: 32,
        7: 64,
        8: 12,
        9: 20
    }


    def __init__(self):
        self.reset()
    
    def log(self, *args):
        print(args, file=sys.stderr)

    def reset(self):
        self.peeked_byte = None
        self.peeked_samplenum = -1
        self.wrote_pcap_header = False
        self.samplerate = None
        self.sample_as_clock = False
        self.detect_clock = False
        self.fi = self.clock_rate[0]
        self.di = self.baud_rate[0]
        self.ss = self.es = -1
        self.state = 'FIND START'
        self.bits = []
        self.clock_skip = 372
        self.lastSamplePositive = True
        self.sampleOverflowCount = 0

    def metadata(self, key, value):
        if key == srd.SRD_CONF_SAMPLERATE:
            self.samplerate = value
            if self.samplerate:
                self.secs_per_sample = float(1) / float(self.samplerate)

    def start(self):
        self.out_python = self.register(srd.OUTPUT_PYTHON)
        self.out_ann = self.register(srd.OUTPUT_ANN)
        self.out_binary = self.register(srd.OUTPUT_BINARY)
        self.sample_as_clock = self.options['clock_option'] == "sample_as_clock"
        self.detect_clock = self.options['clock_option'] == "detect"
        if self.options['starts_with_atr'] == "true":
            self.state = 'FIND START'
        else:
            self.state = 'DATA'
        if (self.options['protocol'] == "T=0"):
            self.hasT0 = True
            self.hasT1 = False
        elif (self.options['protocol'] == "T=1"):
            self.hasT0 = False
            self.hasT1 = True

    def pcap_global_header(self):
        # See https://wiki.wireshark.org/Development/LibpcapFileFormat.
        h  = b'\xd4\xc3\xb2\xa1' # Magic, indicate microsecond ts resolution
        h += b'\x02\x00'         # Major version 2
        h += b'\x04\x00'         # Minor version 4
        h += b'\x00\x00\x00\x00' # Correction vs. UTC, seconds
        h += b'\x00\x00\x00\x00' # Timestamp accuracy
        h += b'\xff\xff\x00\x00' # Max packet len
        h += b'\x01\x00\x00\x00' # Link layer
        return h

    def get_bytes(self, bits):
        byte = 0
        for bit in list(reversed(bits)):
            byte = (byte << 1) | bit
        return byte
    
    def write_pcap_header(self):
        if not self.wrote_pcap_header:
            self.put(0, 0, self.out_binary, [0, self.pcap_global_header()])
            self.wrote_pcap_header = True
    
    def ts_from_samplenum(self, sample):
        x = ctypes.c_uint32(sample).value;
        ovrflow = ctypes.c_uint32(int(self.sampleOverflowCount * 0xFFFFFFFF * self.secs_per_sample)).value
        ts = float(x) * self.secs_per_sample + ovrflow
        return (int(ts), int((ts % 1.0) * 1e6))

    def read_first_byte(self):
        self.bits = []
        self.ss = self.samplenum
        self.clock_skip = 0

        if (self.sample_as_clock):
            pins = self.wait({1: 'r'})
            self.clock_skip = self.samplenum - self.ss + 2
            self.detected_clock_skip = self.clock_skip
            self.wait({'skip': int(self.clock_skip / 3)})
            self.bits.append(0)
        elif (self.detect_clock):
            while (True):
                pins = self.wait({0: 'r'})
                self.clock_skip += 1
                if (pins[1] == 1):            
                    self.bits.append(0)
                    for c in range(int(self.clock_skip / 2)): 
                        self.wait({0: 'r'})
                    break;
            self.detected_clock_skip = self.clock_skip
        else:
            self.clock_skip = 372
            self.bits.append(0)
            for c in range(int(self.clock_skip / 2 + self.clock_skip)): 
                self.wait({0: 'r'})

        for x in range(9):
            pins = self.wait({'skip': 0})
            self.bits.append(pins[1])
            if (self.sample_as_clock):
                self.wait({'skip': self.clock_skip - 4})
            else:
                for c in range(int(self.clock_skip)): 
                    self.wait({0: 'r'})

        self.log("FIRSTBIT, clockskip:", self.clock_skip,"sample_as_clock: ", self.sample_as_clock)
        self.es = self.samplenum
        if (self.bits.count(1) % 2 != 0):
            self.log("CHKSUM ERROR: " + str(pins[1]) + "  sample: "+ str(self.samplenum))
            self.put(self.ss, self.samplenum, self.out_ann, [0, ["CHKSUM ERROR bits={bits}".format(bits=self.bits)]])
        byte = self.get_bytes(self.bits[1:9])
        self.log(self.samplenum, self.bits[1:9], " : ", "0x{:02x}".format(byte))
        self.put(self.ss, self.samplenum, self.out_ann, [1, [hex(byte)]])
        return byte

    def read_byte(self):
        if (self.samplenum < 0 and self.lastSamplePositive):
            self.lastSamplePositive = False
        if (self.lastSamplePositive == False and self.samplenum > 0 ):
            self.sampleOverflowCount += 1
            self.lastSamplePositive = True
        if (self.peeked_byte != None):
            byte =self.peeked_byte
            self.peeked_byte = None
            self.peeked_samplenum = -1
            return byte;
        self.wait({1: 'f'})
        self.sleep_cycles()
        return self.read_byte_no_wait();
    
    def peek_byte(self):
        self.wait({1: 'f'})
        self.sleep_cycles()
        self.peeked_samplenum = self.samplenum
        self.peeked_byte = self.read_byte_no_wait();
        return self.peeked_byte;

    def read_byte_no_wait(self):
        self.bits = []
        self.ss = self.samplenum
        for x in range(10):
            pins = self.wait({'skip': 0})
            #if (x != 0 and x < 9):
                #self.log("read_bit: " + str(pins[1]) + "  sample: "+ str(self.samplenum))
            self.bits.append(pins[1])
            if (self.sample_as_clock):
                self.wait({'skip': self.clock_skip - 4})
            else:
                for c in range(int(self.clock_skip)): 
                    self.wait({0: 'r'})

        self.es = self.samplenum
        if (self.bits.count(1) % 2 != 0):
            self.log(self.samplenum, "CHKSUM ERROR: ", pins[1], "bits: ", self.bits)
            self.put(self.ss, self.samplenum, self.out_ann, [0, ["CHKSUM ERROR bits={bits}".format(bits=self.bits)]])
        byte = self.get_bytes(self.bits[1:9])
        self.log(self.samplenum, self.bits[1:9], " : ", "0x{:02x}".format(byte))
        self.put(self.ss, self.samplenum, self.out_ann, [1, [hex(byte)]])
        return byte


    def sleep_cycles(self):
        if (self.sample_as_clock):
            self.wait({'skip': int(self.clock_skip / 3)})
        else:
            for c in range(int(self.clock_skip / 3)): 
                self.wait({0: 'r'})

    def handle_atr(self, pins):
        
        atr_start = self.samplenum;

        self.log("START ATR:", self.samplenum);
        self.state = 'ATR'
        
        tA = []
        tB = []
        tC = []
        tD = []
        historicalBytes = []
        self.ATR = []

        if (self.peeked_byte != None):
            atr_start = self.peeked_samplenum
            byte = self.read_byte()
        else:
            byte = self.read_first_byte()
        self.ATR.append(byte)

        t0 = self.read_byte()
        self.ATR.append(t0)

        firstT0 = t0

        self.hasT0 = False
        self.hasT1 = False
        self.hasT15 = False
        while (firstT0 & 0b11110000):
            if (firstT0 & 0b00010000):
                byte = self.read_byte()
                tA.append(byte)
                self.ATR.append(byte)
            if (firstT0 & 0b00100000):
                byte = self.read_byte()
                tB.append(byte)
                self.ATR.append(byte)
            if (firstT0 & 0b01000000):
                byte = self.read_byte()
                tC.append(byte)
                self.ATR.append(byte)
            if (firstT0 & 0b10000000):
                byte = self.read_byte()
                if ((byte & 0x0F) == 0):
                    self.hasT0 = True
                elif ((byte & 0x0F) == 1):
                    self.hasT1 = True
                elif ((byte & 0x0F) == 15):
                    self.hasT15 = True
                else:
                    self.log("Invalid Protocol in ATR: ", "T=",(byte & 0x0F))    
                    self.put(atr_start, self.samplenum, self.out_ann, [0, ["Invalid Protocol in ATR T={protocol}".format(protocol=(byte & 0x0F))]])
                tD.append(byte)
                self.ATR.append(byte)
                firstT0 = byte
                self.log("TD("+str(len(tD))+"): ", hex(firstT0), "T=",(byte & 0x0F))
            else:
                firstT0 = 0;

        for _ in range(0, t0 & 0x0F):
            byte = self.read_byte()
            self.ATR.append(byte)
        
        if (self.hasT1 == False and self.hasT0 == False):
            self.hasT0 = True

        if (self.hasT1 == True or self.hasT15):
            byte = self.read_byte()
            self.ATR.append(byte)
            xor = 0
            for i in range(1, len(self.ATR)): xor = xor ^ self.ATR[i]
            if (xor != 0):
                self.put(atr_start, self.samplenum, self.out_ann, [0, ["Invalid TCK in ATR, got={tck:02x} expected={xor:02x}".format(tck=byte,xor=xor)]])
                self.log("Invalid TCK in ATR", hex(byte), hex(xor))    

        self.put(atr_start, self.samplenum, self.out_ann, [2, ["ATR", "ATR={atr}".format(atr=codecs.encode(bytes(self.ATR), 'hex'))]])
        self.put(atr_start, self.samplenum, self.out_python, [0, self.ATR])

        self.log("ENDATR", codecs.encode(bytes(self.ATR), 'hex'))
        self.state = 'DATA'

        if (self.options['protocol'] == "T=0"):
            self.hasT0 = True
            self.hasT1 = False
        elif (self.options['protocol'] == "T=1"):
            self.hasT0 = False
            self.hasT1 = True

    def t1_parse_block(self, es):
        packet = []
        lrc = 0;
        nad = self.read_byte()
        lrc = lrc ^ nad
        self.put(es, self.samplenum, self.out_ann, [1, "NAD:" + hex(nad)])
        sad = nad & 0x70
        dad = nad & 0x07
        self.log("T=1 NAD=", hex(nad), "SAD=", hex(sad), "DAD=", hex(dad))
        
        pcb = self.read_byte()
        lrc = lrc ^ pcb
        
        isSBlock = False
        isRBlock = False
        isIBlock = False
        if (pcb & 0b11000000 == 0b11000000):
            # S-Block
            isSBlock = True
            self.put(es, self.samplenum, self.out_ann, [3, "PCB S " + hex(pcb)])
            self.log("PCB S-Block", hex(pcb & 0b00111111))
        elif (pcb & 0b10000000 == 0b10000000):
            # R-Block
            isRBlock = True
            self.put(es, self.samplenum, self.out_ann, [3, "PCB R " + hex(pcb)])
            self.log("PCB R-Block", hex(pcb & 0b00111111))
        else:
            # I-Block
            isIBlock = True
            self.put(es, self.samplenum, self.out_ann, [3, "PCB I " + hex(pcb)])
            self.log("PCB I-Block", hex(pcb))

        bLen = self.read_byte()
        lrc = lrc ^ bLen
        if (bLen > 0):
            for _ in range(bLen): 
                byte = self.read_byte()
                lrc = lrc ^ byte
                if (isIBlock): packet.append(byte)
        
        # CRC to implement
        bLrc =  self.read_byte()
        lrc = lrc ^ bLrc

        if (lrc != 0):
            self.put(es, self.samplenum, self.out_ann, [0, ["Invalid checksum on T=1 block, , got={got:02x} expected={expected:02x}".format(got=lrc,expected=bLrc)]])
            self.log("Invalid checksum on T=1 block", hex(lrc), hex(bLrc))

        self.log("block_content", codecs.encode(bytes(packet), 'hex'))

        if (isIBlock):
            self.put(es, self.samplenum, self.out_ann, [6, ["I-Block", "I-Block len={len} isMultiBlock={multi}".format(len=bLen,multi=(pcb & 0b00100000 > 0))]])
        if (isRBlock):
            self.put(es, self.samplenum, self.out_ann, [7, ["R-Block", "R-Block flag={flag:02x}".format(flag=pcb & 0b00111111)]])
        if (isSBlock):
            self.put(es, self.samplenum, self.out_ann, [8, ["S-Block", "S-Block flag={flag:02x}".format(flag=pcb & 0b00111111)]])

        if (isIBlock and pcb & 0b00100000): # m-flag
            self.log("T=1 Multiblock flag", hex(pcb))
            while (True):
                isIBlock2,packet2 = self.t1_parse_block(self.samplenum)
                if (isIBlock2):
                    packet = packet + packet2
                    break
        

        return isIBlock,packet;
    
    def handle_pps(self):
        lrc = 0
        ss = self.peeked_samplenum
        pps = self.read_byte()
        pps0 = self.read_byte()
        pps1 = 0; pps2 = 0; pps3 = 0
        if (pps0 & 0b00010000):
            pps1 = self.read_byte()
            lrc = lrc ^ pps1
        if (pps0 & 0b00100000):
            pps2 = self.read_byte()
            lrc = lrc ^ pps2
        if (pps0 & 0b01000000):
            pps3 = self.read_byte()
            lrc = lrc ^ pps3
        pck = self.read_byte()
        lrc = lrc ^ pps ^ pps0 ^ pck
        if (lrc != 0):
            self.put(ss, self.samplenum, self.out_ann, [0, ["INVALID Checksum on PPS Request, got={got:02x} expected={expected:02x}".format(got=pck,expected=(lrc ^ pps ^ pps0))]])
            self.log("INVALID Checksum on PPS Request", hex(lrc))
        
        r_lrc = 0
        r_pps = self.read_byte()
        r_pps1 = 0; r_pps2 = 0; r_pps3 = 0
        if (r_pps != 0xFF):
            self.put(ss, self.samplenum, self.out_ann, [0, ["PPS Request not confirmed"]])
            self.log("PPS Request not confirmed", r_pps)
        r_pps0 = self.read_byte()
        if (r_pps0 & 0b00010000):
            r_pps1 = self.read_byte()
            r_lrc = r_lrc ^ r_pps1
        if (r_pps0 & 0b00100000):
            r_pps2 = self.read_byte()
            r_lrc = r_lrc ^ r_pps2
        if (r_pps0 & 0b01000000):
            r_pps3 = self.read_byte()
            r_lrc = r_lrc ^ r_pps3
        r_pck = self.read_byte()
        r_lrc = r_lrc ^ r_pps ^ r_pps0 ^ r_pck
        if (r_lrc != 0):
            self.put(ss, self.samplenum, self.out_ann, [0, ["INVALID Checksum on PPS Response, got={got:02x} expected={expected:02x}".format(got=r_pck,expected=(r_lrc ^ r_pps ^ r_pps0))]])
            self.log("INVALID Checksum on PPS Response", hex(r_lrc))
        
        if (pps0 == r_pps0 and pps1 == r_pps1 and pps2 == r_pps2 and pps3 == r_pps3):
            if (self.detect_clock or self.sample_as_clock):
                tmp_fi = self.clock_rate[int(pps1 >> 4)]
                tmp_di = self.baud_rate[int(pps1 & 0x0F)]
                tmp_clock_skip = int(tmp_fi / tmp_di)                
                self.log("Received PPS change: FI", tmp_fi, "DI", tmp_di, "clock_skip", tmp_clock_skip)
                self.clock_skip = int(tmp_clock_skip * self.detected_clock_skip / 372)
                self.fi = tmp_fi
                self.di = tmp_di
                self.log("PPS Success new settings (calculated): FI", self.fi, "DI", self.di, "clock_skip", self.clock_skip)
            else:
                self.fi = self.clock_rate[int(pps1 >> 4)]
                self.di = self.baud_rate[int(pps1 & 0x0F)]
                self.clock_skip = int(self.fi / self.di)
                self.log("PPS Success new settings: FI", self.fi, "DI", self.di, "clock_skip", self.clock_skip)
        else:
            self.log("INVALID PPS. Request & Response not matching.", hex(r_lrc))       
            self.put(ss, self.samplenum, self.out_ann, [0, ["INVALID PPS. Request & Response not matching"]])
        self.put(ss, self.samplenum, self.out_ann, [3, ["PPS", "PPS DI={di} FI={fi} clock_skip={clock_skip}".format(di=self.di,fi=self.fi,clock_skip=self.clock_skip)]])


    def decode(self):
        self.write_pcap_header();
        while True:
            # State machine.
            if self.state == 'FIND START':
                self.wait({1: 'h'})
                self.handle_atr(self.wait({1: 'f'}))
            elif self.state == 'DATA':
                packet = [];

                firstByte = self.peek_byte();
                if (firstByte == 0xFF): # PPS Request
                    self.handle_pps();
                    continue;
                elif (firstByte == 0x3b): # Probably ATR
                    self.handle_atr(self.wait({'skip': 0}))
                    continue;

                es = self.peeked_samplenum;
                if (self.hasT0):
                    bClass = self.read_byte()
                    packet.append(bClass); # class
                    bIns = self.read_byte();
                    packet.append(bIns); # instruction
                    packet.append(self.read_byte()); # param1
                    packet.append(self.read_byte()); # param2
                    dataLen = self.read_byte();
                    self.log("DATALEN: ", dataLen)
                    packet.append(dataLen); # param3             
                    procedureByte = self.read_byte();
                    if (procedureByte == bIns):
                        for _ in range(0,dataLen):
                            packet.append(self.read_byte()); # payload
                        packet.append(self.read_byte()); # status0
                        packet.append(self.read_byte()); # status1
                    elif (procedureByte == 0x60):
                        packet.append(procedureByte); # status0
                        packet.append(self.read_byte()); # status1
                    elif (procedureByte & 0xF0 == 0x60 or procedureByte & 0xF0 == 0x90):
                        packet.append(procedureByte); # status0
                        packet.append(self.read_byte()); # status1
                    else:
                        self.put(es, self.samplenum, self.out_ann, [0, ["INVALID Procedure Byte"]])
                        self.log("INVALID Procedure Byte", hex(procedureByte))
                    self.put(es, self.samplenum, self.out_ann, [4, ["T=0"]])
                    self.put(es, self.samplenum, self.out_ann, [9, ["APDU", "APDU cls={cls:02x} ins={ins:02x}".format(cls=bClass,ins=bIns), "APDU cls={cls:02x} ins={ins:02x} p1={p1:02x} p2={p2:02x} p3={p3:02x} len={len} status={sw1:02x}{sw2:02x}".format(cls=bClass,ins=bIns,p1=packet[2],p2=packet[3],p3=packet[4],len=dataLen,sw1=packet[-2],sw2=packet[-1])]])
                elif (self.hasT1):
                    isIBlock,packet = self.t1_parse_block(es)
                    if (isIBlock):
                        while (True):
                            isIBlock,packet2 = self.t1_parse_block(es)
                            if (isIBlock):
                                packet = packet + packet2
                                break
                    self.put(es, self.samplenum, self.out_ann, [4, ["T=1", "T=1 (reassembled)"]])
                    if (len(packet) >= 8):
                        self.put(es, self.samplenum, self.out_ann, [9, ["APDU", "APDU cls={cls:02x} ins={ins:02x}".format(cls=packet[0],ins=packet[1]), "APDU cls={cls:02x} ins={ins:02x} p1={p1:02x} p2={p2:02x} p3={p3:02x} len={len} status={sw1:02x}{sw2:02x}".format(cls=packet[0],ins=packet[1],p1=packet[2],p2=packet[3],p3=packet[4],len=len(packet) - 7,sw1=packet[-2],sw2=packet[-1])]])


                if (len(packet) > 0):
                    ts = self.ts_from_samplenum(es)
                    pkt = pcap_udp_pkt(ts, packet)
                    self.put(es, self.samplenum, self.out_binary, [0, pkt.record_header()])
                    self.put(es, self.samplenum, self.out_binary, [0, pkt.packet()])
                    
                self.log("PACKETEND", codecs.encode(bytes(packet), 'hex'))
            else:    
                break;
