using System;
using System.Collections.Generic;
using System.Linq;
using System.Text;
using System.Threading.Tasks;

namespace SharedDriver
{

    public class CaptureSession
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
        public AnalyzerChannel[] CaptureChannels { get; set; } = [];
        public BurstInfo[]? Bursts { get; set; }
        public TriggerType TriggerType { get; set; }
        public int TriggerChannel { get; set; }
        public bool TriggerInverted { get; set; }
        public int TriggerBitCount { get; set; }
        public ushort TriggerPattern { get; set; }

        public CaptureSession Clone()
        {
            var newInst = (CaptureSession)MemberwiseClone();
            for (int i = 0; i < CaptureChannels.Length; i++)
            {
                newInst.CaptureChannels[i] = CaptureChannels[i].Clone();
            }
            return newInst;
        }
    }

    public enum TriggerType
    {
        Edge,
        Complex,
        Fast
    }
}
