# LogicAnalyzer
----
## UPDATE 27/08/2022 - LevelShifter update and more...

I have updated the level shifter board. It's a minor change but it makes the shifter a lot more flexible as now you can use the internal +5V as reference for the input voltages or you can use an external voltage source as reference. Basically this allows you to use the target device's voltage sources as VRef so the board now can work with levels between 1.65v and 5.5v

New board:
![Shifter board](ShifterVRef.jpg?raw=true "Shifter board with VRef selector")

To use an external VRef source you need to remove the jumper JP1 and connect the external voltage reference to the +5v/ExtVRef pins of the input header.

![VRef pins](ShifterVRefPins.jpg?raw=true "Shifter board VRef input pins")

BEWARE!!! There is no overvoltage protection for the VRef input so you must be careful to respect the 5.5v maximum voltage limit.

#### More things to come very soon:

- Capability to abort a running capture (under testing)
- Enclosure for the analyzer (a preview is already in the repository, do not use as I'm on the process of adjusting it)

Enjoy it!

----
## UPDATE 31/07/2022 - RELEASE 2.0

Good news! The multiplatform application is ready!

The application has been completelly rewritten using AvaloniaUI, it works in Windows, Linux, Linux-ARM (Raspberry) and MacOSX.
It has been tested under Debian, Raspbian and Windows 10, MacOSX has not been tested as I don't have a working mac but it should work without problems.

Also, the new app includes improvements over the original one, like the ability to export the captures to Sigrok and better performance in general.

Application running in Windows:
![Windows software](SoftwareWindows.jpg?raw=true "SPI analysis")

Application running in Linux:
![Linux software](SoftwareLinux.jpg?raw=true "SPI analysis")

Application running in Raspberry:
![Raspberry software](SoftwareRaspberry.jpg?raw=true "SPI analysis")

----
## UPDATE 13/07/2022

I have managed to finally test the command line application in Linux and it worked as expected so I'm releasing it.

The command line capture program is a multiplatform command line application, it has versions for Linux, MacOSX and Windows and allows to capture data directly to a CSV file. The file format is compatible with Sigrok/PulseView so you can analyze the captures with it.

NOTE FOR LINUX/MACOSX USERS: Due to how I compile the apps you will need to make the app executable with CHMOD.

The app has been tested in Linux and Windows, if any user tests it on MacOSX please leave an issue with the results, I will be very thankful :D

### How to use the command line app:

If at any moment you need help you can execute `./CLCapture --help` and it will show you the usage help.

The app requires seven parameters to start a capture: serial port, sampling speed, channels to capture, pre-trigger samples, post-trigger samples, trigger definition and output file name.

- The first parameter is the name of the serial port of the logic analyzer.
- The second parameter is the desired capture speed in samples per second.
- The third parameter is a list of channels separated by coma, per example `1,2,3,4` or `1,16,24`.
- The fourth parameter is the number of samples to capture before the trigger.
- The fifth parameter is the number of samples to capture after the trigger.
- The sixth parameter is the trigger definition expressed in the form of: "TriggerType:(Edge, Fast or Complex),Channel:(base trigger channel),Value:(string - containing 1's and 0's indicating each trigger chanel state)". Per example, if we want an edge trigger on the positive edge using channel 4 the value would be `TriggerType:Edge,Channel:4,Value:1`. If we would want a fast trigger using channels 3,4,5 and a pattern of "101" the trigger definition would be `TriggerType:Fast,Channel:3,Value:101`. Note that there are no spaces, each parameter is separated by coma and no quote is used.
- Finally the seventh parameter is the output file name we want to generate.

A complete example to capture channels 1, 2, 3 and 4 at 100Mhz using channel 5 as positive edge trigger and storing the results in a file called "output.csv" would be similar to this:

```./CLCapture /dev/ttyACM0 100000000 1,2,3,4 512 1024 TriggerType:Edge,Channel:5,Value:1 output.csv```

If everything goes Ok you will see something like this:

```
Opening logic analyzer in port /dev/ttyACM0...
Conneced to device LOGIC_ANALYZER_V1_0 in port /dev/ttyACM0
Starting edge triggered capture...
Capture running...
```

The analyzer will blink while the capture is running and once it has finished it will print the result:
```
Capture complete, writting output file...
Done.
```

This capture will contain the data in CSV and is compatible with PulseView. To import it in PulseView go to "Open->Import comma-separated values...". The file is generated in a way that you don't need to change any of the CSV paramters, you will need to specify only the number of channels and the capture speed.

Once imported you will see your data, something like this:
![imagen](https://user-images.githubusercontent.com/4086913/178774617-024c1aa4-852d-4d2d-8352-e973249b769c.png)

I hope that with this, at least until the multiplatform app is ready, all the users can use the analyzer the way they want, it will work in all the common OS'es and it introduces compatibility with Sigrok/Pulseview in a way that is not intrusive for Sigrok nor for the LogicAnalyzer app.

Have fun!

----
## UPDATE 12/07/2022

I have received the shifter PCB's and there is an error. The footprints of J1 and J2 are exchanged, so what should be inputs are outputs and vice-versa. Thankfully this is not a problem, as the PCB is completelly symmetric and it has components in both sides flipping the board fixes the problem.

Board before flip.
![IMG_1562_2](https://user-images.githubusercontent.com/4086913/178580443-b1ed4abf-1c8a-494a-9fba-48415d7801bb.jpg)

Board after flip.
![Board after flip](https://user-images.githubusercontent.com/4086913/178579577-289d0d75-e9ea-4293-9b07-098600bab5cc.JPG)

The KiCad project is already updated.

The good news is that the board works like a charm, I have tested it with my clock generator with a 50Mhz clock and it captures every single half cycle perfectly, like if the board was not there :D

So if you want to build your own shifter board, it's ready and tested.

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

A logic analyzer only cares about logic states of lines, so without thinking much about it you may think that any microcontroller using DMA channels that read GPIO values would be more than enough, but that is the "easy" part of a logic analyzer, the problem comes when you need to trigger the captures based in GPIO states and you want also to have data captured previously and after the trigger happens.

For that, you need to compare the read values from the GPIOs check if the pin or pins values match the requested trigger and you must do it as fast as you want to capture, so for example, the most basic comparison will at least consume 3 or 4 instructions, if each instruction is 1 to 4 cycles (more or less, I'm thinking in ARM processors) then you will use up to 16 cycles to read a sample, so you would need a 1.6Ghz CPU to sample at 100Msps.

So, how the heck the pico is able to achieve this? Well, the key are the PIO units, these units are a wonder, they are coprocessors explicitly designed to handle IO, it uses a very restricted and deterministic assembler (only nine instructions that each take a single cycle to execute) but extremely efficient, so efficient that with only two instructions is possible to create a loop that captures GPIO data up to 30 bits and redirects the program flow based in the status of one of these GPIOs.

Of course there are some limitations, that two-instruction loop can only change the execution flow based on a GPIO pin, it can't branch based on a pattern (using only two instructions) but as we have more than one unit (each pico has two units and each unit has four state machines, so you can run in parallel up to 8 programs) we can abuse a bit the system and create a separate trigger program that notifies the capture program using a pin, that's why GPIO0 and GPIO1 are shorted.

The analyzer described here has three trigger modes: edge trigger, fast pattern trigger and complex pattern trigger.

The edge trigger uses a single program, that's the basic version that uses only two instructions, runs up to 100Msps and the triggering is synchronized with the captures.

The complex triggers is the first that uses two programs, one to capture and other for the trigger. The complex trigger supports patterns up to 16 bits matched from consecutive channels in the first 16 ones.
Having two programs is key to keep sampling up to 100Msps, the trigger program uses three instructions so its speed is limited to 66Msps, but the sampling can run at full speed using two instructions. Of course this presents some inconveniences, there is latency between the trigger signal and the reported trigger, also if the trigger pattern lasts less than one cycle at 66Mhz the trigger can be lost, and finally as the trigger always runs at maximum speed on lower speeds there may happen a "glitch", the trigger is raised because the pattern was found but the sampling program does not register this as it runs at a lower speed.

Finally we have the fast trigger, this uses a very clever "hack" (thanks to alastairpatrick from the Raspberry forums for the idea) that abuses the limitations of the PIO units. Each PIO unit can handle only 32 instructions, so the program counter of a state machine rolls to 0 if it's overflown, also the PIO assembler has an instruction to MOVe data from the IN pins to the program counter, and finally the PIO assembler allows to modify pin values on each instruction without using any extra cycle. So, said that, the trick consists on create a full 32 instruction program that moves the values from the GPIO to the PC and the instructions that are allocated in indexes that match the required pattern block the execution and sets a GPIO to 1.
Of course this limits the possibilities for the pattern, we can use up to 5 channels for this trigger but the trigger will run at full speed (it can work even faster, up to 200Msp).

If you want more info about the triggers check the PIO code in the source as there is more explanation on how this works.

## Schematic

The base schematic is only the Pico with a short between GPIO0 and GPIO1 but I have designed a PCB for convenience, it has been designed to maintain trace lengths so no glitch may happen because propagation delays (at 100Mhz it should not be a problem, but in marginal cases if there is a noticeable trace length difference some picoseconds of delay can be introduced and change the analyzed values).

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

Before designing my own analyzer I have used some cheap Chinese analyzers and all use the same software, OLS, OpenBench Logic Analyzer, and to be honest, I don't like it. So, I have implemented my own binary protocol (more info in the firmware code) and visualization software. 

![Software picture](Software1.jpg?raw=true "Software main screen")

This is a .net desktop program for Windows (if I have enough requests I may plan to create a .net MAUI version that runs in Windows/MacOS/Linux) which allows you to visualize the capture data, highlight sampling ranges, name channels extremely fast, export the captured data preserving the capture settings and ranges, implements protocol analyzers (and a very easy system to include your own ones) and so on.

![Software picture](Software2.jpg?raw=true "SPI analysis")

For now I have already implemented a SPI protocol analyzer but I plan to implement also I2C, RS-232 and system bus analyzers (for old computers, 16 address bits and 8 data bits). In any case, with little knowledge of C# you can add your own protocol, which makes the program capable of analyze proprietary protocols.

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
