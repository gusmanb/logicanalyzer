# Using the Logic Analyzer with pico2-ice

The **pico2-ice** is an FPGA development board featuring the **ICE40UP5K FPGA** paired with the **RP2350B** microcontroller. This guide explains how to use Dr. Gusman's Logic Analyzer firmware with the pico2-ice board for debugging FPGA projects.

## Overview

The pico2-ice Logic Analyzer firmware provides a seamless integration between FPGA development and logic analysis. The RP2350B handles both FPGA configuration management and high-speed logic capture, making it an ideal tool for FPGA debugging and verification.

## Prerequisites

### 1. FPGA Flash Programming Required

**⚠️ IMPORTANT: You must program the FPGA flash memory before using the Logic Analyzer.**

The pico2-ice Logic Analyzer firmware does **NOT** program the FPGA flash. You need to:

1. Program your FPGA bitstream to the onboard flash memory using standard pico2-ice tools
2. Ensure your FPGA design is stored in flash and ready for configuration
3. Only then use the Logic Analyzer firmware

**Programming Tools:**
- Use the official pico2-ice SDK and tools for flash programming
- Refer to the [pico2-ice documentation](https://pico2-ice.tinyvision.ai/md_getting__started.html) for detailed programming instructions
- Popular tools include `iceprog`, `openFPGALoader`, or the pico2-ice MicroPython utilities

### 2. Hardware Requirements

- pico2-ice development board
- USB cable for connection to host computer
- FPGA bitstream programmed in flash memory

## How It Works

### FPGA Initialization Sequence

When the Logic Analyzer firmware starts:

1. **Reset Release**: The RP2350B pulls `CRESETN` (GPIO31) high, releasing the FPGA from reset
2. **Clock Start**: Due to a hardware bug with CDONE voltage levels, the RP2350B immediately starts the **10MHz clock** on `PIN_CLOCK` (GPIO21) using PIO
3. **Configuration Loading**: The ICE40UP5K automatically loads its configuration from onboard flash memory
4. **Configuration Complete**: The FPGA asserts `CDONE` (GPIO40) when configuration is successful (though voltage levels may not be reliably readable)
5. **Logic Analysis Ready**: The Logic Analyzer is now ready to capture signals while maintaining FPGA operation

### CDONE Hardware Bug Workaround

**Note**: The pico2-ice has a hardware issue where the CDONE signal voltage is below the RP2350B's input threshold. The firmware works around this by:
- Starting the FPGA clock immediately after releasing reset
- Not waiting for CDONE assertion (since it's not reliably readable)
- Providing sufficient time for FPGA configuration to complete

### Dual Functionality

The firmware provides **dual functionality**:
- **FPGA Support**: Manages FPGA configuration, reset control, and clock generation
- **Logic Analysis**: Captures high-speed digital signals from GPIO pins for analysis

## Pin Configuration

### FPGA Control Pins
- **GPIO31** (`CRESETN`) - FPGA reset control (active-low) - **OUTPUT**
- **GPIO40** (`CDONE`) - FPGA configuration done status (unreliable voltage) - **INPUT**
- **GPIO21** (`PIN_CLOCK`) - FPGA clock output (10MHz) - **OUTPUT**

### SPI Flash Programming Pins
- **GPIO4** (`ICE_SI`) - SPI MOSI to FPGA
- **GPIO7** (`ICE_SO`) - SPI MISO from FPGA  
- **GPIO6** (`ICE_SCK`) - SPI clock
- **GPIO5** (`ICE_SSN`) - SPI chip select (active-low)
- **No external PSRAM** (PIN_RAM_SS = -1)

### Logic Analyzer Capture Pins and Channel Mapping

The Logic Analyzer can monitor these GPIO pins:
- **GPIO20-GPIO43** - High-speed I/O range (excluding conflicting pins)

**Channel to GPIO Pin Mapping:**
```
Logic Analyzer Channel → GPIO Pin
Channel 01 → GPIO20
Channel 02 → GPIO21 (FPGA Clock) 🕐
Channel 03 → GPIO22
Channel 04 → GPIO23
Channel 05 → GPIO24
Channel 06 → GPIO25
Channel 07 → GPIO26
Channel 08 → GPIO27
Channel 09 → GPIO28
Channel 10 → GPIO29
Channel 11 → GPIO30
Channel 12 → GPIO31 (CRESETN) 🔄
Channel 13 → GPIO32
Channel 14 → GPIO33
Channel 15 → GPIO34
Channel 16 → GPIO35
Channel 17 → GPIO36
Channel 18 → GPIO37
Channel 19 → GPIO38
Channel 20 → GPIO39
Channel 21 → GPIO40 (CDONE) 📡
Channel 22 → GPIO41
Channel 23 → GPIO42
Channel 24 → GPIO43

Note:  GPIO2 and GPIO3 must be jumpered if you want to use COMPLEX triggering (triggering on a pattern).  You can change these LogicAnalyzer_Board_Settings.h if you want other pins on the RP2350B.
Note: 🕐 = 10MHz FPGA clock output
📡 = FPGA configuration done status (unreliable voltage)  
🔄 = FPGA reset control (active-low)
<!-- Test update to verify GitHub sync -->
```

**Important Notes:**
- **Channel 02** (GPIO21) shows the 10MHz FPGA clock - useful for timing reference
- **Channel 12** (GPIO31) shows FPGA reset control (should stay high during normal operation)  
- **Channel 21** (GPIO40) shows FPGA configuration status (voltage may be unreliable)

**Note**: GPIO21 and GPIO31 are **output pins** but can still be **monitored** by the Logic Analyzer. The firmware uses universal pin state preservation to maintain their output state while allowing signal capture. **All pin configurations remain unchanged** after capture operations.

### Status LEDs (RGB LED)
- **GPIO1** - Red LED (active-low)
- **GPIO0** - Green LED (active-low)  
- **GPIO9** - Blue LED (active-low)

## Clock Configuration

The FPGA receives a **10MHz clock** generated by the RP2350B's PIO system.

### Changing the FPGA Clock Frequency

To modify the clock frequency, edit the `fpga_start_clock()` function in `LogicAnalyzer_FPGA.c`:

```c
bool fpga_start_clock(void) {
    // Calculate divider for desired frequency
    float target_freq = 10000000.0f;  // 10MHz
    
    // For different frequencies:
    // 5MHz:  float target_freq = 5000000.0f;
    // 25MHz: float target_freq = 25000000.0f;
    
    float system_freq = (float)clock_get_hz(clk_sys);
    float clkdiv = system_freq / (target_freq * 2.0f);
    sm_config_set_clkdiv(&c, clkdiv);
}
```

## Usage Instructions

### 1. Build and Flash the Firmware

```bash
# Configure for pico2-ice
cmake -DBOARD_TYPE=BOARD_PICO2_ICE ..
make -j8

# Flash the resulting .uf2 file to your pico2-ice
```

### 2. Connect to Logic Analyzer Software

1. Connect the pico2-ice to your computer via USB
2. The device will identify as "Logic Analyzer (PICO2_ICE)"
3. Use Dr. Gusman's Logic Analyzer software to connect
4. The software communicates via USB CDC using escaped binary protocol

### 3. Verify FPGA Operation

Before capturing signals:
1. Check that your FPGA configuration loaded successfully (by observing FPGA I/O behavior)
2. Verify the 10MHz clock is present on GPIO21 (Channel 02)
3. Confirm CRESETN (GPIO31) is at 3.3V (Channel 12)
4. Note that CDONE (GPIO40) voltage may not be reliably readable due to hardware bug

### 4. Capture Logic Signals

- Configure capture channels in the Logic Analyzer software
- You can monitor both FPGA I/O and RP2350B GPIO pins
- GPIO21 (FPGA clock) and GPIO31 (CRESETN) can be captured while maintaining their output functions

## Advanced Features

### Multi-Core Architecture

The pico2-ice Logic Analyzer uses both RP2350B cores:
- **Core 0**: Main Logic Analyzer functionality, USB communication, FPGA management
- **Core 1**: Available for user applications

**Core 1 is available for custom user code!** You can implement additional functionality on Core 1 while the Logic Analyzer runs on Core 0.

### Universal Pin State Preservation

The firmware implements complete pin state preservation:
- **All pin states are preserved** during and after Logic Analyzer capture operations
- **Output pins** (like FPGA clock) maintain their output state and continue driving
- **Input pins** maintain their input configuration and pull-up/pull-down settings
- **High-Z pins** remain in high-impedance state  
- **Core 1 user applications** are completely unaffected by Logic Analyzer operations
- **FPGA applications** continue running without any pin state disruption
- Logic Analyzer only **reads** pin states - never changes pin configurations

### Real-time FPGA Monitoring

The Logic Analyzer can capture FPGA signals in real-time while the FPGA continues normal operation:
- Monitor FPGA I/O signals
- Debug timing relationships
- Capture FPGA clock for timing reference
- Analyze FPGA-to-RP2350B communication

## Hardware Differences from pico-ice

### Key Changes in pico2-ice:
- **MCU**: RP2350B (80-pin package) instead of RP2040
- **GPIO Range**: Uses GPIO20-43 instead of GPIO0-27
- **FPGA Pins**: Different GPIO assignments (CRESETN=GPIO31, CLOCK=GPIO21, CDONE=GPIO40)
- **PSRAM**: No external PSRAM (PIN_RAM_SS = -1)
- **CDONE Bug**: Hardware voltage level issue requires immediate clock start workaround
- **RGB LED**: Single RGB LED on GPIO0/1/9 instead of separate LEDs

## Troubleshooting

### FPGA Not Configuring
- Verify FPGA flash is programmed with valid bitstream
- Check that CRESETN (GPIO31) reaches 3.3V
- The FPGA clock starts immediately - don't rely on CDONE signal due to voltage bug
- Allow sufficient time (1000ms) for FPGA configuration to complete

### No FPGA Clock
- Clock starts immediately after reset release (doesn't wait for CDONE)
- Check GPIO21 with oscilloscope for 10MHz signal
- Ensure Logic Analyzer capture isn't interfering with clock output

### CDONE Signal Issues
- **Known Hardware Bug**: CDONE voltage may not reach proper logic HIGH level
- Don't rely on CDONE for determining FPGA configuration status
- Use FPGA I/O behavior to verify successful configuration instead

### Logic Analyzer Connection Issues
- Verify USB connection and drivers
- Check that device identifies as "Logic Analyzer (PICO2_ICE)"
- Ensure Logic Analyzer software supports the pico2-ice variant

## Technical Specifications

- **MCU**: RP2350B (Dual ARM Cortex-M33 @ 125MHz, 80-pin package)
- **FPGA**: ICE40UP5K (5K LUTs, 128KB BRAM, 8 DSP blocks)
- **Logic Analyzer Channels**: 24 channels (GPIO20-43)
- **Max Sample Rate**: 100 Msps
- **Capture Memory**: 384KB buffer (3x larger than RP2040 boards)
- **FPGA Clock**: 10MHz (user configurable)
- **Communication**: USB CDC (escaped binary protocol)
- **Special Features**: Immediate clock start (CDONE bug workaround)

## References

- [pico2-ice Official Documentation](https://pico2-ice.tinyvision.ai/md_getting__started.html)
- [ICE40UP5K FPGA Datasheet](https://www.latticesemi.com/en/Products/FPGAandCPLD/iCE40UltraPlus)
- [Dr. Gusman's Logic Analyzer Project](https://github.com/gusmanb/logicanalyzer)
- [RP2350B Datasheet](https://datasheets.raspberrypi.com/rp2350/rp2350-datasheet.pdf)

## Contributing

This pico2-ice support is designed to be merged with Dr. Gusman's main Logic Analyzer repository. Contributions, bug reports, and improvements are welcome!

---

**Note**: This firmware provides FPGA development board support while maintaining full compatibility with the original Logic Analyzer functionality. The immediate clock start workaround ensures reliable FPGA operation despite the CDONE hardware bug, and universal pin state preservation ensures reliable operation with any FPGA design.