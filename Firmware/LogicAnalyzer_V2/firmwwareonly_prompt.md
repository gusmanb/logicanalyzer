# Goal 1
Our goal is to make this logic analyzer work with the pico-ice.  The pico-ice is an FPGA developer board for the ICE40UP5K that uses the RP2040 to provide an easy way to program the FPGA.  It also provide a clock and can provide some I/O for the FPGA depending on the designer's wishes.  The RP2040 and FPGA share a number of pins which will make this handy for debugging FPGA projects.  This is the first step to a larger project that will work with other similar development boards like the pico2-ice.  

## How we will proceed
I will have the pico-ice flash already programmed, so all that is required is to pull the \ICE_RESET high which will initiate the process of loading the CRAM in the FPGA from flash.  When it is finished a signal CDONE will be asserted.  When CDONE is asserted I would like to use the PIO to generate the FPGA clock (PIN_CLOCK).  It will be at 10 MHz, but it would be nice to make it obvious how to change the frequency for users.  After that I would like the logic analyzer code in this repository to take over so I can use it to monitor the device.  We need to very carefully make sure that the logic analyzer code does not mess up what we are doing with the FPGA clock it its initialization.  I want to follow the way this has been done in the past, where #defines are made for the PICO and the PICO_2, etc., but use the PICO_ICE, so the code can still be built for the pico, etc.  Please comment things carefully so it is obvious what we are doing.  The logic analyzer connects via USB CDC using escaped binary.  I would like this new firmware to identify that it is running on a pico-ice.
I do not want to use TURBO_MODE for development at all.  It has caused strange things to speed up the RP2350 or RP2040, so let's set that to zero.  I want the software to match what is already there in style.

## Notes for the pico-ice
The pico-ice documentation is at: https://pico-ice.tinyvision.ai/md_getting__started.html   The pico-ice uses the RP2040 to transfer data to and from the FPGA CRAM.  I am including the ICE40UP5K FPGA datasheet converted from pdf to text (Firmware/FPGA-dS.txt) for you to refer to.

### Pinout for the pico-ice
#### For pico-ice (using the RP2040):
GPIO8 = PIN_ICE_SI (ICE_SI, RP2040 ➜ FPGA)
GPIO11 = PIN_ICE_SO (ICE_SO, FPGA ➜ RP2040)
GPIO10 = PIN_ICE_SCK (ICE_SCK)
GPIO9 = PIN_ICE_SSN (sysCONFIG SS, active-low)
GPIO14 = PIN_RAM_SS (External PSRAM SS)
GPIO27 = PIN_FPGA_CRESETN (CRESET_B, active-low)
GPIO26 = PIN_FPGA_CDONE (CDONE)
GPIO24 = PIN_CLOCK (clock to FPGA)
GPIO13/12/15 = LED_R/G/B (active-low)

#### pico-ice pins to capture logic analyzer data from:
GPIO0-GPIO7
GPIO12-GPIO27  Note: GPIO24 and GPIO27 are also outputs, but I wish to be able to monitor them with the logic analyzer.

# Goal 2
We want to do the same thing we already accomplished in Goal 1, but for the pico2-ice.  So we will add the board build for the pico2-ice.  The big differences between the pico-ice and the pico2-ice are processor in the pico2-ice is the RP2350B instead of the RP2040, and the pinout (see below) is a bit different for the pico2-ice.  

## Notes for the pico2-ice
The pico2-ice documentation is at: https://pico2-ice.tinyvision.ai/md_getting__started.html   The pico2-ice uses the RP2040 to transfer data to and from the FPGA CRAM.  I am including the ICE40UP5K FPGA datasheet converted from pdf to text (Firmware/FPGA-dS.txt) for you to refer to.

### Pinout for pico2-ice
#### For pico2-ice (RP2350):

GPIO4 = PIN_ICE_SI (ICE_SI, RP2350 ➜ FPGA)
GPIO7 = PIN_ICE_SO (ICE_SO, FPGA ➜ RP2350)
GPIO6 = PIN_ICE_SCK (ICE_SCK)
GPIO5 = PIN_ICE_SSN (sysCONFIG SS, active-low)
GPIO31 = PIN_FPGA_CRESETN (CRESET_B, active-low) - Correct per pico-ice-sdk
GPIO40 = PIN_FPGA_CDONE (CDONE) - Correct per pico-ice-sdk
GPIO21 = PIN_CLOCK (clock to FPGA)
GPIO1/0/9 = LED_R/G/B (active-low)
No external PSRAM (PIN_RAM_SS = -1)

pico2-ice pins to capture data from:
GPIO20-GPIO43

We want to output the FPGA clock and the CRESETN the same way we did for the pico-ice so we can have them going all the time, but also monitor them.