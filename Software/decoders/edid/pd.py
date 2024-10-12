##
## This file is part of the libsigrokdecode project.
##
## Copyright (C) 2012 Bert Vermeulen <bert@biot.com>
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

# TODO:
#    - EDID < 1.3
#    - add short annotations
#    - Signal level standard field in basic display parameters block
#    - Additional color point descriptors
#    - Additional standard timing descriptors
#    - Extensions

import sigrokdecode as srd
from common.srdhelper import SrdIntEnum
import os

St = SrdIntEnum.from_str('St', 'OFFSET EXTENSIONS HEADER EDID')

EDID_HEADER = [0x00, 0xff, 0xff, 0xff, 0xff, 0xff, 0xff, 0x00]
OFF_VENDOR = 8
OFF_VERSION = 18
OFF_BASIC = 20
OFF_CHROM = 25
OFF_EST_TIMING = 35
OFF_STD_TIMING = 38
OFF_DET_TIMING = 54
OFF_NUM_EXT = 126
OFF_CHECKSUM = 127

# Pre-EDID established timing modes
est_modes = [
    '720x400@70Hz',
    '720x400@88Hz',
    '640x480@60Hz',
    '640x480@67Hz',
    '640x480@72Hz',
    '640x480@75Hz',
    '800x600@56Hz',
    '800x600@60Hz',
    '800x600@72Hz',
    '800x600@75Hz',
    '832x624@75Hz',
    '1024x768@87Hz(i)',
    '1024x768@60Hz',
    '1024x768@70Hz',
    '1024x768@75Hz',
    '1280x1024@75Hz',
    '1152x870@75Hz',
]

# X:Y display aspect ratios, as used in standard timing modes
xy_ratio = [
    (16, 10),
    (4, 3),
    (5, 4),
    (16, 9),
]

# Annotation classes
ANN_FIELDS = 0
ANN_SECTIONS = 1

class Decoder(srd.Decoder):
    api_version = 3
    id = 'edid'
    name = 'EDID'
    longname = 'Extended Display Identification Data'
    desc = 'Data structure describing display device capabilities.'
    license = 'gplv3+'
    inputs = ['i2c']
    outputs = []
    tags = ['Display', 'Memory', 'PC']
    annotations = (
        ('field', 'Field'),
        ('section', 'Section'),
    )
    annotation_rows = (
        ('fields', 'Fields', (0,)),
        ('sections', 'Sections', (1,)),
    )

    def __init__(self):
        self.reset()

    def reset(self):
        self.state = None
        # Received data items, used as an index into samplenum/data
        self.cnt = 0
        # Start/end sample numbers per data item
        self.sn = []
        # Received data
        self.cache = []
        # Random read offset
        self.offset = 0
        # Extensions
        self.extension = 0
        self.ext_sn = [[]]
        self.ext_cache = [[]]

    def start(self):
        self.out_ann = self.register(srd.OUTPUT_ANN)

    def decode(self, ss, es, data):
        cmd, data = data

        if cmd == 'ADDRESS WRITE' and data == 0x50:
            self.state = St.OFFSET
            self.ss = ss
            return

        if cmd == 'ADDRESS READ' and data == 0x50:
            if self.extension > 0:
                self.state = St.EXTENSIONS
                s = str(self.extension)
                t = ["Extension: " + s, "X: " + s, s]
            else:
                self.state = St.HEADER
                t = ["EDID"]
            self.put(ss, es, self.out_ann, [ANN_SECTIONS, t])
            return

        if cmd == 'DATA WRITE' and self.state == St.OFFSET:
            self.offset = data
            self.extension = self.offset // 128
            self.cnt = self.offset % 128
            if self.extension > 0:
                ext = self.extension - 1
                l = len(self.ext_sn[ext])
                # Truncate or extend to self.cnt.
                self.sn = self.ext_sn[ext][0:self.cnt] + [0] * max(0, self.cnt - l)
                self.cache = self.ext_cache[ext][0:self.cnt] + [0] * max(0, self.cnt - l)
            else:
                l = len(self.sn)
                self.sn = self.sn[0:self.cnt] + [0] * max(0, self.cnt - l)
                self.cache = self.cache[0:self.cnt] + [0] * max(0, self.cnt - l)
            ss = self.ss if self.ss else ss
            s = str(data)
            t = ["Offset: " + s, "O: " + s, s]
            self.put(ss, es, self.out_ann, [ANN_SECTIONS, t])
            return

        # We only care about actual data bytes that are read (for now).
        if cmd != 'DATA READ':
            return

        self.cnt += 1
        if self.extension > 0:
            self.ext_sn[self.extension - 1].append([ss, es])
            self.ext_cache[self.extension - 1].append(data)
        else:
            self.sn.append([ss, es])
            self.cache.append(data)

        if self.state is None or self.state == St.HEADER:
            # Wait for the EDID header
            if self.cnt >= OFF_VENDOR:
                if self.cache[-8:] == EDID_HEADER:
                    # Throw away any garbage before the header
                    self.sn = self.sn[-8:]
                    self.cache = self.cache[-8:]
                    self.cnt = 8
                    self.state = St.EDID
                    self.put(self.sn[0][0], es, self.out_ann,
                            [ANN_SECTIONS, ['Header']])
                    self.put(self.sn[0][0], es, self.out_ann,
                            [ANN_FIELDS, ['Header pattern']])
        elif self.state == St.EDID:
            if self.cnt == OFF_VERSION:
                self.decode_vid(-10)
                self.decode_pid(-8)
                self.decode_serial(-6)
                self.decode_mfrdate(-2)
                self.put(self.sn[OFF_VENDOR][0], es, self.out_ann,
                        [ANN_SECTIONS, ['Vendor/product']])
            elif self.cnt == OFF_BASIC:
                self.put(self.sn[OFF_VERSION][0], es, self.out_ann,
                        [ANN_SECTIONS, ['EDID Version']])
                self.put(self.sn[OFF_VERSION][0], self.sn[OFF_VERSION][1],
                        self.out_ann, [ANN_FIELDS,
                            ['Version %d' % self.cache[-2]]])
                self.put(self.sn[OFF_VERSION+1][0], self.sn[OFF_VERSION+1][1],
                        self.out_ann, [ANN_FIELDS,
                            ['Revision %d' % self.cache[-1]]])
            elif self.cnt == OFF_CHROM:
                self.put(self.sn[OFF_BASIC][0], es, self.out_ann,
                        [ANN_SECTIONS, ['Basic display']])
                self.decode_basicdisplay(-5)
            elif self.cnt == OFF_EST_TIMING:
                self.put(self.sn[OFF_CHROM][0], es, self.out_ann,
                        [ANN_SECTIONS, ['Color characteristics']])
                self.decode_chromaticity(-10)
            elif self.cnt == OFF_STD_TIMING:
                self.put(self.sn[OFF_EST_TIMING][0], es, self.out_ann,
                        [ANN_SECTIONS, ['Established timings']])
                self.decode_est_timing(-3)
            elif self.cnt == OFF_DET_TIMING:
                self.put(self.sn[OFF_STD_TIMING][0], es, self.out_ann,
                        [ANN_SECTIONS, ['Standard timings']])
                self.decode_std_timing(self.cnt - 16)
            elif self.cnt == OFF_NUM_EXT:
                self.decode_descriptors(-72)
            elif self.cnt == OFF_CHECKSUM:
                self.put(ss, es, self.out_ann,
                    [0, ['Extensions present: %d' % self.cache[self.cnt-1]]])
            elif self.cnt == OFF_CHECKSUM+1:
                checksum = 0
                for i in range(128):
                    checksum += self.cache[i]
                if checksum % 256 == 0:
                    csstr = 'OK'
                else:
                    csstr = 'WRONG!'
                self.put(ss, es, self.out_ann, [0, ['Checksum: %d (%s)' % (
                         self.cache[self.cnt-1], csstr)]])
                self.state = St.EXTENSIONS

        elif self.state == St.EXTENSIONS:
            cache = self.ext_cache[self.extension - 1]
            sn = self.ext_sn[self.extension - 1]
            v = cache[self.cnt - 1]
            if self.cnt == 1:
                if v == 2:
                    self.put(ss, es, self.out_ann, [1, ['Extensions Tag', 'Tag']])
                else:
                    self.put(ss, es, self.out_ann, [1, ['Bad Tag']])
            elif self.cnt == 2:
                self.put(ss, es, self.out_ann, [1, ['Version']])
                self.put(ss, es, self.out_ann, [0, [str(v)]])
            elif self.cnt == 3:
                self.put(ss, es, self.out_ann, [1, ['DTD offset']])
                self.put(ss, es, self.out_ann, [0, [str(v)]])
            elif self.cnt == 4:
                self.put(ss, es, self.out_ann, [1, ['Format support | DTD count']])
                support = "Underscan: {0}, {1} Audio, YCbCr: {2}".format(
                        "yes" if v & 0x80 else "no",
                        "Basic" if v & 0x40 else "No",
                        ["None", "422", "444", "422+444"][(v & 0x30) >> 4])
                self.put(ss, es, self.out_ann, [0, ['{0}, DTDs: {1}'.format(support, v & 0xf)]])
            elif self.cnt <= cache[2]:
                if self.cnt == cache[2]:
                    self.put(sn[4][0], es, self.out_ann, [1, ['Data block collection']])
                    self.decode_data_block_collection(cache[4:], sn[4:])
            elif (self.cnt - cache[2]) % 18 == 0:
                n = (self.cnt - cache[2]) / 18
                if n <= cache[3] & 0xf:
                    self.put(sn[self.cnt - 18][0], es, self.out_ann, [1, ['DTD']])
                    self.decode_descriptors(-18)

            elif self.cnt == 127:
                dtd_last = cache[2] + (cache[3] & 0xf) * 18
                self.put(sn[dtd_last][0], es, self.out_ann, [1, ['Padding']])
            elif self.cnt == 128:
                checksum = sum(cache) % 256
                self.put(ss, es, self.out_ann, [0, ['Checksum: %d (%s)' % (
                         cache[self.cnt-1], 'Wrong' if checksum else 'OK')]])

    def ann_field(self, start, end, annotation):
        annotation = annotation if isinstance(annotation, list) else [annotation]
        sn = self.ext_sn[self.extension - 1] if self.extension else self.sn
        self.put(sn[start][0], sn[end][1],
                 self.out_ann, [ANN_FIELDS, annotation])

    def lookup_pnpid(self, pnpid):
        pnpid_file = os.path.join(os.path.dirname(__file__), 'pnpids.txt')
        if os.path.exists(pnpid_file):
            for line in open(pnpid_file).readlines():
                if line.find(pnpid + ';') == 0:
                    return line[4:].strip()
        return ''

    def decode_vid(self, offset):
        pnpid = chr(64 + ((self.cache[offset] & 0x7c) >> 2))
        pnpid += chr(64 + (((self.cache[offset] & 0x03) << 3)
                           | ((self.cache[offset+1] & 0xe0) >> 5)))
        pnpid += chr(64 + (self.cache[offset+1] & 0x1f))
        vendor = self.lookup_pnpid(pnpid)
        if vendor:
            pnpid += ' (%s)' % vendor
        self.ann_field(offset, offset+1, pnpid)

    def decode_pid(self, offset):
        pidstr = 'Product 0x%.2x%.2x' % (self.cache[offset+1], self.cache[offset])
        self.ann_field(offset, offset+1, pidstr)

    def decode_serial(self, offset):
        serialnum = (self.cache[offset+3] << 24) \
                + (self.cache[offset+2] << 16) \
                + (self.cache[offset+1] << 8) \
                + self.cache[offset]
        serialstr = ''
        is_alnum = True
        for i in range(4):
            if not chr(self.cache[offset+3-i]).isalnum():
                is_alnum = False
                break
            serialstr += chr(self.cache[offset+3-i])
        serial = serialstr if is_alnum else str(serialnum)
        self.ann_field(offset, offset+3, 'Serial ' + serial)

    def decode_mfrdate(self, offset):
        datestr = ''
        if self.cache[offset]:
            datestr += 'week %d, ' % self.cache[offset]
        datestr += str(1990 + self.cache[offset+1])
        if datestr:
            self.ann_field(offset, offset+1, ['Manufactured ' + datestr, datestr])

    def decode_basicdisplay(self, offset):
        # Video input definition
        vid = self.cache[offset]
        if vid & 0x80:
            # Digital
            self.ann_field(offset, offset, 'Video input: VESA DFP 1.')
        else:
            # Analog
            sls = (vid & 60) >> 5
            self.ann_field(offset, offset, 'Signal level standard: %.2x' % sls)
            if vid & 0x10:
                self.ann_field(offset, offset, 'Blank-to-black setup expected')
            syncs = ''
            if vid & 0x08:
                syncs += 'separate syncs, '
            if vid & 0x04:
                syncs += 'composite syncs, '
            if vid & 0x02:
                syncs += 'sync on green, '
            if vid & 0x01:
                syncs += 'Vsync serration required, '
            if syncs:
                self.ann_field(offset, offset, 'Supported syncs: %s' % syncs[:-2])
        # Max horizontal/vertical image size
        if self.cache[offset+1] != 0 and self.cache[offset+2] != 0:
            # Projectors have this set to 0
            sizestr = '%dx%dcm' % (self.cache[offset+1], self.cache[offset+2])
            self.ann_field(offset+1, offset+2, 'Physical size: ' + sizestr)
        # Display transfer characteristic (gamma)
        if self.cache[offset+3] != 0xff:
            gamma = (self.cache[offset+3] + 100) / 100
            self.ann_field(offset+3, offset+3, 'Gamma: %1.2f' % gamma)
        # Feature support
        fs = self.cache[offset+4]
        dpms = ''
        if fs & 0x80:
            dpms += 'standby, '
        if fs & 0x40:
            dpms += 'suspend, '
        if fs & 0x20:
            dpms += 'active off, '
        if dpms:
            self.ann_field(offset+4, offset+4, 'DPMS support: %s' % dpms[:-2])
        dt = (fs & 0x18) >> 3
        dtstr = ''
        if dt == 0:
            dtstr = 'Monochrome'
        elif dt == 1:
            dtstr = 'RGB color'
        elif dt == 2:
            dtstr = 'non-RGB multicolor'
        if dtstr:
            self.ann_field(offset+4, offset+4, 'Display type: %s' % dtstr)
        if fs & 0x04:
            self.ann_field(offset+4, offset+4, 'Color space: standard sRGB')
        # Save this for when we decode the first detailed timing descriptor
        self.have_preferred_timing = (fs & 0x02) == 0x02
        if fs & 0x01:
            gft = ''
        else:
            gft = 'not '
        self.ann_field(offset+4, offset+4,
                       'Generalized timing formula: %ssupported' % gft)

    def convert_color(self, value):
        # Convert from 10-bit packet format to float
        outval = 0.0
        for i in range(10):
            if value & 0x01:
                outval += 2 ** -(10-i)
            value >>= 1
        return outval

    def decode_chromaticity(self, offset):
        redx = (self.cache[offset+2] << 2) + ((self.cache[offset] & 0xc0) >> 6)
        redy = (self.cache[offset+3] << 2) + ((self.cache[offset] & 0x30) >> 4)
        self.ann_field(offset, offset+9, 'Chromacity red: X %1.3f, Y %1.3f' % (
                       self.convert_color(redx), self.convert_color(redy)))

        greenx = (self.cache[offset+4] << 2) + ((self.cache[offset] & 0x0c) >> 6)
        greeny = (self.cache[offset+5] << 2) + ((self.cache[offset] & 0x03) >> 4)
        self.ann_field(offset, offset+9, 'Chromacity green: X %1.3f, Y %1.3f' % (
                       self.convert_color(greenx), self.convert_color(greeny)))

        bluex = (self.cache[offset+6] << 2) + ((self.cache[offset+1] & 0xc0) >> 6)
        bluey = (self.cache[offset+7] << 2) + ((self.cache[offset+1] & 0x30) >> 4)
        self.ann_field(offset, offset+9, 'Chromacity blue: X %1.3f, Y %1.3f' % (
                       self.convert_color(bluex), self.convert_color(bluey)))

        whitex = (self.cache[offset+8] << 2) + ((self.cache[offset+1] & 0x0c) >> 6)
        whitey = (self.cache[offset+9] << 2) + ((self.cache[offset+1] & 0x03) >> 4)
        self.ann_field(offset, offset+9, 'Chromacity white: X %1.3f, Y %1.3f' % (
                       self.convert_color(whitex), self.convert_color(whitey)))

    def decode_est_timing(self, offset):
        # Pre-EDID modes
        bitmap = (self.cache[offset] << 9) \
            + (self.cache[offset+1] << 1) \
            + ((self.cache[offset+2] & 0x80) >> 7)
        modestr = ''
        for i in range(17):
                if bitmap & (1 << (16-i)):
                    modestr += est_modes[i] + ', '
        if modestr:
            self.ann_field(offset, offset+2,
                           'Supported established modes: %s' % modestr[:-2])

    def decode_std_timing(self, offset):
        modestr = ''
        for i in range(0, 16, 2):
            if self.cache[offset+i] == 0x01 and self.cache[offset+i+1] == 0x01:
                # Unused field
                continue
            x = (self.cache[offset+i] + 31) * 8
            ratio = (self.cache[offset+i+1] & 0xc0) >> 6
            ratio_x, ratio_y = xy_ratio[ratio]
            y = x / ratio_x * ratio_y
            refresh = (self.cache[offset+i+1] & 0x3f) + 60
            modestr += '%dx%d@%dHz, ' % (x, y, refresh)
        if modestr:
            self.ann_field(offset, offset + 15,
                    'Supported standard modes: %s' % modestr[:-2])

    def decode_detailed_timing(self, cache, sn, offset, is_first):
        if is_first and self.have_preferred_timing:
            # Only on first detailed timing descriptor
            section = 'Preferred'
        else:
            section = 'Detailed'
        section += ' timing descriptor'

        self.put(sn[0][0], sn[17][1],
             self.out_ann, [ANN_SECTIONS, [section]])

        pixclock = float((cache[1] << 8) + cache[0]) / 100
        self.ann_field(offset, offset+1, 'Pixel clock: %.2f MHz' % pixclock)

        horiz_active = ((cache[4] & 0xf0) << 4) + cache[2]
        horiz_blank = ((cache[4] & 0x0f) << 8) + cache[3]
        self.ann_field(offset+2, offset+4, 'Horizontal active: %d, blanking: %d' % (horiz_active, horiz_blank))

        vert_active = ((cache[7] & 0xf0) << 4) + cache[5]
        vert_blank = ((cache[7] & 0x0f) << 8) + cache[6]
        self.ann_field(offset+5, offset+7, 'Vertical active: %d, blanking: %d' % (vert_active, vert_blank))

        horiz_sync_off = ((cache[11] & 0xc0) << 2) + cache[8]
        horiz_sync_pw  = ((cache[11] & 0x30) << 4) + cache[9]
        vert_sync_off  = ((cache[11] & 0x0c) << 2) + ((cache[10] & 0xf0) >> 4)
        vert_sync_pw   = ((cache[11] & 0x03) << 4) +  (cache[10] & 0x0f)

        syncs = (horiz_sync_off, horiz_sync_pw, vert_sync_off, vert_sync_pw)
        self.ann_field(offset+8, offset+11, [
            'Horizontal sync offset: %d, pulse width: %d, Vertical sync offset: %d, pulse width: %d' % syncs,
            'HSync off: %d, pw: %d, VSync off: %d, pw: %d' % syncs])

        horiz_size = ((cache[14] & 0xf0) << 4) + cache[12]
        vert_size  = ((cache[14] & 0x0f) << 8) + cache[13]
        self.ann_field(offset+12, offset+14, 'Physical size: %dx%dmm' % (horiz_size, vert_size))

        horiz_border = cache[15]
        self.ann_field(offset+15, offset+15, 'Horizontal border: %d pixels' % horiz_border)
        vert_border = cache[16]
        self.ann_field(offset+16, offset+16, 'Vertical border: %d lines' % vert_border)

        features = 'Flags: '
        if cache[17] & 0x80:
            features += 'interlaced, '
        stereo = (cache[17] & 0x60) >> 5
        if stereo:
            if cache[17] & 0x01:
                features += '2-way interleaved stereo ('
                features += ['right image on even lines',
                             'left image on even lines',
                             'side-by-side'][stereo-1]
                features += '), '
            else:
                features += 'field sequential stereo ('
                features += ['right image on sync=1', 'left image on sync=1',
                             '4-way interleaved'][stereo-1]
                features += '), '
        sync = (cache[17] & 0x18) >> 3
        sync2 = (cache[17] & 0x06) >> 1
        posneg = ['negative', 'positive']
        features += 'sync type '
        if sync == 0x00:
            features += 'analog composite (serrate on RGB)'
        elif sync == 0x01:
            features += 'bipolar analog composite (serrate on RGB)'
        elif sync == 0x02:
            features += 'digital composite (serrate on composite polarity ' \
                        + (posneg[sync2 & 0x01]) + ')'
        elif sync == 0x03:
            features += 'digital separate ('
            features += 'Vsync polarity ' + (posneg[(sync2 & 0x02) >> 1])
            features += ', Hsync polarity ' + (posneg[sync2 & 0x01])
            features += ')'
        features += ', '
        self.ann_field(offset+17, offset+17, features[:-2])

    def decode_descriptor(self, cache, offset):
        tag = cache[3]
        self.ann_field(offset, offset+1, "Flag")
        self.ann_field(offset+2, offset+2, "Flag (reserved)")
        self.ann_field(offset+3, offset+3, "Tag: {0:X}".format(tag))
        self.ann_field(offset+4, offset+4, "Flag")

        sn = self.ext_sn[self.extension - 1] if self.extension else self.sn

        if tag == 0xff:
            # Monitor serial number
            self.put(sn[offset][0], sn[offset+17][1], self.out_ann,
                     [ANN_SECTIONS, ['Serial number']])
            text = bytes(cache[5:][:13]).decode(encoding='cp437', errors='replace')
            self.ann_field(offset+5, offset+17, text.strip())
        elif tag == 0xfe:
            # Text
            self.put(sn[offset][0], sn[offset+17][1], self.out_ann,
                     [ANN_SECTIONS, ['Text']])
            text = bytes(cache[5:][:13]).decode(encoding='cp437', errors='replace')
            self.ann_field(offset+5, offset+17, text.strip())
        elif tag == 0xfc:
            # Monitor name
            self.put(sn[offset][0], sn[offset+17][1], self.out_ann,
                     [ANN_SECTIONS, ['Monitor name']])
            text = bytes(cache[5:][:13]).decode(encoding='cp437', errors='replace')
            self.ann_field(offset+5, offset+17, text.strip())
        elif tag == 0xfd:
            # Monitor range limits
            self.put(sn[offset][0], sn[offset+17][1], self.out_ann,
                     [ANN_SECTIONS, ['Monitor range limits']])
            self.ann_field(offset+5, offset+5, [
                           'Minimum vertical rate: {0}Hz'.format(cache[5]),
                           'VSync >= {0}Hz'.format(cache[5])])
            self.ann_field(offset+6, offset+6, [
                           'Maximum vertical rate: {0}Hz'.format(cache[6]),
                           'VSync <= {0}Hz'.format(cache[6])])
            self.ann_field(offset+7, offset+7, [
                           'Minimum horizontal rate: {0}kHz'.format(cache[7]),
                           'HSync >= {0}kHz'.format(cache[7])])
            self.ann_field(offset+8, offset+8, [
                           'Maximum horizontal rate: {0}kHz'.format(cache[8]),
                           'HSync <= {0}kHz'.format(cache[8])])
            self.ann_field(offset+9, offset+9, [
                           'Maximum pixel clock: {0}MHz'.format(cache[9] * 10),
                           'PixClk <= {0}MHz'.format(cache[9] * 10)])
            if cache[10] == 0x02:
                self.ann_field(offset+10, offset+10, ['Secondary timing formula supported', '2nd GTF: yes'])
                self.ann_field(offset+11, offset+17, ['GTF'])
            else:
                self.ann_field(offset+10, offset+10, ['Secondary timing formula unsupported', '2nd GTF: no'])
                self.ann_field(offset+11, offset+17, ['Padding'])
        elif tag == 0xfb:
            # Additional color point data
            self.put(sn[offset][0], sn[offset+17][1], self.out_ann,
                     [ANN_SECTIONS, ['Additional color point data']])
        elif tag == 0xfa:
            # Additional standard timing definitions
            self.put(sn[offset][0], sn[offset+17][1], self.out_ann,
                     [ANN_SECTIONS, ['Additional standard timing definitions']])
        else:
            self.put(sn[offset][0], sn[offset+17][1], self.out_ann,
                     [ANN_SECTIONS, ['Unknown descriptor']])

    def decode_descriptors(self, offset):
        # 4 consecutive 18-byte descriptor blocks
        cache = self.ext_cache[self.extension - 1] if self.extension else self.cache
        sn = self.ext_sn[self.extension - 1] if self.extension else self.sn

        for i in range(offset, 0, 18):
            if cache[i] != 0 or cache[i+1] != 0:
                self.decode_detailed_timing(cache[i:], sn[i:], i, i == offset)
            else:
                if cache[i+2] == 0 or cache[i+4] == 0:
                    self.decode_descriptor(cache[i:], i)

    def decode_data_block(self, tag, cache, sn):
        codes = { 0: ['0: Reserved'],
                  1: ['1: Audio Data Block', 'Audio'],
                  2: ['2: Video Data Block', 'Video'],
                  3: ['3: Vendor Specific Data Block', 'VSDB'],
                  4: ['4: Speacker Allocation Data Block', 'SADB'],
                  5: ['5: VESA DTC Data Block', 'DTC'],
                  6: ['6: Reserved'],
                  7: ['7: Extended', 'Ext'] }
        ext_codes = {  0: [ '0: Video Capability Data Block', 'VCDB'],
                       1: [ '1: Vendor Specific Video Data Block', 'VSVDB'],
                      17: ['17: Vendor Specific Audio Data Block', 'VSADB'], }
        if tag < 7:
            code = codes[tag]
            ext_len = 0
            if tag == 1:
                aformats = { 1: '1 (LPCM)' }
                rates = [ '192', '176', '96', '88', '48', '44', '32' ]

                aformat = cache[1] >> 3
                sup_rates = [ i for i in range(0, 8) if (1 << i) & cache[2] ]

                data = "Format: {0} Channels: {1}".format(
                    aformats.get(aformat, aformat), (cache[1] & 0x7) + 1)
                data += " Rates: " + " ".join(rates[6 - i] for i in sup_rates)
                data += " Extra: [{0:02X}]".format(cache[3])

            elif tag ==2:
                data = "VIC: "
                data += ", ".join("{0}{1}".format(v & 0x7f,
                        ['', ' (Native)'][v >> 7])
                        for v in cache[1:])

            elif tag ==3:
                ouis = { b'\x00\x0c\x03': 'HDMI Licensing, LLC' }
                oui = bytes(cache[3:0:-1])
                ouis = ouis.get(oui, None)
                data = "OUI: " + " ".join('{0:02X}'.format(x) for x in oui)
                data += " ({0})".format(ouis) if ouis else ""
                data += ", PhyAddr: {0}.{1}.{2}.{3}".format(
                        cache[4] >> 4, cache[4] & 0xf, cache[5] >> 4, cache[5] & 0xf)
                data += ", [" + " ".join('{0:02X}'.format(x) for x in cache[6:]) + "]"

            elif tag ==4:
                speakers = [ 'FL/FR', 'LFE', 'FC', 'RL/RR',
                             'RC', 'FLC/FRC', 'RLC/RRC', 'FLW/FRW',
                             'FLH/FRH', 'TC', 'FCH' ]
                sup_speakers = cache[1] + (cache[2] << 8)
                sup_speakers = [ i for i in range(0, 8) if (1 << i) & sup_speakers ]
                data = "Speakers: " + " ".join(speakers[i] for i in sup_speakers)

            else:
                data = " ".join('{0:02X}'.format(x) for x in cache[1:])

        else:
            # Extended tags
            ext_len = 1
            ext_code = ext_codes.get(cache[1], ['Unknown', '?'])
            code = zip(codes[7], [", ", ": "], ext_code)
            code = [ "".join(x) for x in code ]
            data = " ".join('{0:02X}'.format(x) for x in cache[2:])

        self.put(sn[0][0], sn[0 + ext_len][1], self.out_ann,
                 [ANN_FIELDS, code])
        self.put(sn[1 + ext_len][0], sn[len(cache) - 1][1], self.out_ann,
                 [ANN_FIELDS, [data]])

    def decode_data_block_collection(self, cache, sn):
        offset = 0
        while offset < len(cache):
            length = 1 + cache[offset] & 0x1f
            tag = cache[offset] >> 5
            self.decode_data_block(tag, cache[offset:offset + length], sn[offset:])
            offset += length
