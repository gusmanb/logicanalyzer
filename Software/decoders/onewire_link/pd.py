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

class SamplerateError(Exception):
    pass

# Timing values in us for the signal at regular and overdrive speed.
timing = {
    'RSTL': {
        'min': {
            False: 480.0,
            True: 48.0,
        },
        'max': {
            False: 960.0,
            True: 80.0,
        },
    },
    'RSTH': {
        'min': {
            False: 480.0,
            True: 48.0,
        },
    },
    'PDH': {
        'min': {
            False: 15.0,
            True: 2.0,
        },
        'max': {
            False: 60.0,
            True: 6.0,
        },
    },
    'PDL': {
        'min': {
            False: 60.0,
            True: 8.0,
        },
        'max': {
            False: 240.0,
            True: 24.0,
        },
    },
    'SLOT': {
        'min': {
            False: 60.0,
            True: 6.0,
        },
        'max': {
            False: 120.0,
            True: 16.0,
        },
    },
    'REC': {
        'min': {
            False: 1.0,
            True: 1.0,
        },
    },
    'LOWR': {
        'min': {
            False: 1.0,
            True: 1.0,
        },
        'max': {
            False: 15.0,
            True: 2.0,
        },
    },
}

class Decoder(srd.Decoder):
    api_version = 3
    id = 'onewire_link'
    name = '1-Wire link layer'
    longname = '1-Wire serial communication bus (link layer)'
    desc = 'Bidirectional, half-duplex, asynchronous serial bus.'
    license = 'gplv2+'
    inputs = ['logic']
    outputs = ['onewire_link']
    tags = ['Embedded/industrial']
    channels = (
        {'id': 'owr', 'name': 'OWR', 'desc': '1-Wire signal line'},
    )
    options = (
        {'id': 'overdrive', 'desc': 'Start in overdrive speed',
            'default': 'no', 'values': ('yes', 'no')},
    )
    annotations = (
        ('bit', 'Bit'),
        ('warning', 'Warning'),
        ('reset', 'Reset'),
        ('presence', 'Presence'),
        ('overdrive', 'Overdrive speed notification'),
    )
    annotation_rows = (
        ('bits', 'Bits', (0, 2, 3)),
        ('info', 'Info', (4,)),
        ('warnings', 'Warnings', (1,)),
    )

    def __init__(self):
        self.reset()

    def reset(self):
        self.samplerate = None
        self.state = 'INITIAL'
        self.present = 0
        self.bit = 0
        self.bit_count = -1
        self.command = 0
        self.overdrive = False
        self.fall = 0
        self.rise = 0

    def start(self):
        self.out_python = self.register(srd.OUTPUT_PYTHON)
        self.out_ann = self.register(srd.OUTPUT_ANN)
        self.overdrive = (self.options['overdrive'] == 'yes')
        self.fall = 0
        self.rise = 0
        self.bit_count = -1

    def putm(self, data):
        self.put(0, 0, self.out_ann, data)

    def putpfs(self, data):
        self.put(self.fall, self.samplenum, self.out_python, data)

    def putfs(self, data):
        self.put(self.fall, self.samplenum, self.out_ann, data)

    def putfr(self, data):
        self.put(self.fall, self.rise, self.out_ann, data)

    def putprs(self, data):
        self.put(self.rise, self.samplenum, self.out_python, data)

    def putrs(self, data):
        self.put(self.rise, self.samplenum, self.out_ann, data)

    def checks(self):
        # Check if samplerate is appropriate.
        if self.options['overdrive'] == 'yes':
            if self.samplerate < 2000000:
                self.putm([1, ['Sampling rate is too low. Must be above ' +
                               '2MHz for proper overdrive mode decoding.']])
            elif self.samplerate < 5000000:
                self.putm([1, ['Sampling rate is suggested to be above 5MHz ' +
                               'for proper overdrive mode decoding.']])
        else:
            if self.samplerate < 400000:
                self.putm([1, ['Sampling rate is too low. Must be above ' +
                               '400kHz for proper normal mode decoding.']])
            elif self.samplerate < 1000000:
                self.putm([1, ['Sampling rate is suggested to be above ' +
                               '1MHz for proper normal mode decoding.']])

    def metadata(self, key, value):
        if key != srd.SRD_CONF_SAMPLERATE:
            return
        self.samplerate = value

    def wait_falling_timeout(self, start, t):
        # Wait until either a falling edge is seen, and/or the specified
        # number of samples have been skipped (i.e. time has passed).
        cnt = int((t[self.overdrive] / 1000000.0) * self.samplerate)
        samples_to_skip = (start + cnt) - self.samplenum
        samples_to_skip = samples_to_skip if (samples_to_skip > 0) else 0
        return self.wait([{0: 'f'}, {'skip': samples_to_skip}])

    def decode(self):
        if not self.samplerate:
            raise SamplerateError('Cannot decode without samplerate.')
        self.checks()
        while True:
            # State machine.
            if self.state == 'INITIAL': # Unknown initial state.
                # Wait until we reach the idle high state.
                self.wait({0: 'h'})
                self.rise = self.samplenum
                self.state = 'IDLE'
            elif self.state == 'IDLE': # Idle high state.
                # Wait for falling edge.
                self.wait({0: 'f'})
                self.fall = self.samplenum
                # Get time since last rising edge.
                time = ((self.fall - self.rise) / self.samplerate) * 1000000.0
                if self.rise > 0 and \
                    time < timing['REC']['min'][self.overdrive]:
                    self.putfr([1, ['Recovery time not long enough'
                        'Recovery too short',
                        'REC < ' + str(timing['REC']['min'][self.overdrive])]])
                # A reset pulse or slot can start on a falling edge.
                self.state = 'LOW'
                # TODO: Check minimum recovery time.
            elif self.state == 'LOW': # Reset pulse or slot.
                # Wait for rising edge.
                self.wait({0: 'r'})
                self.rise = self.samplenum
                # Detect reset or slot base on timing.
                time = ((self.rise - self.fall) / self.samplerate) * 1000000.0
                if time >= timing['RSTL']['min'][False]: # Normal reset pulse.
                    if time > timing['RSTL']['max'][False]:
                        self.putfr([1, ['Too long reset pulse might mask interrupt ' +
                            'signalling by other devices',
                            'Reset pulse too long',
                            'RST > ' + str(timing['RSTL']['max'][False])]])
                    # Regular reset pulse clears overdrive speed.
                    if self.overdrive:
                        self.putfr([4, ['Exiting overdrive mode', 'Overdrive off']])
                    self.overdrive = False
                    self.putfr([2, ['Reset', 'Rst', 'R']])
                    self.state = 'PRESENCE DETECT HIGH'
                elif self.overdrive == True and \
                    time >= timing['RSTL']['min'][self.overdrive] and \
                    time < timing['RSTL']['max'][self.overdrive]:
                    # Overdrive reset pulse.
                    self.putfr([2, ['Reset', 'Rst', 'R']])
                    self.state = 'PRESENCE DETECT HIGH'
                elif time < timing['SLOT']['max'][self.overdrive]:
                    # Read/write time slot.
                    if time < timing['LOWR']['min'][self.overdrive]:
                        self.putfr([1, ['Low signal not long enough',
                            'Low too short',
                            'LOW < ' + str(timing['LOWR']['min'][self.overdrive])]])
                    if time < timing['LOWR']['max'][self.overdrive]:
                        self.bit = 1 # Short pulse is a 1 bit.
                    else:
                        self.bit = 0 # Long pulse is a 0 bit.
                    # Wait for end of slot.
                    self.state = 'SLOT'
                else:
                    # Timing outside of known states.
                    self.putfr([1, ['Erroneous signal', 'Error', 'Err', 'E']])
                    self.state = 'IDLE'
            elif self.state == 'PRESENCE DETECT HIGH': # Wait for slave presence signal.
                # Wait for a falling edge and/or presence detect signal.
                self.wait_falling_timeout(self.rise, timing['PDH']['max'])

                # Calculate time since rising edge.
                time = ((self.samplenum - self.rise) / self.samplerate) * 1000000.0

                if self.matched[0] and not self.matched[1]:
                    # Presence detected.
                    if time < timing['PDH']['min'][self.overdrive]:
                        self.putrs([1, ['Presence detect signal is too early',
                            'Presence detect too early',
                            'PDH < ' + str(timing['PDH']['min'][self.overdrive])]])
                    self.fall = self.samplenum
                    self.state = 'PRESENCE DETECT LOW'
                else: # No presence detected.
                    self.putrs([3, ['Presence: false', 'Presence', 'Pres', 'P']])
                    self.putprs(['RESET/PRESENCE', False])
                    self.state = 'IDLE'
            elif self.state == 'PRESENCE DETECT LOW': # Slave presence signalled.
                # Wait for end of presence signal (on rising edge).
                self.wait({0: 'r'})
                # Calculate time since start of presence signal.
                time = ((self.samplenum - self.fall) / self.samplerate) * 1000000.0
                if time < timing['PDL']['min'][self.overdrive]:
                    self.putfs([1, ['Presence detect signal is too short',
                        'Presence detect too short',
                        'PDL < ' + str(timing['PDL']['min'][self.overdrive])]])
                elif time > timing['PDL']['max'][self.overdrive]:
                    self.putfs([1, ['Presence detect signal is too long',
                        'Presence detect too long',
                        'PDL > ' + str(timing['PDL']['max'][self.overdrive])]])
                if time > timing['RSTH']['min'][self.overdrive]:
                    self.rise = self.samplenum
                # Wait for end of presence detect.
                self.state = 'PRESENCE DETECT'

            # End states (for additional checks).
            if self.state == 'SLOT': # Wait for end of time slot.
                # Wait for a falling edge and/or end of timeslot.
                self.wait_falling_timeout(self.fall, timing['SLOT']['min'])

                if self.matched[0] and not self.matched[1]:
                    # Low detected before end of slot.
                    self.putfs([1, ['Time slot not long enough',
                        'Slot too short',
                        'SLOT < ' + str(timing['SLOT']['min'][self.overdrive])]])
                    # Don't output invalid bit.
                    self.fall = self.samplenum
                    self.state = 'LOW'
                else: # End of time slot.
                    # Output bit.
                    self.putfs([0, ['Bit: %d' % self.bit, '%d' % self.bit]])
                    self.putpfs(['BIT', self.bit])
                    # Save command bits.
                    if self.bit_count >= 0:
                        self.command += (self.bit << self.bit_count)
                        self.bit_count += 1
                    # Check for overdrive ROM command.
                    if self.bit_count >= 8:
                        if self.command == 0x3c or self.command == 0x69:
                            self.overdrive = True
                            self.put(self.samplenum, self.samplenum,
                                self.out_ann,
                                [4, ['Entering overdrive mode', 'Overdrive on']])
                        self.bit_count = -1
                    self.state = 'IDLE'

            if self.state == 'PRESENCE DETECT':
                # Wait for a falling edge and/or end of presence detect.
                self.wait_falling_timeout(self.rise, timing['RSTH']['min'])

                if self.matched[0] and not self.matched[1]:
                    # Low detected before end of presence detect.
                    self.putfs([1, ['Presence detect not long enough',
                        'Presence detect too short',
                        'RTSH < ' + str(timing['RSTH']['min'][self.overdrive])]])
                    # Inform about presence detected.
                    self.putrs([3, ['Slave presence detected', 'Slave present',
                        'Present', 'P']])
                    self.putprs(['RESET/PRESENCE', True])
                    self.fall = self.samplenum
                    self.state = 'LOW'
                else: # End of time slot.
                    # Inform about presence detected.
                    self.putrs([3, ['Presence: true', 'Presence', 'Pres', 'P']])
                    self.putprs(['RESET/PRESENCE', True])
                    self.rise = self.samplenum
                    # Start counting the first 8 bits to get the ROM command.
                    self.bit_count = 0
                    self.command = 0
                    self.state = 'IDLE'
