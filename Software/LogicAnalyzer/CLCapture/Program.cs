using CLCapture;
using CommandLine;
using Newtonsoft.Json;
using SharedDriver;
using System.IO.Ports;
using System.Linq;
using System.Runtime.CompilerServices;
using System.Text;
using System.Text.Json.Serialization;
using System.Text.RegularExpressions;
using System.Threading.Channels;

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

    if(string.IsNullOrWhiteSpace(opts.OutputFile))
    {
        Console.WriteLine("Output file not specified.");
        return -1;
    }

    string ext = Path.GetExtension(opts.OutputFile).ToLower();

    if (ext != ".csv" || ext != ".lac")
    {
        Console.WriteLine("Unsupported output file type. Must be .csv or .lac.");
        return -1;
    }

    CLChannel[]? channels;

    try
    {

        channels = opts.Channels?.Split(",", StringSplitOptions.RemoveEmptyEntries).Select(c => new CLChannel(c)).ToArray();

        if (channels == null || channels.Any(c => c.ChannelNumber < 1 || c.ChannelNumber > 24))
        {
            Console.WriteLine("Specified capture channels out of range.");
            return -1;
        }

    }
    catch (Exception ex)
    {
        Console.WriteLine(ex.Message);
        return -1;
    }

    if(opts.Trigger == null || opts.Trigger.Value == null)
    {
        Console.WriteLine("Invalid trigger definition.");
        return -1;
    }

    switch (opts.Trigger.TriggerType)
    {
        case TriggerType.Edge:

            if (opts.Trigger.Channel < 1 || opts.Trigger.Channel > 24)
            {
                Console.WriteLine("Trigger channel out of range.");
                return -1;
            }

            break;

        case TriggerType.Fast:

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

        case TriggerType.Complex:

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

    CaptureSession session = new CaptureSession();
    session.Frequency = opts.SamplingFrequency;
    session.PreTriggerSamples = opts.PreSamples;
    session.PostTriggerSamples = opts.PostSamples;
    session.CaptureChannels = channels.OrderBy(c => c.ChannelNumber).Select(c => new AnalyzerChannel { ChannelNumber = c.ChannelNumber - 1, ChannelName = c.ChannelName }).ToArray();
    session.LoopCount = opts.BurstCount > 1 ? opts.BurstCount - 1 : 0;
    session.MeasureBursts = opts.MeasureBurst;
    session.TriggerType = opts.Trigger.TriggerType;
    session.TriggerChannel = opts.Trigger.Channel - 1;

    if (session.TriggerType == TriggerType.Edge)
    {
        session.TriggerInverted = opts.Trigger.Value == "0";
    }
    else
    {
        session.TriggerBitCount = opts.Trigger.Value.Length;
        session.TriggerPattern = 0;

        for (int buc = 0; buc < opts.Trigger.Value.Length; buc++)
        {
            if (opts.Trigger.Value[buc] == '1')
                session.TriggerPattern |= (UInt16)(1 << buc);
        }
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
    Console.WriteLine($"Device max. frequency: {driver.MaxFrequency}");
    Console.WriteLine($"Device max. channels: {driver.ChannelCount}");
    Console.WriteLine($"Device buffer size: {driver.BufferSize}");

    if (opts.SamplingFrequency > driver.MaxFrequency || opts.SamplingFrequency < driver.MinFrequency)
    {
        driver.Dispose();
        Console.WriteLine($"Requested sampling frequency out of device's capabilities ({driver.MinFrequency}-{driver.MaxFrequency}).");
        return -1;
    }

    var limits = driver.GetLimits(session.CaptureChannels.Select(c => c.ChannelNumber).ToArray());

    if(session.PreTriggerSamples > limits.MaxPreSamples || session.PreTriggerSamples < limits.MinPreSamples)
    {
        driver.Dispose();
        Console.WriteLine($"Requested pre-trigger samples out of device's capabilities ({limits.MinPreSamples}-{limits.MaxPreSamples}).");
        return -1;
    }

    if (session.PostTriggerSamples > limits.MaxPostSamples || session.PostTriggerSamples < limits.MinPostSamples)
    {
        driver.Dispose();
        Console.WriteLine($"Requested post-trigger samples out of device's capabilities ({limits.MinPostSamples}-{limits.MaxPostSamples}).");
        return -1;
    }

    if(session.TotalSamples > limits.MaxTotalSamples)
    {
        driver.Dispose();
        Console.WriteLine($"Requested total samples exceed device's capabilities ({limits.MaxTotalSamples}).");
        return -1;
    }

    captureCompletedTask = new TaskCompletionSource<CaptureEventArgs>();

    Console.WriteLine("Starting capture...");
    var resStart = driver.StartCapture(session, CaptureFinished);

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

    var result = await captureCompletedTask.Task;

    if (!result.Success)
    {
        Console.WriteLine("Error capturing data.");
        return -1;
    }

    driver.Dispose();

    Console.WriteLine("Capture complete, writing output file(s)...");

    await WriteOutput(session, opts.OutputFile);

    Console.WriteLine("Done.");

    return 1;
}

async Task WriteOutput(CaptureSession session, string outputFile)
{
    string ext = Path.GetExtension(outputFile).ToLower();

    if (ext == ".csv")
    {
        await WriteCSV(session, outputFile);
    }
    else if (ext == ".lac")
    {
        await WriteLAC(session, outputFile);
    }
}

async Task WriteLAC(CaptureSession session, string outputFile)
{
    var content = JsonConvert.SerializeObject(new ExportedCapture { Settings = session });
    await File.WriteAllTextAsync(outputFile, content);
}

async Task WriteCSV(CaptureSession session, string outputFile)
{
    var file = File.Create(outputFile);
    StreamWriter sw = new StreamWriter(file);

    sw.WriteLine(String.Join(',', session.CaptureChannels.Select(c => c.ChannelName).ToArray()));

    StringBuilder sb = new StringBuilder();

    for (int sample = 0; sample < session.TotalSamples; sample++)
    {
        sb.Clear();

        for (int buc = 0; buc < session.CaptureChannels.Length; buc++)
        {
            if (session.CaptureChannels[buc].Samples?[sample] == 1)
                sb.Append("1,");
            else
                sb.Append("0,");
        }
        sb.Remove(sb.Length - 1, 1);
        await sw.WriteLineAsync(sb.ToString());
    }

    sw.Close();
    sw.Dispose();
    file.Close();
    file.Dispose();

    if (session.Bursts != null && session.Bursts.Length > 0)
    {
        var outBursts = Path.Combine(Path.GetDirectoryName(outputFile) ?? "", Path.GetFileNameWithoutExtension(outputFile) + "_bursts.csv");
        file = File.Create(outBursts);

        sw = new StreamWriter(file);

        sw.WriteLine("Start,End,SampleGap,TimeGap");

        foreach (var burst in session.Bursts)
        {
            await sw.WriteLineAsync($"{burst.BurstSampleStart},{burst.BurstSampleEnd},{burst.BurstSampleGap},{burst.BurstTimeGap}");
        }

        sw.Close();
        sw.Dispose();
        file.Close();
        file.Dispose();
    }

}

int Configure(CLNetworkOptions opts)
{
    var ports = SerialPort.GetPortNames();

    if (!ports.Any(p => p.ToLower() == opts.SerialPort.ToLower()))
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

class ExportedCapture
{
    public required CaptureSession Settings { get; set; }
}