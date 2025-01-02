﻿using System;
using System.Collections.Generic;
using System.Linq;
using System.Text;
using System.Text.RegularExpressions;
using System.Threading.Channels;
using System.Threading.Tasks;
using CommandLine;

namespace CLCapture
{
    [Verb(name: "capture", HelpText = "Start a signal capture.")]
    public class CLCaptureOptions
    {
        [Value(0, Required = true, HelpText = "Device's serial port or IP address and port.")]
        public string? AddressPort { get; set; }

        [Value(1, Required = true, HelpText = "Desired sampling frequency.")]
        public int SamplingFrequency { get; set; }

        [Value(2, Required = true, HelpText = "List of channels to capture (channels sepparated by comma, can contain a name adding a semicolon after the channel number, no spaces allowed).")]
        public string? Channels { get; set; }

        [Value(3, Required = true, HelpText = "Number of samples to capture before the trigger.")]
        public int PreSamples { get; set; }

        [Value(4, Required = true, HelpText = "Number of samples to capture after the trigger.")]
        public int PostSamples { get; set; }

        [Value(5, Required = true, HelpText = "Number of bursts to capture (0 or 1 to disable burst mode).")]
        public int LoopCount { get; set; }

        [Value(6, Required = true, HelpText = "Trigger definition in the form of \"TriggerType:(Edge, Fast or Complex),Channel:(base trigger channel),Value:(string containing 1's and 0's indicating each trigger chanel state)\".")]
        public CLTrigger? Trigger { get; set; }

        [Value(7, Required = true, HelpText = "Name of the output file.")]
        public string? OutputFile { get; set; }

        [Value(8, Required = false, HelpText = "Format of the output file. Can be csv|vcd or csv:vcd to export both")]
        public string? OutputFileFormat { get; set; }

        public bool ExportVCD => OutputFileFormat?.Contains("vcd") ?? false;

        public bool ExportCSV => string.IsNullOrEmpty(OutputFileFormat) || OutputFileFormat.Contains("csv");
    }

    public class CLTrigger
    {
        public CLTrigger(string Data) 
        {
            string[] parts = Data.Split(",", StringSplitOptions.RemoveEmptyEntries);

            if (parts == null || parts.Length != 3)
                throw new ArgumentException("Invalid trigger parameters.");

            foreach (var part in parts)
            {
                string[] components = part.Split(":", StringSplitOptions.RemoveEmptyEntries);

                if(components == null || components.Length != 2)
                    throw new ArgumentException("Invalid trigger parameters.");

                switch (components[0].ToLower())
                {
                    case "triggertype":

                        CLTriggerType type;
                        var typeParsed = Enum.TryParse<CLTriggerType>(components[1], true, out type);

                        if (!typeParsed)
                            throw new ArgumentException($"Unknown trigger type: {type}.");

                        TriggerType = type;

                        break;
                    case "channel":

                        int channel;

                        if(!int.TryParse(components[1], out channel))
                            throw new ArgumentException($"Invalid value for trigger channel.");

                        Channel = channel;

                        break;

                    case "value":

                        if(components[1].Any(v => v != '0' && v != '1'))
                            throw new ArgumentException($"Trigger values can only be composed of '0's or '1's.");

                        Value = components[1];

                        break;
                    default:
                        throw new ArgumentException($"Unknown trigger parameter: {components[0]}");
                }
            }
        }
        public CLTriggerType TriggerType { get; set; }
        public int Channel { get; set; }
        public string Value { get; set; }
    }

    public enum CLTriggerType
    {
        Edge,
        Fast,
        Complex
    }
}
