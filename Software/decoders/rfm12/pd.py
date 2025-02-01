##
## This file is part of the libsigrokdecode project.
##
## Copyright (C) 2014 Sławek Piotrowski <sentinel@atteo.org>
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

class Decoder(srd.Decoder):
    api_version = 3
    id = 'rfm12'
    name = 'RFM12'
    longname = 'HopeRF RFM12'
    desc = 'HopeRF RFM12 wireless transceiver control protocol.'
    license = 'gplv2+'
    inputs = ['spi']
    outputs = []
    tags = ['Wireless/RF']
    annotations = (
        ('cmd', 'Command'),
        ('param', 'Command parameter'),
        ('disabled', 'Disabled bit'),
        ('return', 'Returned value'),
        ('disabled_return', 'Disabled returned value'),
        ('interpretation', 'Interpretation'),
    )
    annotation_rows = (
        ('commands', 'Commands', (0, 1, 2)),
        ('returns', 'Returns', (3, 4)),
        ('interpretations', 'Interpretations', (5,)),
    )

    def __init__(self):
        self.reset()

    def reset(self):
        self.mosi_bytes, self.miso_bytes = [], []
        self.mosi_bits, self.miso_bits = [], []
        self.row_pos = [0, 0, 0]

        self.ann_to_row = [0, 0, 0, 1, 1, 2]

        # Initialize with Power-On-Reset values.
        self.last_status = [0x00, 0x00]
        self.last_config = 0x08
        self.last_power = 0x08
        self.last_freq = 0x680
        self.last_data_rate = 0x23
        self.last_fifo_and_reset = 0x80
        self.last_afc = 0xF7
        self.last_transceiver = 0x00
        self.last_pll = 0x77

    def advance_ann(self, ann, length):
        row = self.ann_to_row[ann]
        self.row_pos[row] += length

    def putx(self, ann, length, description):
        if not isinstance(description, list):
            description = [description]
        row = self.ann_to_row[ann]
        bit = self.row_pos[row]
        self.put(self.mosi_bits[bit][1], self.mosi_bits[bit + length - 1][2],
                 self.out_ann, [ann, description])
        bit += length
        self.row_pos[row] = bit

    def describe_bits(self, data, names):
        i = 0x01 << len(names) - 1
        bit = 0
        while i != 0:
            if names[bit] != '':
                self.putx(1 if (data & i) else 2, 1, names[bit])
            i >>= 1
            bit += 1

    def describe_return_bits(self, data, names):
        i = 0x01 << len(names) - 1
        bit = 0
        while i != 0:
            if names[bit] != '':
                self.putx(3 if (data & i) else 4, 1, names[bit])
            else:
                self.advance_ann(3, 1)
            i >>= 1
            bit += 1

    def describe_changed_bits(self, data, old_data, names):
        changes = data ^ old_data
        i = 0x01 << (len(names) - 1)
        bit = 0
        while i != 0:
            if names[bit] != '' and changes & i:
                s = ['+', 'Turning on'] if (data & i) else ['-', 'Turning off']
                self.putx(5, 1, s)
            else:
                self.advance_ann(5, 1)
            i >>= 1
            bit += 1

    def start(self):
        self.out_ann = self.register(srd.OUTPUT_ANN)

    def handle_configuration_cmd(self, cmd, ret):
        self.putx(0, 8, ['Configuration command', 'Configuration'])
        NAMES = [['Internal data register', 'el'], ['FIFO mode', 'ef']]

        bits = (cmd[1] & 0xC0) >> 6
        old_bits = (self.last_config & 0xC0) >> 6
        self.describe_bits(bits, NAMES)
        self.describe_changed_bits(bits, old_bits, NAMES)

        FREQUENCIES = ['315', '433', '868', '915']
        f = FREQUENCIES[(cmd[1] & 0x30) >> 4] + 'MHz'
        self.putx(1, 2, ['Frequency: ' + f, f])
        if cmd[1] & 0x30 != self.last_config & 0x30:
            self.putx(5, 2, ['Changed', '~'])

        c = '%.1fpF' % (8.5 + (cmd[1] & 0xF) * 0.5)
        self.putx(1, 4, ['Capacitance: ' + c, c])
        if cmd[1] & 0xF != self.last_config & 0xF:
            self.putx(5, 4, ['Changed', '~'])

        self.last_config = cmd[1]

    def handle_power_management_cmd(self, cmd, ret):
        self.putx(0, 8, ['Power management', 'Power'])
        NAMES = [['Receiver chain', 'er'], ['Baseband circuit', 'ebb'],
                 ['Transmission', 'et'], ['Synthesizer', 'es'],
                 ['Crystal oscillator', 'ex'], ['Low battery detector', 'eb'],
                 ['Wake-up timer', 'ew'], ['Clock output off switch', 'dc']]

        self.describe_bits(cmd[1], NAMES)

        power = cmd[1]

        # Some bits imply other, even if they are set to 0.
        if power & 0x80:
            power |= 0x58
        if power & 0x20:
            power |= 0x18
        self.describe_changed_bits(power, self.last_power, NAMES)

        self.last_power = power

    def handle_frequency_setting_cmd(self, cmd, ret):
        self.putx(0, 4, ['Frequency setting', 'Frequency'])
        f = ((cmd[1] & 0xF) << 8) + cmd[2]
        self.putx(0, 12, ['F = %3.4f' % f])
        self.row_pos[2] -= 4
        if self.last_freq != f:
            self.putx(5, 12, ['Changing', '~'])
        self.last_freq = f

    def handle_data_rate_cmd(self, cmd, ret):
        self.putx(0, 8, ['Data rate command', 'Data rate'])
        r = cmd[1] & 0x7F
        cs = (cmd[1] & 0x80) >> 7
        rate = 10000 / 29.0 / (r + 1) / (1 + 7 * cs)
        self.putx(0, 8, ['%3.1fkbps' % rate])
        if self.last_data_rate != cmd[1]:
            self.putx(5, 8, ['Changing', '~'])
        self.last_data_rate = cmd[1]

    def handle_receiver_control_cmd(self, cmd, ret):
        self.putx(0, 5, ['Receiver control command'])
        s = 'interrupt input' if (cmd[0] & 0x04) else 'VDI output'
        self.putx(0, 1, ['pin16 = ' + s])
        VDI_NAMES = ['Fast', 'Medium', 'Slow', 'Always on']
        vdi_speed = VDI_NAMES[cmd[0] & 0x3]
        self.putx(0, 2, ['VDI: %s' % vdi_speed])
        BANDWIDTH_NAMES = ['Reserved', '400kHz', '340kHz', '270kHz', '200kHz',
                           '134kHz', '67kHz', 'Reserved']
        bandwidth = BANDWIDTH_NAMES[(cmd[1] & 0xE0) >> 5]
        self.putx(0, 3, ['Bandwidth: %s' % bandwidth])
        LNA_GAIN_NAMES = [0, -6, -14, -20]
        lna_gain = LNA_GAIN_NAMES[(cmd[1] & 0x18) >> 3]
        self.putx(0, 2, ['LNA gain: %ddB' % lna_gain])
        RSSI_THRESHOLD_NAMES = ['-103', '-97', '-91', '-85', '-79', '-73',
                                'Reserved', 'Reserved']
        rssi_threshold = RSSI_THRESHOLD_NAMES[cmd[1] & 0x7]
        self.putx(0, 3, ['RSSI threshold: %s' % rssi_threshold])

    def handle_data_filter_cmd(self, cmd, ret):
        self.putx(0, 8, ['Data filter command'])
        if cmd[1] & 0x80:
            clock_recovery = 'auto'
        elif cmd[1] & 0x40:
            clock_recovery = 'fast'
        else:
            clock_recovery = 'slow'
        self.putx(0, 2, ['Clock recovery: %s mode' % clock_recovery])
        self.advance_ann(0, 1) # Should always be 1.
        s = 'analog' if (cmd[1] & 0x10) else 'digital'
        self.putx(0, 1, ['Data filter: ' + s])
        self.advance_ann(0, 1) # Should always be 1.
        self.putx(0, 3, ['DQD threshold: %d' % (cmd[1] & 0x7)])

    def handle_fifo_and_reset_cmd(self, cmd, ret):
        self.putx(0, 8, ['FIFO and reset command'])
        fifo_level = (cmd[1] & 0xF0) >> 4
        self.putx(0, 4, ['FIFO trigger level: %d' % fifo_level])
        last_fifo_level = (self.last_fifo_and_reset & 0xF0) >> 4
        if fifo_level != last_fifo_level:
            self.putx(5, 4, ['Changing', '~'])
        else:
            self.advance_ann(5, 4)
        s = 'one byte' if (cmd[1] & 0x08) else 'two bytes'
        self.putx(0, 1, ['Synchron length: ' + s])
        if (cmd[1] & 0x08) != (self.last_fifo_and_reset & 0x08):
            self.putx(5, 1, ['Changing', '~'])
        else:
            self.advance_ann(5, 1)

        if cmd[1] & 0x04:
            fifo_fill = 'Always'
        elif cmd[1] & 0x02:
            fifo_fill = 'After synchron pattern'
        else:
            fifo_fill = 'Never'
        self.putx(0, 2, ['FIFO fill: %s' % fifo_fill])
        if (cmd[1] & 0x06) != (self.last_fifo_and_reset & 0x06):
            self.putx(5, 2, ['Changing', '~'])
        else:
            self.advance_ann(5, 2)

        s = 'non-sensitive' if (cmd[1] & 0x01) else 'sensitive'
        self.putx(0, 1, ['Reset mode: ' + s])
        if (cmd[1] & 0x01) != (self.last_fifo_and_reset & 0x01):
            self.putx(5, 1, ['Changing', '~'])
        else:
            self.advance_ann(5, 1)

        self.last_fifo_and_reset = cmd[1]

    def handle_synchron_pattern_cmd(self, cmd, ret):
        self.putx(0, 8, ['Synchron pattern command'])
        if self.last_fifo_and_reset & 0x08:
            self.putx(0, 8, ['Pattern: 0x2D%02X' % pattern])
        else:
            self.putx(0, 8, ['Pattern: %02X' % pattern])

    def handle_fifo_read_cmd(self, cmd, ret):
        self.putx(0, 8, ['FIFO read command', 'FIFO read'])
        self.putx(3, 8, ['Data: %02X' % ret[1]])

    def handle_afc_cmd(self, cmd, ret):
        self.putx(0, 8, ['AFC command'])
        MODES = ['Off', 'Once', 'During receiving', 'Always']
        mode = (cmd[1] & 0xC0) >> 6
        self.putx(0, 2, ['Mode: %s' % MODES[mode]])
        if (cmd[1] & 0xC0) != (self.last_afc & 0xC0):
            self.putx(5, 2, ['Changing', '~'])
        else:
            self.advance_ann(5, 2)

        range_limit = (cmd[1] & 0x30) >> 4
        FREQ_TABLE = [0.0, 2.5, 5.0, 7.5]
        freq_delta = FREQ_TABLE[(self.last_config & 0x30) >> 4]

        if range_limit == 0:
            self.putx(0, 2, ['Range: No limit'])
        elif range_limit == 1:
            self.putx(0, 2, ['Range: +/-%dkHz' % (15 * freq_delta)])
        elif range_limit == 2:
            self.putx(0, 2, ['Range: +/-%dkHz' % (7 * freq_delta)])
        elif range_limit == 3:
            self.putx(0, 2, ['Range: +/-%dkHz' % (3 * freq_delta)])

        if (cmd[1] & 0x30) != (self.last_afc & 0x30):
            self.putx(5, 2, ['Changing', '~'])
        else:
            self.advance_ann(5, 2)

        NAMES = ['Strobe edge', 'High accuracy mode', 'Enable offset register',
                 'Enable offset calculation']
        self.describe_bits(cmd[1] & 0xF, NAMES)
        self.describe_changed_bits(cmd[1] & 0xF, self.last_afc & 0xF, NAMES)

        self.last_afc = cmd[1]

    def handle_transceiver_control_cmd(self, cmd, ret):
        self.putx(0, 8, ['Transceiver control command'])
        self.putx(0, 4, ['FSK frequency delta: %dkHz' % (15 * ((cmd[1] & 0xF0) >> 4))])
        if cmd[1] & 0xF0 != self.last_transceiver & 0xF0:
            self.putx(5, 4, ['Changing', '~'])
        else:
            self.advance_ann(5, 4)

        POWERS = [0, -2.5, -5, -7.5, -10, -12.5, -15, -17.5]
        self.advance_ann(0, 1)
        self.advance_ann(5, 1)
        self.putx(0,3, ['Relative power: %dB' % (cmd[1] & 0x07)])
        if (cmd[1] & 0x07) != (self.last_transceiver & 0x07):
            self.putx(5, 3, ['Changing', '~'])
        else:
            self.advance_ann(5, 3)
        self.last_transceiver = cmd[1]

    def handle_pll_setting_cmd(self, cmd, ret):
        self.putx(0, 8, ['PLL setting command'])
        self.advance_ann(0, 1)
        self.putx(0, 2, ['Clock buffer rise and fall time'])
        self.advance_ann(0, 1)
        self.advance_ann(5, 4)
        NAMES = [['Delay in phase detector', 'dly'], ['Disable dithering', 'ddit']]
        self.describe_bits((cmd[1] & 0xC) >> 2, NAMES)
        self.describe_changed_bits((cmd[1] & 0xC) >> 2, (self.last_pll & 0xC) >> 2, NAMES)
        s = '256kbps, high' if (cmd[1] & 0x01) else '86.2kbps, low'
        self.putx(0, 1, ['Max bit rate: %s noise' % s])

        self.advance_ann(5, 1)
        if (cmd[1] & 0x01) != (self.last_pll & 0x01):
            self.putx(5, 1, ['Changing', '~'])

        self.last_pll = cmd[1]

    def handle_transmitter_register_cmd(self, cmd, ret):
        self.putx(0, 8, ['Transmitter register command', 'Transmit'])
        self.putx(0, 8, ['Data: %s' % cmd[1], '%s' % cmd[1]])

    def handle_software_reset_cmd(self, cmd, ret):
        self.putx(0, 16, ['Software reset command'])

    def handle_wake_up_timer_cmd(self, cmd, ret):
        self.putx(0, 3, ['Wake-up timer command', 'Timer'])
        r = cmd[0] & 0x1F
        m = cmd[1]
        time = 1.03 * m * pow(2, r) + 0.5
        self.putx(0, 13, ['Time: %7.2f' % time])

    def handle_low_duty_cycle_cmd(self, cmd, ret):
        self.putx(0, 16, ['Low duty cycle command'])

    def handle_low_battery_detector_cmd(self, cmd, ret):
        self.putx(0, 8, ['Low battery detector command'])
        NAMES = ['1', '1.25', '1.66', '2', '2.5', '3.33', '5', '10']
        clock = NAMES[(cmd[1] & 0xE0) >> 5]
        self.putx(0, 3, ['Clock output: %sMHz' % clock, '%sMHz' % clock])
        self.advance_ann(0, 1)
        v = 2.25 + (cmd[1] & 0x0F) * 0.1
        self.putx(0, 4, ['Low battery voltage: %1.2fV' % v, '%1.2fV' % v])

    def handle_status_read_cmd(self, cmd, ret):
        self.putx(0, 8, ['Status read command', 'Status'])
        NAMES = ['RGIT/FFIT', 'POR', 'RGUR/FFOV', 'WKUP', 'EXT', 'LBD',
                 'FFEM', 'RSSI/ATS', 'DQD', 'CRL', 'ATGL']
        status = (ret[0] << 3) + (ret[1] >> 5)
        self.row_pos[1] -= 8
        self.row_pos[2] -= 8
        self.describe_return_bits(status, NAMES)
        receiver_enabled = (self.last_power & 0x80) >> 7

        if ret[0] & 0x80:
            if receiver_enabled:
                s = 'Received data in FIFO'
            else:
                s = 'Transmit register ready'
            self.putx(5, 1, s)
        else:
            self.advance_ann(5, 1)
        if ret[0] & 0x40:
            self.putx(5, 1, 'Power on Reset')
        else:
            self.advance_ann(5, 1)
        if ret[0] & 0x20:
            if receiver_enabled:
                s = 'RX FIFO overflow'
            else:
                s = 'Transmit register under run'
            self.putx(5, 1, s)
        else:
            self.advance_ann(5, 1)
        if ret[0] & 0x10:
            self.putx(5, 1, 'Wake-up timer')
        else:
            self.advance_ann(5, 1)
        if ret[0] & 0x08:
            self.putx(5, 1, 'External interrupt')
        else:
            self.advance_ann(5, 1)
        if ret[0] & 0x04:
            self.putx(5, 1, 'Low battery')
        else:
            self.advance_ann(5, 1)
        if ret[0] & 0x02:
            self.putx(5, 1, 'FIFO is empty')
        else:
            self.advance_ann(5, 1)
        if ret[0] & 0x01:
            if receiver_enabled:
                s = 'Incoming signal above limit'
            else:
                s = 'Antenna detected RF signal'
            self.putx(5, 1, s)
        else:
            self.advance_ann(5, 1)
        if ret[1] & 0x80:
            self.putx(5, 1, 'Data quality detector')
        else:
            self.advance_ann(5, 1)
        if ret[1] & 0x40:
            self.putx(5, 1, 'Clock recovery locked')
        else:
            self.advance_ann(5, 1)
        self.advance_ann(5, 1)

        self.putx(3, 5, ['AFC offset'])
        if (self.last_status[1] & 0x1F) != (ret[1] & 0x1F):
            self.putx(5, 5, ['Changed', '~'])
        self.last_status = ret

    def handle_cmd(self, cmd, ret):
        if cmd[0] == 0x80:
            self.handle_configuration_cmd(cmd, ret)
        elif cmd[0] == 0x82:
            self.handle_power_management_cmd(cmd, ret)
        elif cmd[0] & 0xF0 == 0xA0:
            self.handle_frequency_setting_cmd(cmd, ret)
        elif cmd[0] == 0xC6:
            self.handle_data_rate_cmd(cmd, ret)
        elif cmd[0] & 0xF8 == 0x90:
            self.handle_receiver_control_cmd(cmd, ret)
        elif cmd[0] == 0xC2:
            self.handle_data_filter_cmd(cmd, ret)
        elif cmd[0] == 0xCA:
            self.handle_fifo_and_reset_cmd(cmd, ret)
        elif cmd[0] == 0xCE:
            self.handle_synchron_pattern_cmd(cmd, ret)
        elif cmd[0] == 0xB0:
            self.handle_fifo_read_cmd(cmd, ret)
        elif cmd[0] == 0xC4:
            self.handle_afc_cmd(cmd, ret)
        elif cmd[0] & 0xFE == 0x98:
            self.handle_transceiver_control_cmd(cmd, ret)
        elif cmd[0] == 0xCC:
            self.handle_pll_setting_cmd(cmd, ret)
        elif cmd[0] == 0xB8:
            self.handle_transmitter_register_cmd(cmd, ret)
        elif cmd[0] == 0xFE:
            self.handle_software_reset_cmd(cmd, ret)
        elif cmd[0] & 0xE0 == 0xE0:
            self.handle_wake_up_timer_cmd(cmd, ret)
        elif cmd[0] == 0xC8:
            self.handle_low_duty_cycle_cmd(cmd, ret)
        elif cmd[0] == 0xC0:
            self.handle_low_battery_detector_cmd(cmd, ret)
        elif cmd[0] == 0x00:
            self.handle_status_read_cmd(cmd, ret)
        else:
            c = '%02x %02x' % tuple(cmd)
            r = '%02x %02x' % tuple(ret)
            self.putx(0, 16, ['Unknown command: %s (reply: %s)!' % (c, r)])

    def decode(self, ss, es, data):
        ptype, mosi, miso = data

        # For now, only use DATA and BITS packets.
        if ptype not in ('DATA', 'BITS'):
            return

        # Store the individual bit values and ss/es numbers. The next packet
        # is guaranteed to be a 'DATA' packet belonging to this 'BITS' one.
        if ptype == 'BITS':
            if mosi is not None:
                self.mosi_bits.extend(reversed(mosi))
            if miso is not None:
                self.miso_bits.extend(reversed(miso))
            return

        # Append new bytes.
        self.mosi_bytes.append(mosi)
        self.miso_bytes.append(miso)

        # All commands consist of 2 bytes.
        if len(self.mosi_bytes) < 2:
            return

        self.row_pos = [0, 8, 8]

        self.handle_cmd(self.mosi_bytes, self.miso_bytes)

        self.mosi_bytes, self.miso_bytes = [], []
        self.mosi_bits, self.miso_bits = [], []
