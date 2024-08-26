# LogicAnalyzer

## Downloads
You can find all the compiled projects in the [Releases section](https://github.com/gusmanb/logicanalyzer/releases).

Latest version: Release 5.1.0.0, 05/05/2024
----

# Pico 2: a game changer?

I've started checking the Pico 2 and porting the code to it. I must say that it has been one of the easiest transitions that I ever did, just reconfigure the cmake scripts, change a couple of lines, and voi-la! the project runs in the pico 2.

This is the base code, no changes at all, but from here I have multiple improvements to do, starting with the DMA (no mode ping-pong DMAs for the Pico 2, a single DMA can do all the work simplifying the code A LOT) and then upgrading the buffers to three times what are now, I expect to have up to 380k samples :)

Said that, I started checking the limits of the pico 2 and... well, I'm really surprised, with the original pico I only got stable up to 200Mhz, beyond that I had problems with the flash and it got hung, but, oh my gosh, this thing (the pico 2) right now is running at 400Mhz without a single hicup!!

Of course I had to raise the voltage to 1.4v for the core and it gets warmer, but I added a little heatsink to it and it's perfectly fine. Soooo.... I need to test this in deep but this may be a very, very big change, not only three times the samples than the pico, but also twice the speed!

Stay tuned for more news!

----

# Help wanted!

I'm cooking something very special, if you whant to know what it is and help with it, [check this post](https://github.com/gusmanb/logicanalyzer/discussions/127).
😉

# More boards on the go!

One of the new functionalities of the RP2350 is the capability of having two XIP devices and also has the full device implementation (RP2040 only had READ capabilities implemented). This means that is possible to have (for example) a flash device *and* a PSRAM connected to it.
Unfortunatelly the Pico 2 does not expose the QSPI pins and they are tied directly to the flash... But there is hope! PiMoroni has developed the PiMoroni Pico Plus 2 which contains 16Mb of flash and 8Mb of PSRAM.

I already have ordered one of these new boards and have some ideas on what could be done with them :D
Right now the most possible one is this: PSRAM is not fast enough for sampling at a decent speed with many channels, BUT, it is fast enough for something like storing ADC samples, so what I'm going to try is to allow the mix of analog and digital channels. The analog channels will be very slow compared to the digital ones (only 500Ks/s) but it still can be useful to monitor behaviors of things like motors, servos or whatever. As the PSRAM is 8Mb it will allow to store up to 8 seconds of analog data on single channel mode (2 bytes per sample at 500Ks/s is roughly 1Mb/s of data), this, combined with the upgraded onboard ram and the burst mode can be really useful in multiple projects.

Stay tuned for more news!

----

# Exciting news! The Pico 2 is coming soon!

As some of you may know the Pico 2 is being released this month. The new Pico 2 is a very exciting upgrade of the pico, more powerful cores, two alternative RiscV cores, three PIO units instead of two and 520Kb of RAM!

This can be a game changer for LogicAnalyzer, only with the new ammount of RAM the quantity of samples is going to increase massively, we're talking about three times the current ammount of samples!

Also, there are really exciting changes on the PIO side, the new IRQ system allows to intercomunicate the PIO units, this means that the trigger pins could be freed now, and this, as small change as it seems can be really amazing combined with the new third PIO unit... Think about this, a 64Mb dual SPI RAM running at 100Mhz connected to the two free pins and controlled at full speed by the third PIO unit... 

I was preparing a release for this month but it's going to be delayed, once I receive the new Pico's I will start the development for the Pico 2 and once it's completed I will release all at once.

Stay tuned!

## RELEASE 5.1

This release is a QoL release with some functional corrections. For more details check the release page.

## RELEASE 5.0, Burst mode is here!

New release with exciting feature!

The biggest change on this release is the Burst mode. With burst mode you can capture blocks of data and the analyzer will rearm itself immediatelly and capture more data when the trigger condition is met again. This will improve the memory usage discarding unneeded samples! Right now only the simple trigger mode accepts burst mode but in a future I will try to implement it in all the other triggers.
For more information check [the wiki.](https://github.com/gusmanb/logicanalyzer/wiki/06---The-LogicAnalyzer-program#triggers)

Also new features to ease the navigation in the capture viewer have been added like shortcuts and a preview of the full capture. More info in [the wiki.](https://github.com/gusmanb/logicanalyzer/wiki/06---The-LogicAnalyzer-program#navigating-on-the-capture-viewer)

Finally multiple improvements have been done, some bugs in the capture tail detection have been corrected, the USB transfer has been improved using directly the CDC transfer functions and more.

Beware that this version is not compatible with other ones, the protocol has changed. The driver will check the device version and will not connect to it if it is lower than V5.0.

Have fun!

----

## UPDATE 28/06/2023 - Release 4.5.1 - QOL improvements

This release include some QOL updates to the applications.

LogicAnalyzer app:

* Ammount of on-screen samples will be preserved if you repeat the last capture.
* Added a new menu entry called "Repeat las analysis" to the protocol analyzers, it will execute the last analysis performed to speed up things.
* Changed where config files are stored, they will use the %appData% folder now ($home/.config in Linux).
* Changed horizontal scrollbar visibility.

CLCapture app:

* Now channel names can be provided from the command line.

Have fun!

----

## UPDATE 11/04/2023 - Release 4.5 - Support for the RP2040-Zero and new board definition system

This release includes only an update to the firmware.

First, the RP2040-Zero is now officially supported (no shifter board for it though). 
You can download the firmware for it on the [releases](https://github.com/gusmanb/logicanalyzer/releases) section. Also, the pinout has been added to the [wiki](https://github.com/gusmanb/logicanalyzer/wiki/02---LogicAnalyzer-Hardware#barebones-configuration) so you can use it with the bare-bones configuration.

And second, the firmware has been refactored in order to make a lot easier to add new boards. You have the complete instructions on how to add support to a new board on [the wiki firmware section](https://github.com/gusmanb/logicanalyzer/wiki/03---LogicAnalyzer-Firmware). Also, as some boards include the very popular WS2812 RGB led the firmware includes a driver for it, it's purely software-based, no timers nor interrupts needed, so feel free to use it if you want.

If you add support for a new board, feel free to create a pull request with the changes :)

Have fun!

----

## UPDATE 25/02/2023 - Release 4.0 is up! Channels a go-go!

Hi again! This is a BIG update loaded with new functions and improvements to the hardware, firmware and software!

Let's start with the little things: we have a logo! Yes, it's nothing important but I hated to not to have a proper one so I designed one that I think fits well to the project :D

<img src="https://user-images.githubusercontent.com/4086913/221263290-0e8598d1-3c6e-4d85-b33a-16c73146cd27.png" width="50%" height="50%" />

Next, we have a proper Wiki! All the project has been documented: hardware, firmware and software. If you have any doubt check it as I have tried to explain everything related to the analyzer usage in there. If you find any error or missing feature please open an issue and I will correct it as soon as I can.

<img src="https://user-images.githubusercontent.com/4086913/221356351-c3212066-0ef0-408c-88f3-6c6818878d60.png" width="50%" height="50%" />

Ok, now the changes to the hardware. There is a new pcb for the analyzer that includes two connectors to daisy chain the analyzers. You can use two or three Dupont wires (the central pin is unused, it's reserved for future usage, I have left it there so anyone that produces these PCB's can patch them easily).

<img src="https://user-images.githubusercontent.com/4086913/221230472-f05828de-72f3-4337-a71d-685bb989c1a1.png" height="60%" width="60%" />

And the firmware has also been updated to support the daisy chaining. So, what is for the daisy chaining? Well, daisy chaining allows to chain up to five analyzers without wasting pins so you now will be able to capture a massive ammount of **120 CHANNELS!!!** Check the [Connection](https://github.com/gusmanb/logicanalyzer/wiki/06---The-LogicAnalyzer-program#connecting-to-devices) and [Capture](https://github.com/gusmanb/logicanalyzer/wiki/06---The-LogicAnalyzer-program#capture) sections of the Wiki to know all the possibilities and how to use them.

Now, the software. It contains many changes, so I'm going to start with the improvements and then with the new functionalities.

First I have improved the sample rendering. It is now more visible and looks a lot better. Also, the guides shown to see where a sample starts and ends are automatically scaled or removed, it made no sense to have so many lines that they made a solid gray background, so when there are too many they will get automatically deactivated. Also, this allowed to improve the performance so now the sample viewer will allow to show up to 2000 samples in screen without any check.

![New render](https://user-images.githubusercontent.com/4086913/221300523-39c6b881-09c4-49e0-b3d6-0126883eba27.png)

Related to this the protocol analyzer renderer has been updated, it will take less useless space and will hide the information if it does not fit in the assigned space.

Now, the connection system has been updated to include a "multidevice", this is the device that you must use when using the daisy chained analyzers.

![Multidevice](https://user-images.githubusercontent.com/4086913/221277047-dccae975-ab8c-4cd9-9d39-7edbcb344218.png)

Next, the capture dialog has been updated, the mode selector has been removed and the mode is autoselected based in the channels enabled, check the [Wiki page](https://github.com/gusmanb/logicanalyzer/wiki/06---The-LogicAnalyzer-program#basic-parameters) to know the limits and modes.

Also, the capture dialog has a new channel selector, more visual and that includes the name field for the channels, instead of configuring the names after the capture has been finished (and lose these if you capture again) the names can be entered directly on the capture dialog. These names will be preserved between captures (and if you change them from the channel viewer these changes will be respected).

<img src="https://user-images.githubusercontent.com/4086913/221279281-5abe0a5e-7ead-4242-8703-36d6bef0d882.png" width="50%" height="50%" />

This new channel selector also allows to show up to the 120 channels that can be used when daisy chaining five devices, the selector will have a scrollbar when the channel list is bigger than its space.

Another change, the editing features have been improved and expanded. First of all, you will not need to create regions to execute edit actions, the sample range selection has been improved and it is used now for these. Check the [Wiki page](https://github.com/gusmanb/logicanalyzer/wiki/06---The-LogicAnalyzer-program#editing-captures) to see a description on how it works and which new features have been included.

Finally, the system now can create capture files from scratch, for this I have implemented a language that allows to describe signals in an easy way, it even includes a colored syntax editor, check the [Wiki](https://github.com/gusmanb/logicanalyzer/wiki/06---The-LogicAnalyzer-program#the-signal-description-language) for a description of this language!

<img src="https://user-images.githubusercontent.com/4086913/221319793-ee273022-f2fb-453f-b9f4-c35706b2b6eb.png" width="50%" height="50%" />

Also, I already have planned the next update, I'm not sure when it will be ready but I will implement it for sure, and this is one of the motivations to create the SDL language: replay captures! ;)

This is a resume of the most prominent changes, surely that I forgot some, but all are documented in the Wiki, so ensure to review it!

Any feedback about the update will be welcome, so don't hesitate to open issues or start discussions.

Have fun!

## UPDATE 07/02/2023 - New release with updated shared driver.

This is a bug-fix release, with the introduction of the Pico-W WiFi support I unified the transfer mode in the driver using streams for network and for the serial port, but I forgot that .net 6.0 Ports package causes problems with Linux, so the previous release will hung the app when receiving more than 4k samples... Doh!

I have updated the code to use the same work around that I used previously and the problem has been fixed.

Have fun!

----

## UPDATE 04/02/2023 - New release! Bugs corrected and more samples!

Hi! This update comes loaded of news.

### First of all, bug corrections. 

The biggest bug that has been corrected is the fast trigger in the Pico-W. When I implemented the Pico-W I tried it extensively, but I used only the simple trigger to do the tests. What was my surprise when I tried to use the Pico-W with a fast trigger and I found that it got completelly hung!

The thing is that the Pico-W hides a little secret that I haven't found documented anywhere, this little secret is that the driver uses a PIO program to do the transfers! The fast trigger uses a full PIO unit, all its 32 instructions to create a jump table, and the CYW driver uses a SM in the PIO1 to do the SPI transfers. So I tried to swap the PIO units and it at least started to capture, but the capture was never finished, I have revised up-to-down the driver and still haven't found why the PIO1 interrupts don't work at all after the CYW driver has been enabled, so I have done a work-around that does not need the IRQ to trigger a handler. So, if you are using a Pico-W update the firmware asap.

The next bug is a small bug that caused that some samples weren't clear correctly when a trigger was rised immediately after starting capture (for example the trigger condition is already met when the first sample is done).

### And now, the really big news, MORE SAMPLES!

I have tweaked the buffer transference between the PIO and the memory and it allows to hold up to 131071 samples! Of course this is at the expense of how many channels you use, the device now has three modes: 8 channels, 16 channels and 24 channels.

The sample limits are specified here:

 * Mode 8:
 
     * Minimum pre-samples: 2
     * Maximum pre-samples: 98303
     * Minimum post-samples: 512
     * Maximum post-samples: 131069
     * Maximum total samples: 131071
     
 * Mode 16:
 
     * Minimum pre-samples: 2
     * Maximum pre-samples: 49151
     * Minimum post-samples: 512
     * Maximum post-samples: 65533
     * Maximum total samples: 65535
     
 * Mode 24:
 
     * Minimum pre-samples: 2
     * Maximum pre-samples: 24576
     * Minimum post-samples: 512
     * Maximum post-samples: 32765
     * Maximum total samples: 32767

As you can see, using the 8 channel mode you can capture up to four times the samples that were available until now, a substantial increase.
The channels used for 8 and 16 modes must be the first ones, you cannot choose eight random channels, and this introduces a limitation, they collide with the complex and fast triggers (not the simple trigger, for that you still can use any channel left). Bear in mind this to plan how you configure your capture, for example for the 8 channel mode you still can have a 8 channel complex trigger or a fast 5 channel trigger without including these channels in the capture, but if you need more channels for one of these triggers, or you need to use the 16 channel mode you will suffer of this.

### Another new update, now you can show up to 1024 samples in screen!

You can activate this feature from the main screen, it has a checkbox (which will warn you as this may be a very CPU intensive task for old computers) that allows you to change the on-screen samples from 200 to 1024, this is really useful for use with big screens and modern computers.

Also I have tweaked a bit the appearance of the sample viewer, I didn't liked the dashed lines so now all are continuous ones.

Well, that's it for now.

Have fun!

----

## UPDATE 03/02/2023 - Measurement tool.

This is a very handy update to the analyzer, you can measure a region and get information of each channel: total samples selected, period of the selection, number of positive pulses, number of negative pulses, average and predominant period for positive and negative pulses and average and predominant frequency.

The predominant values are calculated applying a variant of the 95th percentile rule to discard aberrant/broken samples and I must say it works really well, it matched exactly all the frecuencies I have tested.

![imagen](https://user-images.githubusercontent.com/4086913/216588696-f654142b-0359-4737-b268-9a03e389aca1.png)

There is still no new release, you will need to compile the application if you want it, but I will create the release very soon.

Have fun!

----

## UPDATE 02/02/2023 - I2C protocol analyzer.

New day, new analyzer :D. This time is the turn for I2C. The analyzer will show you the raw data, the ACK/NACK's and will also show the device address (7 and 10 bit modes), operation of a request and any kind of frame error. To install it get it from [here](https://github.com/gusmanb/logicanalyzer/blob/master/I2CProtocolAnalyzer.dll) and copy it to the "analyzers" folder of the application.

![imagen](https://user-images.githubusercontent.com/4086913/216373359-d09fb234-0858-4005-aec1-e9a09177f37f.png)

Have fun!

----

## UPDATE 01/02/2023 - Serial protocol analyzer.

This is a small update, I have created a serial protocol analyzer (RS-232). This update does not include a release but I have left the analyzer library compiled in the repository. To install it get it from [here](https://github.com/gusmanb/logicanalyzer/blob/master/SerialProtocolAnalyzer.dll) and copy it to the "analyzers" folder of the application.

It supports positive and negative polarity (for TTL and RS-232 level signals), two channels (RX + TX), 7 or 8 bits, no parity/odd parity/even parity and 1, 1.5 or 2 stop bits.

![imagen](https://user-images.githubusercontent.com/4086913/216373893-f28a6de1-a1d6-4efd-a9b1-95b5418de66d.png)

Have fun!

----

## UPDATE 31/01/2023 - Pico-W support and WiFi!

It's finally here! WiFi support!

First of all, there are now three different firmware versions in the release section, one with no suffix for the regular pico, another with the "W" suffix for the Pico-W with no WiFi support and a final one with the "WIFI" suffix for the Pico-W with WiFi support. Choose the one that best suits your needs.

Now, how to use the WiFi support?

First of all, you need a Pico-W, I think that's obvious :D, flash it with the "WIFI" firmware and the device is ready to be used. If you plan to solder the Pico-W to the analyzer board beware to not to add the debug pins as they are now located in the middle of the board and it will not allow you to solder it, if you want them then you will need to use some pin headers to rise the Pico from the board (for my own device is what I always have done, in this way I can replace the Pico whenever I want).

Ok, now let's see how to use it.

First of all, you need to connect at least once the Pico-W to the computer to configure the network settings, this process can be done as many times as you want, connect the Pico-W to the computer and use the CLCapture or the LogicAnalyzer software to configure it.

When you connect the Pico-W with the WiFi firmware you will notice that a new menu gets enabled:

![WiFi menu](WiFi-1.jpg?raw=true "WiFi menu")

From there you can then select the "Update Network Settings" menu.

![WiFi menu 2](WiFi-2.jpg?raw=true "WiFi menu 2")

That will open the dialog to configure the network settings, you must enter the SSID of your router, the password (only WPA2 is supported), the desired static IP address and the listening TCP port.

![Network options](WiFi-3.jpg?raw=true "Network options")

Once these are configured accept them and they will be saved to the Pico-W flash, immediately the Pico-W will try to connect to your router, if it's available it will connect and it will be available for network connection.

To connect to the Pico-W through WiFi you must select from the dropdown menu the "Network" option.

![Network connect](WiFi-4.jpg?raw=true "Network connect")

Once you select it and press the "Open" button the network connection dialog will open.

![Network connect dialog](WiFi-5.jpg?raw=true "Network connect dialog")

Fill the IP address and port and press "Accept", if the device is available it will connect to it.

![Network connected](WiFi-6.jpg?raw=true "Network connected")

And that's it! From that point the device works exactly as before, for the application is indifferent if it is connected through network or USB, it has the exact same functionalities.

### The CLCapture updates

The CLCapture also supports the network connection and configuration, for that purpose now the command line starts with a verb, execute the program without any parameter to check the verbs and only with a verb to get the required parameters.

### Some notes

Both interfaces (USB and WiFi) work at the same time, but when a client gets connected through WiFi the USB will be ignored until the client gets disconnected, keep it in mind.

I have found some quirks on the Pico-W WiFi support, the first one is that it does not support at all to connect without a DHCP server, and it always gets the network information from there, fortunatelly I have found a way to change the IP address once it is connected to the AP. This also causes a problem (at least in my router), if you are already connected to the AP and you change the network settings the device disconnects from it and reconnects with the new info, if is the same AP (per example you have just changed the IP address) the static IP is ignored and it will retain the one assigned by the DHCP server, the solution is easy, restart the Pico-W and it will connect with the new IP address.

The firmware now has three "flavours" when compiled, this is controlled from the "LogicAnalyzer_Build_Settings.h" header and the "CMakeLists.txt" files, both contain instructions on how to change the settings based on your preferences.

A user adviced me that the Pico-W may have problems if the USB is connected to a host and the WiFi is used. I haven't experienced none of these and I have tested it extensively, maybe as I have used a sepparated core for the WiFi it avoids this kind of trouble, but if you experience them then use a USB power supply (like a phone charger or similar) if you want to connect through WiFi.

### The future

I'm thinking about creating a new PCB board that contains a battery and an USB charging module, in this way the device will become totally free of wires (except for the ones for the signals, obviously). I think this could be extremely useful, you will be able to place the analyzer even inside a computer or any kind of device and connect to it remotely, I think this could be extremely useful for devices that are in fixed places or are big and difficult to move (like old mini computers or car ECU's).

Stay tunned for more news, and be sure the project still is not completed!

Have fun!

----

## UPDATE 29/01/2023 - Software update

This release contains many updates to the GUI, CLI and driver and also includes many new target architectures.

### Updates to the GUI

First, the sample viewer and sample marker contains also the half of the cycle (where the sample was done in the cycle) to make it easier to see the data.

Now you can create a "user mark", it is a temporary mark and is not saved with the save/export data, just an useful tool to see things. Click on the sample marker without dragging and you will set the user mark place. To remove the user mark click again in the same spot.

Deleting samples is now possible, when you right-click on the sample marker over an existing region now instead of deleting the region it will pop a menu which will allow you to delete the regions that were under the mouse or to delete the regions *and* the samples.

Added more meaningful error messages, in any case the limits in the numeric up/down controls have been updated to match what the driver expects.

### Updates to the CLI

It also includes the new messages with more meaningful errors.

### Updates to the driver

The driver has been adjusted to give more flexibility in the pre/post samples, the valid parameters now are:

    -Frequency must be between 3.1Khz and 100Mhz
    -PreSamples must be between 2 and 31743
    -PostSamples must be between 512 and 32767
    -Total samples cannot exceed 32767
    
Have fun!

----

## UPDATE 17/12/2022 - Application repackaging

One of the features that I loved for .net when it was introduced is the ability to create applications that does not require the user to install the .net Framework independently. I always prefer to create portable packages, something that you uncompress wherever you want and it just works. This creates a bit bigger applications but nowadays with the massive storage devices we have and the fast Internet we have this is not a problem, while having to install the framework can be painful in some cases (restricted user privileges environments, problems with old .net installations, etc).

Well, thanks to the people at [Laboratoire Ouvert Grenoblois](https://www.logre.eu/) I found that the packages for unix/macos where incorrectly packaged and didn't included the framework and needed its installation... Doh!

I have re-packaged all the applications (CLI and GUI) and now all the versions include the required files, it should not need any more the installation of the .net framework.

Also, I have bumped up the firmware to the version that includes the new tail detection (beware, it will still inform that is the V1.0, I will correct the version numbering with the release of the Pico-W support).

Note: If you already have the applications and they are working ok for you that means that you already have the framework installed and there is no need to download the new packages, you only need these if you're doing a new installation or you had problems with the previous versions because the missing framework.

Have fun!

----

## UPDATE 12/12/2022 - Working towards Pico-W support

One of the goals that I want to achieve with the analyzer is to support the Pico-W. Would not be great to have a battery powered analyzer that connects to your computer via WiFi? For me at least this is a really desirable option as I have my main computer on a different desktop than the electronics bench, so when I want to analyze signals I must have a long USB cable hanging from the computer to the analyzer or I must do the analysis in the computer desktop. Also even if you are in the same desktop the less cables that you have around the easier is to work. For this, the Pico-W is ideal, as the analyzer does not transfer data in real time it does not need an extremely fast connection, for transferring the data once it has been captured the integrated WiFi of the Pico-W is more than enough.

### Pico-W missconceptions

It has been a while since I got the Pico-W and I didn't had enough time to start really digging on how the thing works, so my previous knowledge about the W was based on the first notes that were released to the Internet (I bought it at release day). Something that was stated in many places was that the W used some GPIO's to control the WiFi module so you would have less available IO's for your usage.

I have been really pleased when I have read by myself the datasheet and how the Pico has implemented in reality the WiFi module. It indeed uses some GPIO's to control the WiFi, but, those GPIO's have never been available to the user as regular GPIO's. The Pico uses GPIOs 23, 24, 25 and 29 for internal usage (LED, VBUS sense, etc). So, what have they done in the Pico-W to not to use additional GPIO's? They have lifted those functions to the GPIO's of the WiFi module. The WiFi module itself contains a GPIO port and now that port is the one that contains those functionalities, so now GPIO's 23, 24, 25 and 29 control the WiFi module and the first three GPIO's of the module are used for those functions.

So, what does all this means for the analyzer? Well, it means that very little changes needs to be done in the capture code and only the front-end code needs to be changed. Also, this means that the W version will also retain all the 24 channels, it will not lose any capability. Wohooo!!!

### Changes to the capture code

As all the GPIO's that are used to capture are the same there is no need to change any code except for one very small part, the "end capture" mark. The PIO always capture pins in a sequential way, it means that you cannot have "holes" in the pin sequence, and to get the full 24 channels every single available GPIO must be used, up to GPIO28. This means that the GPIOs that controlled the LED's, VBUS and so on also are captured but ignored. Said that, to mark where the capture was finished in the buffer a special value that was impossible to happen was added after the last capture, it was based on that the device those GPIOs would never be 1's. In theory, as we are capturing 32 bit words there will always be some zeroes at the tail, but I'm paranoid and also it is not elegant, so I decided to modify the tail detection code.

Instead of basing the tail detection in a mark in the buffer (which requires to iterate the buffer until it is found) now the tail detection is based in the DMA channels transfer state. This was my original idea, but unfortunatelly the Pico API does not expose a direct way of reading how many transfers have been done or how many are left, you can set them but cannot read them, so I abandoned that idea.

This time I have digged a bit more and went directly to the RP2040 datasheet and it states very clear that the TRANSFER register is R/W, so you can read how many transfers are left. I have no idea why the API does not expose it, but knowing that is very easy to access directly to the register using the dma hardware channel structure.

Now what the code does is: once the capture has finished before aborting the DMA channels it checks which one is busy (remember, there are four DMA channels in a ringed chain, so only one DMA will be busy, the one that's waiting for the next transfer from the PIO), checks how many transfers are left and based on the DMA channel number and the transfers left it computes the index of the last capture.

This is more elegant, faster and prevents that my paranoid side rings a bell each time I see that code thinking on the Pico-W, so all are advantages :D

### Wanna try it?

In the repo source under the [build](https://github.com/gusmanb/logicanalyzer/tree/master/Firmware/LogicAnalyzer/build) folder you will find the UF2 file with the new detection code, so you can try it with the Pico-W, it will still use the USB to transfer the data but you can check its compatibility. I still haven't got time to try it in the W but I plan to do it soon. In any case, if you test the new firmware in a W or a regular Pico I would be thankful if you can leave a comment telling your experience, if you have found any problem or if it worked as expected.

### Next steps

Well, the next step will be to add the front-end code for the W, the idea is to have a single project that based on settings compile it for the W or for the regular pico. About how to implement it, I still need to check the W API for the WiFi, but one thing that I want to do for sure is to have the WiFi module off when the capture is running to avoid any kind of glitch because interferences, I fear that the traces may act as antenna and read false data, so I'm thinking that I will use UDP instead of TCP, use a broadcast address to send/receive data and as UDP does not require an stablished connection it will allow to shut down the module without breaking the network. In any case these are my first thoughts and may change once I start implementing it.

Have fun as always!

----


## UPDATE 27/11/2022 - Small changes, great value

I have uploaded a new version of the PCB's and the firmware. It contains a small modification which can give great value to the device.
Do you have an oscilloscope? Have you ever wanted to trigger it based on the value of a data bus? Or when some digital signals take a concrete value?
Now the logic analyzer offers this functionality!

The modification is very simple, the GPIO pins used for the complex/fast triggers have been exposed through a diode and that signal can be used to trigger other devices like an oscilloscope. Or even you can chain multiple logic analyzers to have as many channels as you want! Configure your analyzer for a complex or fast trigger, connect your device to one of the EXT pins (and GND as needed) and start the capture. To chain multiple analyzers you must configure a simple trigger and connect one of the pins on the secondary analyzers to the EXT trigger pin. In the future and if it is requested I will add another capture mode for the EXT so it can chain more than 3 analyzers.

There is a small delay from the trigger to the signal, I have measured it and it is a delay of 20ns for the fast trigger (the two cycles that takes to detect and propagate the trigger condition) and 35ns for the complex one. Also, the diode introduces a small delay of 4ns, if you want to remove that delay you can skip the diode and the pull-down resistor and place a bridge where the diode should be placed, but be ware that you will leave the trigger unprotected against polarity inversions.

The external trigger has been routed to two pins, in this way you can chain as many analyzers as you want, or connect two other devices.

The new pinout is this:
![imagen](https://user-images.githubusercontent.com/4086913/204116558-528422eb-4674-4909-9f24-1c0df2d47aab.png)

Beware to not to use a new analyzer with an old shifter board, it has been also modified to include the ext signals, if you use an old sshifter with a new board you will create a short between +v5, +3.3v, GPIO0 and GPIO1 what will be fatal.

For the new shifter the pinout is the same as the analyzer but the +5v pin is the +5v/ext_ref depending on the jumper setting.

Finally I also have updated the firmware to disable the GPIO synchronizers what reduces other 4ns of delay.

Have fun!

----

## UPDATE 03/09/2022 - Abort captures
Minor release adding the capability to abort a running capture. To use this feature you will need to update the firmware and the application.

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

## Build requirements

To build the firmware you will need a build environment for the Pico-SDK version 1.3.1 or newer. For Windows users I recommend to use the [Pico-Setup project](https://github.com/ndabas/pico-setup-windows/releases).

To build the application you will need [Visual Studio 2022](https://visualstudio.microsoft.com/) with the C# language installed.

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
