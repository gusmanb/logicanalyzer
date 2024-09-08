using CLCapture;
using CommandLine;
using SharedDriver;
using System.IO.Ports;
using System.Linq;
using System.Runtime.CompilerServices;
using System.Text;
using System.Text.RegularExpressions;

Regex regAddressPort = new Regex("[0-9]+\\.[0-9]+\\.[0-9]+\\.[0-9]+\\:[0-9]+");
Regex regAddress = new Regex("[0-9]+\\.[0-9]+\\.[0-9]+\\.[0-9]+");
LogicAnalyzerDriver? driver = null;

TaskCompletionSource<CaptureEventArgs> captureCompletedTask;

Console.CancelKeyPress += Console_CancelKeyPress;

return await Parser.Default.ParseArguments<CLCaptureOptions, CLNetworkOptions>(args)
        .MapResult(
            async (CLCaptureOptions opts) => await Capture(opts),
            async (CLNetworkOptions opts) => Configure(opts),
            errs => Task.FromResult(-1)
            );

async Task<int> Capture(CLCaptureOptions opts)
{
    bool isNetworkAddress = regAddressPort.IsMatch(opts.AddressPort);
    var ports = SerialPort.GetPortNames();

    if (!isNetworkAddress && !ports.Any(p => p.ToLower() == opts.AddressPort.ToLower()))
    {
        Console.WriteLine("Cannot find specified serial port or address has an incorrect format.");
        return -1;
    }

    if (opts.SamplingFrequency > 100000000 || opts.SamplingFrequency < 3100)
    {
        Console.WriteLine("Requested sampling frequency out of range (3100-100000000).");
        return -1;
    }

    CLChannel[]? channels;

    try
    {

        //int[]? channels = opts.Channels?.Split(",", StringSplitOptions.RemoveEmptyEntries).Select(c => int.Parse(c)).ToArray();
        channels = opts.Channels?.Split(",", StringSplitOptions.RemoveEmptyEntries).Select(c => new CLChannel(c)).ToArray();
    }
    catch (Exception ex)
    {
        Console.WriteLine(ex.Message);
        return -1;
    }

    if (channels == null || channels.Any(c => c.ChannelNumber < 1 || c.ChannelNumber > 24))
    {
        Console.WriteLine("Specified capture channels out of range.");
        return -1;
    }

    int maxChannel = channels.Max(c => c.ChannelNumber);
    int channelMode = maxChannel <= 8 ? 0 : (maxChannel <= 16 ? 1 : 2);

    int channelCount = maxChannel <= 8 ? 8 : (maxChannel <= 16 ? 16 : 24);

    int minPreSamples = 2;
    int maxPreSamples = channelMode == 0 ? 98303 : (channelMode == 1 ? 49151 : 24576);

    int minPostSamples = 512;
    int maxPostSamples = channelMode == 0 ? 131069 : (channelMode == 1 ? 65533 : 32765);

    int maxTotalSamples = channelMode == 0 ? 131071 : (channelMode == 1 ? 65535 : 32767);

    if (opts.PreSamples + opts.PostSamples > maxTotalSamples)
    {
        Console.WriteLine($"Total samples exceed the supported maximum ({maxTotalSamples} for the {channelCount} channel mode).");
        return -1;
    }

    if (opts.PreSamples < minPreSamples)
    {
        Console.WriteLine($"Pre-samples cannot be less than {minPreSamples}.");
        return -1;
    }

    if (opts.PreSamples > maxPreSamples)
    {
        Console.WriteLine($"Pre-samples cannot be more than {maxPreSamples} for the {channelCount} channel mode.");
        return -1;
    }

    if (opts.PostSamples < minPostSamples)
    {
        Console.WriteLine($"Post-samples cannot be less than {minPostSamples}.");
        return -1;
    }

    if (opts.PostSamples > maxPostSamples)
    {
        Console.WriteLine($"Post-samples cannot be more than {maxPostSamples} for the {channelCount} channel mode.");
        return -1;
    }

    if (opts.Trigger == null)
    {
        Console.WriteLine("Invalid trigger definition.");
        return -1;
    }

    if (opts.Trigger.Value == null)
    {
        Console.WriteLine("Invalid trigger value.");
        return -1;
    }

    switch (opts.Trigger.TriggerType)
    {
        case CLTriggerType.Edge:

            if (opts.Trigger.Channel < 1 || opts.Trigger.Channel > 24)
            {
                Console.WriteLine("Trigger channel out of range.");
                return -1;
            }

            break;

        case CLTriggerType.Fast:

            if (opts.Trigger.Value.Length > 5)
            {
                Console.WriteLine("Fast trigger only supports up to 5 channels.");
                return -1;
            }

            if (opts.Trigger.Value.Length + opts.Trigger.Channel > 17)
            {
                Console.WriteLine("Fast trigger can only be used with the first 16 channels.");
                return -1;
            }

            break;

        case CLTriggerType.Complex:

            if (opts.Trigger.Value.Length > 16)
            {
                Console.WriteLine("Complex trigger only supports up to 16 channels.");
                return -1;
            }

            if (opts.Trigger.Value.Length + opts.Trigger.Channel > 17)
            {
                Console.WriteLine("Complex trigger can only be used with the first 16 channels.");
                return -1;
            }

            break;
    }

    Console.WriteLine($"Opening logic analyzer in {opts.AddressPort}...");

    try
    {
        driver = new LogicAnalyzerDriver(opts.AddressPort);
    }
    catch
    {
        Console.WriteLine($"Error detecting Logic Analyzer in port/address {opts.AddressPort}");
        return -1;
    }

    Console.WriteLine($"Connected to device {driver.DeviceVersion} in port/address {opts.AddressPort}");

    captureCompletedTask = new TaskCompletionSource<CaptureEventArgs>();

    int[] nChannels = channels.Select(c => c.ChannelNumber - 1).ToArray();

    if (opts.Trigger.TriggerType == CLTriggerType.Edge)
    {
        Console.WriteLine("Starting edge triggered capture...");
        var resStart = driver.StartCapture(opts.SamplingFrequency, opts.PreSamples, opts.PostSamples, opts.LoopCount < 2 ? 0 : opts.LoopCount - 1, nChannels, opts.Trigger.Channel - 1, opts.Trigger.Value == "0", CaptureFinished);

        if (resStart != CaptureError.None)
        {
            switch (resStart)
            {
                case CaptureError.Busy:
                    Console.WriteLine("Device is busy, stop the capture before starting a new one.");
                    return -1;
                case CaptureError.BadParams:
                    Console.WriteLine("Specified parameters are incorrect.\r\n\r\n    -Frequency must be between 3.1Khz and 100Mhz\r\n    -PreSamples must be between 2 and 31743\r\n    -PostSamples must be between 512 and 32767\r\n    -Total samples cannot exceed 32767");
                    return -1;
                case CaptureError.HardwareError:
                    Console.WriteLine("Device reported error starting capture. Restart the device and try again.");
                    return -1;
                case CaptureError.UnexpectedError:
                    Console.WriteLine("Unexpected error. Restart the device and try again.");
                    return -1;
            }
        }

        Console.WriteLine("Capture running...");
    }
    else
    {
        if (opts.Trigger.TriggerType == CLTriggerType.Fast)
            Console.WriteLine("Starting fast pattern triggered capture");
        else
            Console.WriteLine("Starting complex pattern triggered capture");

        int bitCount = opts.Trigger.Value.Length;
        ushort triggerPattern = 0;

        for (int buc = 0; buc < opts.Trigger.Value.Length; buc++)
        {
            if (opts.Trigger.Value[buc] == '1')
                triggerPattern |= (UInt16)(1 << buc);
        }

        var resStart = driver.StartPatternCapture(opts.SamplingFrequency, opts.PreSamples, opts.PostSamples,
            nChannels, opts.Trigger.Channel - 1, bitCount, triggerPattern, opts.Trigger.TriggerType == CLTriggerType.Fast, CaptureFinished);

        if (resStart != CaptureError.None)
        {
            switch (resStart)
            {
                case CaptureError.Busy:
                    Console.WriteLine("Device is busy, stop the capture before starting a new one.");
                    return -1;
                case CaptureError.BadParams:
                    Console.WriteLine("Specified parameters are incorrect. Check the documentation in the repository to validate them.");
                    return -1;
                case CaptureError.HardwareError:
                    Console.WriteLine("Device reported error starting capture. Restart the device and try again.");
                    return -1;
                case CaptureError.UnexpectedError:
                    Console.WriteLine("Unexpected error. Restart the device and try again.");
                    return -1;
            }
        }

        Console.WriteLine("Capture running...");
    }

    var result = await captureCompletedTask.Task;

    if (result.Samples == null)
    {
        Console.WriteLine("Capture aborted.");
        return -1;
    }

    Console.WriteLine("Capture complete, writing output file...");

    var file = File.Create(opts.OutputFile);
    StreamWriter sw = new StreamWriter(file);

    sw.WriteLine(String.Join(',', channels.Select(c => c.ChannelName).ToArray()));

    StringBuilder sb = new StringBuilder();

    for (int sample = 0; sample < result.Samples.Length; sample++)
    {
        sb.Clear();

        for (int buc = 0; buc < nChannels.Length; buc++)
        {
            if ((result.Samples[sample] & ((UInt128)1 << nChannels[buc])) == 0)
                sb.Append("0,");
            else
                sb.Append("1,");
        }
        sb.Remove(sb.Length - 1, 1);
        sw.WriteLine(sb.ToString());
    }

    sw.Close();
    sw.Dispose();
    file.Close();
    file.Dispose();

    Console.WriteLine("Done.");

    return 1;
}

int Configure(CLNetworkOptions opts)
{
    var ports = SerialPort.GetPortNames();

    if (!ports.Any(p => p.ToLower() == opts.SerialPort))
    {
        Console.WriteLine("Cannot find specified serial port.");
        return -1;
    }

    if (opts.AccessPoint.Length > 32)
    {
        Console.WriteLine("Invalid access point name.");
        return -1;
    }

    if (opts.Password.Length > 63)
    {
        Console.WriteLine("Invalid password.");
        return -1;
    }

    if (!regAddress.IsMatch(opts.Address))
    {
        Console.WriteLine("Invalid IP address.");
        return -1;
    }

    if (opts.Port < 1)
    {
        Console.WriteLine("Invalid TCP port.");
        return -1;
    }

    

    Console.WriteLine($"Opening logic analyzer in port {opts.SerialPort}...");

    try
    {
        driver = new LogicAnalyzerDriver(opts.SerialPort);
    }
    catch
    {
        Console.WriteLine($"Error detecting Logic Analyzer in port {opts.SerialPort}");
        return -1;
    }

    Console.WriteLine($"Connected to device {driver.DeviceVersion} in port {opts.SerialPort}");

    if (driver.DeviceVersion == null || !driver.DeviceVersion.Contains("WIFI"))
    {
        Console.WriteLine($"Device does not support WiFi. Aborting operation.");
        driver.Dispose();
        return -1;
    }

    bool result = driver.SendNetworkConfig(opts.AccessPoint, opts.Password, opts.Address, opts.Port);

    if (!result)
    {
        Console.WriteLine("Error updating the network settings, restart the device and try again.");
        driver.Dispose();
        return -1;
    }

    driver.Dispose();
    Console.WriteLine("Done.");

    return 1;
}

void CaptureFinished(CaptureEventArgs e)
{
    captureCompletedTask.SetResult(e);
}

void Console_CancelKeyPress(object? sender, ConsoleCancelEventArgs e)
{
    if (driver != null)
    {
        try
        {
            driver.StopCapture();
            driver.Dispose();
        }
        catch { }
        driver = null;
    }
}
