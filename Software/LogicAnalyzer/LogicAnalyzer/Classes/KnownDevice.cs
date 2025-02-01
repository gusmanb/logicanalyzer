using System;
using System.Collections.Generic;
using System.Linq;
using System.Text;
using System.Threading.Tasks;

namespace LogicAnalyzer.Classes
{
    public class KnownDevice
    {
        public KnownDeviceEntry[] Entries { get; set; }
    }

    public class KnownDeviceEntry
    {
        public string SerialNumber { get; set; }
        public int Order { get; set; }
    }
}
