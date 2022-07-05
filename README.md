# LogicAnalyzer
----
## Description
Cheap 24 channel logic analyzer with 100Msps, 32k samples deep, edge triggers and pattern triggers.

----
## Overview
LogicAnalyzer is a very cheap analyzer based in a Raspberry Pico. The analyzer offers up to 24 digital channels, pre and post trigger sampling, edge trigger and pattern trigger up to 16 bits.

The most basic version is purely a Pico as-is, you only need to short GPIO0 and GPIO1, upload the firmware and you're good to go.
Of course this has some limitations as the Pico only supports 3.3v, if you want to use it to diagnose 5v signals I also have designed a fast level shifter board.

Additionally to the hardware the logic analyzer also includes a powerful software (Windows only for now) where you can visualize the captured data, export captures, use protocol analyzers, etc.

## About logic analyzers and triggers

A logic analyzer only cares about logic states of lines, so without thinking much about it you may think that any microcontroller using DMA channels that read GPIO values would be more than enough, but that is the "easy" part of a logic analyzer, the problem comes when you need to trigger the captures based in GPIO states and you want also to have data captured previously and aftetr the trigger happens.

For that, you need to compare the read values from the GPIOs check if the pin or pins values match the requested trigger and you must do it as fast as you want to capture, so for example, the most basic comparison will at least consume 3 or 4 instructions, if each instruction is 1 to 4 cycles (more or less, I'm thinking in ARM processors) then you will use up to 16 cycles to read a sample, so you would need a 1.6Ghz CPU to sample at 100Msps.

So, how the heck the pico is able to achieve this? Well, the key are the PIO units, these units are a wonder, they are coprocessors explicitly dessigned to handle IO, it uses a very restricted and deterministic assembler (only nine instructions that each take a single cycle to execuet) but extremely efficient, so efficient that with only two instructions is possible to create a loop that captures GPIO data up to 30 bits and redirects the program flow based in the status of one of these GPIOs.

Of course there are some limitations, that two-instruction loop can only change the execution flow based on a GPIO pin, it can't branch based on a pattern (using only two instructions) but as we have more than one unit (each pico has two units and each unit has four state machines, so you can run in parallel up to 8 programs) we can abuse a bit the system and create a sepparate trigger program that notifies the capture program using a pin, that's why GPIO0 and GPIO1 are shorted.

The analyzer described here has three trigger modes: edge trigger, fast pattern trigger and complex pattern trigger.

The edge trigger uses a single program, that's the basic version that uses only two instructions, runs up to 100Msps and the triggering is synchronized with the captures.

The complex triggers is the first that uses two programs, one to capture and other for the trigger. The complex trigger supports patterns up to 16 bits matched from consecutive channels in the first 16 ones.
Having two programs is key to keep sampling up to 100Msps, the trigger program uses three instructions so its speed is limited to 66Msps, but the sampling can run at full speed using two instructions. Of course this presents some inconveniences, there is latency between the trigger signal and the reported trigger, also if the trigger pattern lasts less than one cycle at 66Mhz the trigger can be lost, and finally as the trigger always runs at maximum speed on lower speeds there may happen a "glitch", the trigger is raised because the pattern was found but the sampling program does not register this as it runs at a lower speed.

Finally we have the fast trigger, this uses a very clever "hack" (thanks to alastairpatrick from the Raspberry forums for the idea) that abuses the limitations of the PIO units. Each PIO unit can handle only 32 instructions, so the program counter of a state machine rolls to 0 if it's overflown, also the PIO assembler has an instruction to MOVe data from the IN pins to the program counter, and finally the PIO assembler allows to modify pin values on each instruction without using any extra cycle. So, said that, the trick consists on create a full 32 instruction program that moves the values from the GPIO to the PC and the instructions that are allocated in indexes that match the required pattern block the execution and sets a GPIO to 1.
Of course this limits the possibilities for the pattern, we can use up to 5 channels for this trigger but the trigger will run at full speed (it can work even faster, up to 200Msp).

If you want more info about the triggers check the PIO code in the source as there is more explanation on how this works.

## Schematic

The base schematic is only the Pico with a short between GPIO0 and GPIO1 but I have designed a PCB for convenience, it has been designed to mantain trace legths so no glitch may happen because propagation delays (at 100Mhz it should not be a problem, but in marginal cases if there is a noticeable trace length difference some picoseconds of delay can be introduced and change the analyzed values).

![Schematic picture](Schematic1.jpg?raw=true "Basic schematic")

Also, as the Pico only supports 3.3v I have designed a level shifter board, it uses very fast transceivers (TXU0104) which met the 100Msps specifications.

![Schematic picture](Schematic2.jpg?raw=true "Shifter schematic")

ATTENTION! I'm in the process of receiving the PCBs so they are not tested, I will update this document after testing it.

## PCB

There are two PCBs, one for the analyzer and other for the level shifter.

![PCB picture](PCB1.jpg?raw=true "Analyzer PCB")

![PCB picture](PCB2.jpg?raw=true "Shifter PCB")

## Building the firmware

To build the firmware you need to have an environment configured for Pico development, but if you don't have it don't worry, the releases include the UF2 file, so you only need to start the Pico in program mode, drop the UF2 file to the Pico drive and that's it, you have a Logic Analyzer ready to be used.

## The software

Before designing my own analyzer I have used some cheap chinese analyzers and all usee the same software, OLS, OpenBench Logic Analyzer, and to be honest, I don't like it. So, I have implemented my own binary protocol (more info in the firmware code) and visualization software. 

![Software picture](Software1.jpg?raw=true "Software main screen")

This is a .net desktop program for Windows (if I have enough requests I may plan to create a .net MAUI version that runs in Windows/MacOS/Linux) which allows you to visualize the capture data, highlight sampling ranges, name channels extremely fast, export the captured data preserving the capture settings and ranges, implemnts protocol analyzers (and a very easy system to include your own ones) and so on.

![Software picture](Software2.jpg?raw=true "SPI analysis")

For now I have already implemented a SPI protocol analyzer but I plan to implement also I2C, RS-232 and system bus analyzers (for old computers, 16 address bits and 8 data bits). In any case, with little knowledge of C# you can add your own protocol, which makes the program capable of analyze propietary protocols.

The capture interface is straight and self-explanatory, and the software preserves your last settings, can import settings from exported captures and allows you to re-issue a capture without having to go through the configuration process.

![Software picture](Software3.jpg?raw=true "Capture interface")

## Using the device

The device once connected to your PC will be detected as a serial port, no drivers are needed. Once you open the software you will have a list of serial ports and you must choose the correct one, once selected if you "Open" the device it will show the firmware version in the top section and will enable the capture buttons.

To use the analyzer connect the required channels to the signals you want to analyze, also connect at least one ground pin from the Pico to the analyzed device, press the "Capture" button, configure your settings and start the capture. The Pico will start flashing until the trigger condition is met and the capture will run.

Once the capture has finished you will see the channels, a range of up to 100 samples and the trigger event will be right at the left side of the sample area.

To name your channels you have a grey box under each one, these are textboxes where you can set whatever you want, and if you export your capture they will be preserved.

To create an highlighted region press over the numeric top bar and drag to select how many samples are highlighted.

![Region picture](Highlight1.jpg?raw=true "Highlight creation")

This will open the region creation dialog where you can choose a name for your region, the color and the opacity of the highlight.

![Region picture](Highlight2.jpg?raw=true "Highlight creation")

![Region picture](Highlight3.jpg?raw=true "Highlight")

If you want to delete a region press on the numeric bar over a highlighted region and it will be deleted. Regions are also exported with captures.

## Adding custom protocol analyzers

To add a new protocol analyzer you need to create a .net 6.0 assembly that references the LogicAnalyzer assembly and implements at least one class based in "ProtocolAnalyzerBase". Basically you will provide a list of settings to present to the user and then you will implement an analysis function that returns analyzed channels.

Each analyzed channel will specify a list of segments where data is overlayed (to present data to the user) and also it may provide a custom renderer for the data segments. You can create your own custom renderers or just provide an instance of the already included "SimpleSegmentRenderer".

---

## About Sigrok and the custom app

I have been reading some comments about why create my own application and why not use Sigrok as it would have been developed faster. First of all, the full project including firmware, PCB's and Windows client took me less than a week of development, I have been creating Windows apps for more than 20 years and it takes me less time to implement a rendering system, plugins and so on than implementing a third-party driver :)
In any case, my main reason to not consider to use sigrok is because I tried to use it with some cheapo analyzers and on my machines it simply would not run, I'm not sure if some component that I use for development is incompatible with it but on my three machines it crashed, in one machine it does not open at all and on the other two I had random crashes when I tried to capture data.

In any case, I will try to get it running in one of my development machines and if it works I will check how complex would be to create a driver for it.

---

Have fun!
