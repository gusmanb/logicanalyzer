using System;
using System.Collections.Generic;
using System.Linq;
using System.Text;
using System.Threading.Tasks;

namespace SharedDriver
{
    public class CaptureSettings
    {
        public int Frequency { get; set; }
        public int PreTriggerSamples { get; set; }
        public int PostTriggerSamples { get; set; }
        public int[] CaptureChannels { get; set; } = new int[0];
        public int TriggerType { get; set; }
        public int TriggerChannel { get; set; }
        public bool TriggerInverted { get; set; }
        public int TriggerBitCount { get; set; }
        public ushort TriggerPattern { get; set; }
    }
}
