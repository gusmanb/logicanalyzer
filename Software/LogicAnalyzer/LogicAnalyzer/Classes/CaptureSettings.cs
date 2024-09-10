using Avalonia.Media;
using System;
using System.Collections.Generic;
using System.Linq;
using System.Text;
using System.Threading.Tasks;

namespace LogicAnalyzer.Classes
{
    public class CaptureSettings
    {
        public int Frequency { get; set; }
        public int PreTriggerSamples { get; set; }
        public int PostTriggerSamples { get; set; }
        public int TotalSamples 
        { 
            get 
            {
                return PostTriggerSamples * (MeasureBursts ? LoopCount + 1 : 1) + PreTriggerSamples;
            } 
        }
        public int LoopCount { get; set; }
        public bool MeasureBursts { get; set; }
        public CaptureChannel[] CaptureChannels { get; set; } = new CaptureChannel[0];
        public int TriggerType { get; set; }
        public int TriggerChannel { get; set; }
        public bool TriggerInverted { get; set; }
        public int TriggerBitCount { get; set; }
        public ushort TriggerPattern { get; set; }

        public CaptureSettings Clone()
        {
            return (CaptureSettings)MemberwiseClone();
        }
    }

    public class CaptureChannel
    {
        public string TextualChannelNumber { get { return $"Channel {ChannelNumber + 1}"; } }
        public int ChannelNumber { get; set; }
        public string ChannelName { get; set; } = "";
        public Color? ChannelColor { get; set; }
        public bool Hidden { get; set; }
        public byte[]? Samples { get; set; }

        public override string ToString()
        {
            return ChannelName ?? TextualChannelNumber;
        }
    }
}
