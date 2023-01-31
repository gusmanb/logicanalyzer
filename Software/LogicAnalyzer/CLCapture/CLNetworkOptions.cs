using CommandLine;
using System;
using System.Collections.Generic;
using System.Linq;
using System.Text;
using System.Text.RegularExpressions;
using System.Threading.Tasks;

namespace CLCapture
{
    [Verb(name: "netconfig")]
    public class CLNetworkOptions
    {
        [Value(0, Required = true, HelpText = "Device's serial port.")]
        public string SerialPort { get; set; }
        [Value(1, Required = true, HelpText = "Access point name.")]
        public string AccessPoint { get; set; }
        [Value(2, Required = true, HelpText = "Access point password.")]
        public string Password { get; set; }
        [Value(3, Required = true, HelpText = "Device IP address.")]
        public string Address { get; set; }
        [Value(4, Required = true, HelpText = "Device TCP port.")]
        public ushort Port { get; set; }
    }

}
