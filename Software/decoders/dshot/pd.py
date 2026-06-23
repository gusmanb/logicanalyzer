##
## This file is part of the libsigrokdecode project.
##
## Copyright (C) 2024 DShot decoder contributor
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

import sigrokdecode as srd
from common.srdhelper import bitpack_msb

class SamplerateError(Exception):
    pass

class DecoderError(Exception):
    pass

# DShot command table (0-47)
DSHOT_COMMANDS = {
    0: 'DISARM',
    1: 'BEEP1',
    2: 'BEEP2',
    3: 'BEEP3',
    4: 'BEEP4',
    5: 'BEEP5',
    6: '3D_MODE_OFF',
    7: '3D_MODE_ON',
    8: 'MOTOR_STOP',
    9: 'SAVE_SETTING',
    10: 'SPIN_DIRECTION_1',
    11: 'SPIN_DIRECTION_2',
    12: 'SAVE_DIRECTION',
    13: 'SPINUP_RATIO_INCREASE',
    14: 'SPINUP_RATIO_DECREASE',
    15: 'SET_PWM_MODE_LOW_KHZ',
    16: 'SET_PWM_MODE_HIGH_KHZ',
    17: 'LED0_ON',
    18: 'LED1_ON',
    19: 'LED2_ON',
    20: 'LED3_ON',
    21: 'LED0_OFF',
    22: 'LED1_OFF',
    23: 'LED2_OFF',
    24: 'LED3_OFF',
    25: 'TOGGLE_LED0',
    26: 'TOGGLE_LED1',
    27: 'TOGGLE_LED2',
    28: 'TOGGLE_LED3',
    29: 'RAMP_RATE_INCREASE',
    30: 'RAMP_RATE_DECREASE',
    31: 'ACRO_TRAINER_INCREASE_LEVEL',
    32: 'ACRO_TRAINER_DECREASE_LEVEL',
    33: 'ACRO_TRAINER_OFF',
    34: 'TURTLE_MODE_ON',
    35: 'TURTLE_MODE_OFF',
    36: 'IMPORT_SETTING',
    37: 'EXPORT_SETTING',
    38: 'TURTLE_MODE_INCREASE_POWER',
    39: 'TURTLE_MODE_DECREASE_POWER',
    40: 'TURTLE_MODE_INCREASE_LEVEL',
    41: 'TURTLE_MODE_DECREASE_LEVEL',
    42: 'TURTLE_MODE_INCREASE_DOWNTHROTTLE',
    43: 'TURTLE_MODE_DECREASE_DOWNTHROTTLE',
    44: 'TURTLE_MODE_INCREASE_REPLENISHMENT',
    45: 'TURTLE_MODE_DECREASE_REPLENISHMENT',
    46: 'SIN_MODE_INCREASE_FREQUENCY',
    47: 'SIN_MODE_DECREASE_FREQUENCY',
}

(
    ANN_BIT, ANN_THROTTLE, ANN_TELEMETRY, ANN_CRC,
    ANN_FRAME, ANN_WARN, ANN_RATE,
) = range(7)

class Decoder(srd.Decoder):
    api_version = 3
    id = 'dshot'
    name = 'DShot'
    longname = 'DShot ESC protocol'
    desc = 'DShot throttle command decoder for ESCs'
    license = 'gplv3+'
    inputs = ['logic']
    outputs = []
    tags = ['Motor Control', 'RC']
    channels = (
        {'id': 'data', 'name': 'Data', 'desc': 'DShot signal line'},
    )
    options = (
        {'id': 'polarity', 'desc': 'Polarity',
         'default': 'active-high',
         'values': ('active-low', 'active-high')},
    )
    annotations = (
        ('bit', 'Bit'),
        ('throttle', 'Throttle'),
        ('telemetry', 'Telemetry'),
        ('crc', 'CRC'),
        ('frame', 'Frame'),
        ('warning', 'Warning'),
        ('rate', 'Rate'),
    )
    annotation_rows = (
        ('bits', 'Bits', (ANN_BIT,)),
        ('fields', 'Fields', (ANN_THROTTLE, ANN_TELEMETRY, ANN_CRC,)),
        ('frames', 'Frames', (ANN_FRAME,)),
        ('warnings', 'Warnings', (ANN_WARN,)),
        ('rates', 'Rate', (ANN_RATE,)),
    )

    def __init__(self):
        self.reset()

    def reset(self):
        self.samplerate = None
        self.bits = []
        self.bit_periods = []
        self.last_period = None
        self.last_rate_label = None
        self.frame_count = 0

    def start(self):
        self.out_ann = self.register(srd.OUTPUT_ANN)
        self.out_meta = self.register(srd.OUTPUT_META,
                                      meta=(float, 'Bit rate', 'Detected DShot bit rate'))

    def metadata(self, key, value):
        if key == srd.SRD_CONF_SAMPLERATE:
            self.samplerate = value

    def putg(self, ss, es, cls, text):
        self.put(ss, es, self.out_ann, [cls, text])

    def putm(self, ss, es, meta_value):
        self.put(ss, es, self.out_meta, meta_value)

    def classify_bit(self, duty, period):
        if period == 0:
            return 0
        ratio = duty / period
        return 1 if ratio > 0.5 else 0

    def compute_crc(self, throttle, telemetry):
        value = (throttle << 1) | telemetry
        csum = (value ^ (value >> 4) ^ (value >> 8)) & 0xF
        return csum

    def detect_rate(self, avg_period_samples):
        if avg_period_samples == 0 or self.samplerate == 0:
            return None, None
        avg_period_us = (avg_period_samples / self.samplerate) * 1e6
        period_ns = avg_period_us * 1000
        rate_bps = 1e9 / period_ns
        rate_kbps = rate_bps / 1000
        standard_rates = {
            150000: 'DSHOT150',
            300000: 'DSHOT300',
            600000: 'DSHOT600',
            1200000: 'DSHOT1200',
        }
        nearest_rate = min(standard_rates.keys(),
                          key=lambda x: abs(x - rate_bps))
        tolerance = nearest_rate * 0.15
        if abs(rate_bps - nearest_rate) <= tolerance:
            label = standard_rates[nearest_rate]
        else:
            label = f'Non-standard ({rate_kbps:.0f} kbit/s)'
        return label, rate_bps

    def handle_frame(self, ss_frame, es_frame):
        if len(self.bits) != 16:
            return
        throttle = bitpack_msb(self.bits[0:11], 0)
        telemetry = self.bits[11][0]
        crc_rx = bitpack_msb(self.bits[12:16], 0)
        crc_exp = self.compute_crc(throttle, telemetry)
        crc_match = (crc_rx == crc_exp)
        ss_throttle, es_throttle = self.bits[0][1], self.bits[10][2]
        ss_telemetry, es_telemetry = self.bits[11][1], self.bits[11][2]
        ss_crc, es_crc = self.bits[12][1], self.bits[15][2]
        throttle_pct = ((throttle - 48) / (2047 - 48)) * 100 if throttle >= 48 else 0
        if throttle < 48:
            throttle_text = DSHOT_COMMANDS.get(throttle, f'Reserved ({throttle})')
        else:
            throttle_text = f'{throttle} ({throttle_pct:.1f}%)'
        self.putg(ss_throttle, es_throttle, ANN_THROTTLE, [throttle_text])
        self.putg(ss_telemetry, es_telemetry, ANN_TELEMETRY,
                 [f'{telemetry}'])
        crc_text = f'{crc_rx:X} (exp {crc_exp:X})'
        self.putg(ss_crc, es_crc, ANN_CRC, [crc_text])
        if not crc_match:
            self.putg(ss_crc, es_crc, ANN_WARN, ['CRC MISMATCH'])
        frame_text = f'THR={throttle} TLM={telemetry} CRC={crc_rx:X} {"OK" if crc_match else "BAD"}'
        self.putg(ss_frame, es_frame, ANN_FRAME, [frame_text])
        self.frame_count += 1
        if len(self.bit_periods) >= 15:
            avg_period = sum(self.bit_periods[:15]) / 15.0
            rate_label, rate_bps = self.detect_rate(avg_period)
            if rate_label and rate_label != self.last_rate_label:
                self.last_rate_label = rate_label
                self.putg(ss_frame, es_frame, ANN_RATE, [rate_label])
            if rate_bps:
                self.putm(ss_frame, es_frame, rate_bps)

    def decode(self):
        if not self.samplerate:
            raise SamplerateError('Cannot decode without samplerate.')
        polarity_active_high = (self.options['polarity'] == 'active-high')
        edge_start = 'r' if polarity_active_high else 'f'
        edge_fall = 'f' if polarity_active_high else 'r'

        bit_count = 0
        frame_ss = None

        # Find the rising edge that starts the very first bit.
        try:
            self.wait({0: edge_start})
        except Exception:
            return
        ss_bit = self.samplenum

        while True:
            if frame_ss is None:
                frame_ss = ss_bit

            # Measure the high period (duty): wait for the falling edge.
            try:
                self.wait({0: edge_fall})
            except Exception:
                break
            duty = self.samplenum - ss_bit

            # Find the next rising edge. Within a frame it is the start of the
            # next bit (rise-to-rise == one bit period). After the last bit of
            # a frame the line stays idle far longer than a bit period, so we
            # also arm an idle timeout to detect the frame boundary. This makes
            # frame delimiting self-timing instead of assuming exactly 16 bits.
            if self.last_period:
                idle_threshold = max(int(self.last_period * 1.5), 1)
                conds = [{0: edge_start}, {'skip': idle_threshold}]
            else:
                # No reference period yet (first bit): only wait for next edge.
                idle_threshold = None
                conds = [{0: edge_start}]

            got_next_edge = False
            try:
                self.wait(conds)
                if idle_threshold is None or self.matched[0]:
                    got_next_edge = True
                    next_ss = self.samplenum
            except Exception:
                got_next_edge = False

            if got_next_edge:
                # Reuse this edge as both this bit's end and next bit's start.
                period = next_ss - ss_bit
                self.last_period = period
                self.bit_periods.append(period)
                es_bit = next_ss
            else:
                # Idle gap or end of capture => this is the frame's last bit.
                period = self.last_period if self.last_period else (self.samplenum - ss_bit)
                es_bit = self.samplenum

            # Classify the bit by its duty cycle.
            bit_value = self.classify_bit(duty, period)
            self.bits.append((bit_value, ss_bit, es_bit))
            self.putg(ss_bit, es_bit, ANN_BIT, ['{:d}'.format(bit_value)])
            bit_count += 1

            # Emit a frame once 16 bits are collected.
            if bit_count >= 16:
                self.handle_frame(frame_ss, es_bit)
                self.bits.clear()
                self.bit_periods.clear()
                bit_count = 0
                frame_ss = None

            if got_next_edge:
                # The edge we found is the start of the next bit (or, if a frame
                # just completed back-to-back, the next frame's first bit).
                ss_bit = next_ss
            else:
                # Idle gap or end of capture. If a frame was mid-flight (not just
                # completed), discard the partial frame and resync.
                if bit_count != 0:
                    self.bits.clear()
                    self.bit_periods.clear()
                    bit_count = 0
                    frame_ss = None
                # Find the next frame's first rising edge.
                try:
                    self.wait({0: edge_start})
                except Exception:
                    break
                ss_bit = self.samplenum
