using System;
using System.Collections.Generic;
using System.Linq;
using System.Text;
using System.Threading.Tasks;

namespace SharedDriver
{
    internal static class TriggerDelays
    {
        public const double ComplexTriggerDelay = 5;
        public const double FastTriggerDelay = 3;
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
