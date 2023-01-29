using CLCapture;
using CommandLine;
using SharedDriver;
using System.IO.Ports;
using System.Linq;
using System.Text;

TaskCompletionSource<CaptureEventArgs> captureCompletedTask;

return await Parser.Default.ParseArguments<CLCaptureCommandLineOptions>(args)
        .MapResult(async (CLCaptureCommandLineOptions opts) =>
        {
            if (string.IsNullOrWhiteSpace(opts.OutputFile))
            {
                Console.WriteLine("Missing serial port.");
                return -1;
            }

            if (opts.SerialPort == null)
            {
                Console.WriteLine("Missing serial port.");
                return -1;
            }

            var ports = SerialPort.GetPortNames();

            if (!ports.Any(p => p.ToLower() == opts.SerialPort.ToLower()))
            {
                Console.WriteLine("Cannot find specified serial port.");
                return -1;
            }

            if (opts.SamplingFrequency > 100000000 || opts.SamplingFrequency < 3100)
            {
                Console.WriteLine("Requested sampling frequency out of range (3100-100000000).");
                return -1;
            }

            int[]? channels = opts.Channels?.Split(",", StringSplitOptions.RemoveEmptyEntries).Select(c => int.Parse(c)).ToArray();

            if (channels == null || channels.Any(c => c < 1 || c > 24))
            {
                Console.WriteLine("Specified capture channels out of range.");
                return -1;
            }

            if (opts.PreSamples + opts.PostSamples > 32767)
            {
                Console.WriteLine("Total samples exceed the supported maximum (32767).");
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

            LogicAnalyzerDriver driver;

            Console.WriteLine($"Opening logic analyzer in port {opts.SerialPort}...");

            try
            {
                driver = new LogicAnalyzerDriver(opts.SerialPort, 115200);
            }
            catch 
            {
                Console.WriteLine($"Error detecting Logic Analyzer in port {opts.SerialPort}");
                return -1;
            }

            Console.WriteLine($"Conneced to device {driver.DeviceVersion} in port {opts.SerialPort}");

            captureCompletedTask = new TaskCompletionSource<CaptureEventArgs>();

            channels = opts.Channels.Split(",", StringSplitOptions.RemoveEmptyEntries).Select(c => int.Parse(c) - 1).ToArray();

            if (opts.Trigger.TriggerType == CLTriggerType.Edge)
            {
                Console.WriteLine("Starting edge triggered capture...");
                var resStart = driver.StartCapture(opts.SamplingFrequency, opts.PreSamples, opts.PostSamples,
                    channels, opts.Trigger.Channel - 1, opts.Trigger.Value == "0", CaptureFinished);

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
                    channels, opts.Trigger.Channel - 1, bitCount, triggerPattern, opts.Trigger.TriggerType == CLTriggerType.Fast, CaptureFinished);

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
                    }
                }

                Console.WriteLine("Capture running...");
            }

            var result = await captureCompletedTask.Task;

            Console.WriteLine("Capture complete, writting output file...");

            var file = File.Create(opts.OutputFile);
            StreamWriter sw = new StreamWriter(file);

            sw.WriteLine(String.Join(',', channels.Select(c => $"Channel {c+1}").ToArray()));

            StringBuilder sb = new StringBuilder();

            for (int sample = 0; sample < result.Samples.Length; sample++)
            {
                sb.Clear();

                for (int buc = 0; buc < opts.Channels.Length; buc++)
                {
                    if((result.Samples[sample] & (1 << buc)) == 0)
                        sb.Append("0,");
                    else
                        sb.Append("1,");
                }

                sw.WriteLine(sb.ToString());
            }

            sw.Close();
            sw.Dispose();
            file.Close();
            file.Dispose();

            Console.WriteLine("Done.");
            
            return 1;

        },
        errs => Task.FromResult(-1));

void CaptureFinished(CaptureEventArgs e)
{
    captureCompletedTask.SetResult(e);
}