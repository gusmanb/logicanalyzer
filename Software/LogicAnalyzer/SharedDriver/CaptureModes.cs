using System;
using System.Collections.Generic;
using System.Linq;
using System.Text;
using System.Threading.Tasks;

namespace SharedDriver
{
    internal static class CaptureModes
    {
        public static CaptureLimits[] Modes = new CaptureLimits[]
        { 
            new CaptureLimits { MinPreSamples = 2, MaxPreSamples = 98303, MinPostSamples = 512, MaxPostSamples = 131069 },
            new CaptureLimits { MinPreSamples = 2, MaxPreSamples = 49151, MinPostSamples = 512, MaxPostSamples = 65533 },
            new CaptureLimits { MinPreSamples = 2, MaxPreSamples = 24576, MinPostSamples = 512, MaxPostSamples = 32765 }
        };
    }

    internal static class TriggerDelays
    {
        public const double ComplexTriggerDelay = 50;
        public const double FastTriggerDelay = 30;
    }

    public class CaptureLimits
    {
        public int MinPreSamples { get; set; }
        public int MaxPreSamples { get; set; }
        public int MinPostSamples { get; set; }
        public int MaxPostSamples { get; set; }
        public int MaxTotalSamples { get { return MinPreSamples + MaxPostSamples; } }
    }
}
