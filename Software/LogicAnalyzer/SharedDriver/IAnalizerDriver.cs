using System;
using System.Collections.Generic;
using System.Linq;
using System.Text;
using System.Threading.Tasks;

namespace SharedDriver
{
    public interface IAnalizerDriver : IDisposable
    {
        public string? DeviceVersion { get; }
        public bool IsCapturing { get; }
        public bool IsNetwork { get; }
        public AnalyzerDriverType DriverType { get; }
        public int Channels { get; }
        public event EventHandler<CaptureEventArgs> CaptureCompleted;
        public bool SendNetworkConfig(string AccesPointName, string Password, string IPAddress, ushort Port);
        public CaptureError StartCapture(int Frequency, int PreSamples, int PostSamples, int LoopCount, int[] Channels, int TriggerChannel, bool TriggerInverted, Action<CaptureEventArgs>? CaptureCompletedHandler = null);
        public CaptureError StartPatternCapture(int Frequency, int PreSamples, int PostSamples, int[] Channels, int TriggerChannel, int TriggerBitCount, UInt16 TriggerPattern, bool Fast, Action<CaptureEventArgs>? CaptureCompletedHandler = null);
        public bool StopCapture();
        public CaptureLimits GetLimits(int[] Channels);

        public string? GetVoltageStatus();
    }

    public class CaptureEventArgs : EventArgs
    {
        public AnalyzerDriverType SourceType { get; set; }
        public int TriggerChannel { get; set; }
        public int ChannelCount { get; set; }
        public int PreSamples { get; set; }
        public UInt128[] Samples { get; set; }
    }

    public enum AnalyzerDriverType
    { 
        Serial,
        Network,
        Multi,
        Emulated
    }

    public enum CaptureError
    {
        None,
        Busy,
        BadParams,
        HardwareError,
        UnexpectedError
    }

}
