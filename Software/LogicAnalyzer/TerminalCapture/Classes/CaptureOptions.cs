using CommandLine;
using System;
using System.Collections.Generic;
using System.Linq;
using System.Text;
using System.Threading.Tasks;

namespace TerminalCapture.Classes
{
    [Verb("gui", true, HelpText = "Generate a capture settings file.")]
    public class TerminalOptions
    {
    }

    [Verb("capture", HelpText = "Capture data from a logic analyzer.")]
    public class CaptureOptions
    {
        [Value(0, Required = true, HelpText = "Device's serial port.")]
        public string SerialPort { get; set; }
        [Value(1, Required = true, HelpText = "Capture settings file (.tcs or .lac).")]
        public string SettingsFile { get; set; }
        [Value(2, Required = true, HelpText = "Output file (.lac or .csv).")]
        public string OutputFile { get; set; }
    }
}
