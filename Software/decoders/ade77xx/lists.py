##
## This file is part of the libsigrokdecode project.
##
## Copyright (C) 2017 Karl Palsson <karlp@etactica.com>
##
## Permission is hereby granted, free of charge, to any person obtaining a copy
## of this software and associated documentation files (the "Software"), to deal
## in the Software without restriction, including without limitation the rights
## to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
## copies of the Software, and to permit persons to whom the Software is
## furnished to do so, subject to the following conditions:
##
## The above copyright notice and this permission notice shall be included in all
## copies or substantial portions of the Software.
##
## THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
## IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
## FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
## AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
## LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
## OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
## SOFTWARE.

from collections import OrderedDict

# Generated from datasheet rev E, using tabula.
regs = OrderedDict([
    (0x1, ('AWATTHR', 'Watt-Hour Accumulation Register for Phase A. Active power is accumulated over time in this read-only register. The AWATTHR register can hold a maximum of 0.52 seconds of active energy information with full-scale analog inputs before it overflows (see the Active Energy Calculation section). Bit 0 and Bit 1 of the COMPMODE register determine how the active energy is processed from the six analog inputs.', 'R', 16, 'S', 0x0)),
    (0x2, ('BWATTHR', 'Watt-Hour Accumulation Register for Phase B.', 'R', 16, 'S', 0x0)),
    (0x3, ('CWATTHR', 'Watt-Hour Accumulation Register for Phase C.', 'R', 16, 'S', 0x0)),
    (0x4, ('AVARHR', 'VAR-Hour Accumulation Register for Phase A. Reactive power is accumulated over time in this read-only register. The AVARHR register can hold a maximum of 0.52 seconds of reactive energy information with full-scale analog inputs before it overflows (see the Reactive Energy Calculation section). Bit 0 and Bit 1 of the COMPMODE register determine how the reactive energy is processed from the six analog inputs.', 'R', 16, 'S', 0x0)),
    (0x5, ('BVARHR', 'VAR-Hour Accumulation Register for Phase B.', 'R', 16, 'S', 0x0)),
    (0x6, ('CVARHR', 'VAR-Hour Accumulation Register for Phase C.', 'R', 16, 'S', 0x0)),
    (0x7, ('AVAHR', 'VA-Hour Accumulation Register for Phase A. Apparent power is accumulated over time in this read-only register. The AVAHR register can hold a maximum of 1.15 seconds of apparent energy information with full-scale analog inputs before it overflows (see the Apparent Energy Calculation section). Bit 0 and Bit 1 of the COMPMODE register determine how the apparent energy is processed from the six analog inputs.', 'R', 16, 'S', 0x0)),
    (0x8, ('BVAHR', 'VA-Hour Accumulation Register for Phase B.', 'R', 16, 'S', 0x0)),
    (0x9, ('CVAHR', 'VA-Hour Accumulation Register for Phase C.', 'R', 16, 'S', 0x0)),
    (0xa, ('AIRMS', 'Phase A Current Channel RMS Register. The register contains the rms component of the Phase A input of the current channel. The source is selected by data bits in the mode register.', 'R', 24, 'S', 0x0)),
    (0xb, ('BIRMS', 'Phase B Current Channel RMS Register.', 'R', 24, 'S', 0x0)),
    (0xc, ('CIRMS', 'Phase C Current Channel RMS Register.', 'R', 24, 'S', 0x0)),
    (0xd, ('AVRMS', 'Phase A Voltage Channel RMS Register.', 'R', 24, 'S', 0x0)),
    (0xe, ('BVRMS', 'Phase B Voltage Channel RMS Register.', 'R', 24, 'S', 0x0)),
    (0xf, ('CVRMS', 'Phase C Voltage Channel RMS Register.', 'R', 24, 'S', 0x0)),
    (0x10, ('FREQ', 'Frequency of the Line Input Estimated by the Zero-Crossing Processing. It can also display the period of the line input. Bit 7 of the LCYCMODE register determines if the reading is frequency or period. Default is frequency. Data Bit 0 and Bit 1 of the MMODE register determine the voltage channel used for the frequency or period calculation.', 'R', 12, 'U', 0x0)),
    (0x11, ('TEMP', 'Temperature Register. This register contains the result of the latest temperature conversion. Refer to the Temperature Measurement section for details on how to interpret the content of this register.', 'R', 8, 'S', 0x0)),
    (0x12, ('WFORM', 'Waveform Register. This register contains the digitized waveform of one of the six analog inputs or the digitized power waveform. The source is selected by Data Bit 0 to Bit 4 in the WAVMODE register.', 'R', 24, 'S', 0x0)),
    (0x13, ('OPMODE', 'Operational Mode Register. This register defines the general configuration of the ADE7758 (see Table 18).', 'R/W', 8, 'U', 0x4)),
    (0x14, ('MMODE', 'Measurement Mode Register. This register defines the channel used for period and peak detection measurements (see Table 19).', 'R/W', 8, 'U', 0xfc)),
    (0x15, ('WAVMODE', 'Waveform Mode Register. This register defines the channel and sampling frequency used in the waveform sampling mode (see Table 20).', 'R/W', 8, 'U', 0x0)),
    (0x16, ('COMPMODE', 'Computation Mode Register. This register configures the formula applied for the energy and line active energy measurements (see Table 22).', 'R/W', 8, 'U', 0x1c)),
    (0x17, ('LCYCMODE', 'Line Cycle Mode Register. This register configures the line cycle accumulation mode for WATT-HR', 'R/W', 8, 'U', 0x78)),
    (0x18, ('Mask', 'IRQ Mask Register. It determines if an interrupt event generates an active-low output at the IRQ pin (see the Interrupts section).', 'R/W', 24, 'U', 0x0)),
    (0x19, ('Status', 'IRQ Status Register. This register contains information regarding the source of the ADE7758 interrupts (see the Interrupts section).', 'R', 24, 'U', 0x0)),
    (0x1a, ('RSTATUS', 'IRQ Reset Status Register. Same as the STATUS register, except that its contents are reset to 0 (all flags cleared) after a read operation.', 'R', 24, 'U', 0x0)),
    (0x1b, ('ZXTOUT', 'Zero-Cross Timeout Register. If no zero crossing is detected within the time period specified by this register', 'R/W', 16, 'U', 0xffff)),
    (0x1c, ('LINECYC', 'Line Cycle Register. The content of this register sets the number of half-line cycles that the active', 'R/W', 16, 'U', 0xffff)),
    (0x1d, ('SAGCYC', 'SAG Line Cycle Register. This register specifies the number of consecutive half-line cycles where voltage channel input may fall below a threshold level. This register is common to the three line voltage SAG detection. The detection threshold is specified by the SAGLVL register (see the Line Voltage SAG Detection section).', 'R/W', 8, 'U', 0xff)),
    (0x1e, ('SAGLVL', 'SAG Voltage Level. This register specifies the detection threshold for the SAG event. This register is common to all three phases’ line voltage SAG detections. See the description of the SAGCYC register for details.', 'R/W', 8, 'U', 0x0)),
    (0x1f, ('VPINTLVL', 'Voltage Peak Level Interrupt Threshold Register. This register sets the level of the voltage peak detection. Bit 5 to Bit 7 of the MMODE register determine which phases are to be monitored. If the selected voltage phase exceeds this level', 'R/W', 8, 'U', 0xff)),
    (0x20, ('IPINTLVL', 'Current Peak Level Interrupt Threshold Register. This register sets the level of the current peak detection. Bit 5 to Bit 7 of the MMODE register determine which phases are to be monitored. If the selected current phase exceeds this level', 'R/W', 8, 'U', 0xff)),
    (0x21, ('VPEAK', 'Voltage Peak Register. This register contains the value of the peak voltage waveform that has occurred within a fixed number of half-line cycles. The number of half-line cycles is set by the LINECYC register.', 'R', 8, 'U', 0x0)),
    (0x22, ('IPEAK', 'Current Peak Register. This register holds the value of the peak current waveform that has occurred within a fixed number of half-line cycles. The number of half-line cycles is set by the LINECYC register.', 'R', 8, 'U', 0x0)),
    (0x23, ('Gain', 'PGA Gain Register. This register is used to adjust the gain selection for the PGA in the current and voltage channels (see the Analog Inputs section).', 'R/W', 8, 'U', 0x0)),
    (0x24, ('AVRMSGAIN', 'Phase A VRMS Gain Register. The range of the voltage rms calculation can be adjusted by writing to this register. It has an adjustment range of ±50% with a resolution of 0.0244%/LSB.', 'R/W', 12, 'S', 0x0)),
    (0x25, ('BVRMSGAIN', 'Phase B VRMS Gain Register.', 'R/W', 12, 'S', 0x0)),
    (0x26, ('CVRMSGAIN', 'Phase C VRMS Gain Register.', 'R/W', 12, 'S', 0x0)),
    (0x27, ('AIGAIN', 'Phase A Current Gain Register. This register is not recommended to be used and it should be kept at 0', 'R/W', 12, 'S', 0x0)),
    (0x28, ('BIGAIN', 'Phase B Current Gain Register. This register is not recommended to be used and it should be kept at 0', 'R/W', 12, 'S', 0x0)),
    (0x29, ('CIGAIN', 'Phase C Current Gain Register. This register is not recommended to be used and it should be kept at 0', 'R/W', 12, 'S', 0x0)),
    (0x2a, ('AWG', 'Phase A Watt Gain Register. The range of the watt calculation can be adjusted by writing to this register. It has an adjustment range of ±50% with a resolution of 0.0244%/LSB.', 'R/W', 12, 'S', 0x0)),
    (0x2b, ('BWG', 'Phase B Watt Gain Register.', 'R/W', 12, 'S', 0x0)),
    (0x2c, ('CWG', 'Phase C Watt Gain Register.', 'R/W', 12, 'S', 0x0)),
    (0x2d, ('AVARG', 'Phase A VAR Gain Register. The range of the VAR calculation can be adjusted by writing to this register. It has an adjustment range of ±50% with a resolution of 0.0244%/LSB.', 'R/W', 12, 'S', 0x0)),
    (0x2e, ('BVARG', 'Phase B VAR Gain Register.', 'R/W', 12, 'S', 0x0)),
    (0x2f, ('CVARG', 'Phase C VAR Gain Register.', 'R/W', 12, 'S', 0x0)),
    (0x30, ('AVAG', 'Phase A VA Gain Register. The range of the VA calculation can be adjusted by writing to this register. It has an adjustment range of ±50% with a resolution of 0.0244%/LSB.', 'R/W', 12, 'S', 0x0)),
    (0x31, ('BVAG', 'Phase B VA Gain Register.', 'R/W', 12, 'S', 0x0)),
    (0x32, ('CVAG', 'Phase C VA Gain Register.', 'R/W', 12, 'S', 0x0)),
    (0x33, ('AVRMSOS', 'Phase A Voltage RMS Offset Correction Register.', 'R/W', 12, 'S', 0x0)),
    (0x34, ('BVRMSOS', 'Phase B Voltage RMS Offset Correction Register.', 'R/W', 12, 'S', 0x0)),
    (0x35, ('CVRMSOS', 'Phase C Voltage RMS Offset Correction Register.', 'R/W', 12, 'S', 0x0)),
    (0x36, ('AIRMSOS', 'Phase A Current RMS Offset Correction Register.', 'R/W', 12, 'S', 0x0)),
    (0x37, ('BIRMSOS', 'Phase B Current RMS Offset Correction Register.', 'R/W', 12, 'S', 0x0)),
    (0x38, ('CIRMSOS', 'Phase C Current RMS Offset Correction Register.', 'R/W', 12, 'S', 0x0)),
    (0x39, ('AWATTOS', 'Phase A Watt Offset Calibration Register.', 'R/W', 12, 'S', 0x0)),
    (0x3a, ('BWATTOS', 'Phase B Watt Offset Calibration Register.', 'R/W', 12, 'S', 0x0)),
    (0x3b, ('CWATTOS', 'Phase C Watt Offset Calibration Register.', 'R/W', 12, 'S', 0x0)),
    (0x3c, ('AVAROS', 'Phase A VAR Offset Calibration Register.', 'R/W', 12, 'S', 0x0)),
    (0x3d, ('BVAROS', 'Phase B VAR Offset Calibration Register.', 'R/W', 12, 'S', 0x0)),
    (0x3e, ('CVAROS', 'Phase C VAR Offset Calibration Register.', 'R/W', 12, 'S', 0x0)),
    (0x3f, ('APHCAL', 'Phase A Phase Calibration Register. The phase relationship between the current and voltage channel can be adjusted by writing to this signed 7-bit register (see the Phase Compensation section).', 'R/W', 7, 'S', 0x0)),
    (0x40, ('BPHCAL', 'Phase B Phase Calibration Register.', 'R/W', 7, 'S', 0x0)),
    (0x41, ('CPHCAL', 'Phase C Phase Calibration Register.', 'R/W', 7, 'S', 0x0)),
    (0x42, ('WDIV', 'Active Energy Register Divider.', 'R/W', 8, 'U', 0x0)),
    (0x43, ('VARDIV', 'Reactive Energy Register Divider.', 'R/W', 8, 'U', 0x0)),
    (0x44, ('VADIV', 'Apparent Energy Register Divider.', 'R/W', 8, 'U', 0x0)),
    (0x45, ('APCFNUM', 'Active Power CF Scaling Numerator Register. The content of this register is used in the numerator of the APCF output scaling calculation. Bits [15:13] indicate reverse polarity active power measurement for Phase A', 'R/W', 16, 'U', 0x0)),
    (0x46, ('APCFDEN', 'Active Power CF Scaling Denominator Register. The content of this register is used in the denominator of the APCF output scaling.', 'R/W', 12, 'U', 0x3f)),
    (0x47, ('VARCFNUM', 'Reactive Power CF Scaling Numerator Register. The content of this register is used in the numerator of the VARCF output scaling. Bits [15:13] indicate reverse polarity reactive power measurement for Phase A', 'R/W', 16, 'U', 0x0)),
    (0x48, ('VARCFDEN', 'Reactive Power CF Scaling Denominator Register. The content of this register is used in the denominator of the VARCF output scaling.', 'R/W', 12, 'U', 0x3f)),
    (0x7e, ('CHKSUM', 'Checksum Register. The content of this register represents the sum of all the ones in the last register read from the SPI port.', 'R', 8, 'U', None)),
    (0x7f, ('Version', 'Version of the Die.', 'R', 8, 'U', None)),
])
