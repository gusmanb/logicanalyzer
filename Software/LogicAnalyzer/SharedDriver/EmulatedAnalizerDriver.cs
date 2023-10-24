using System;
using System.Collections.Generic;
using System.Linq;
using System.Text;
using System.Threading.Tasks;

namespace SharedDriver
{
    public class EmulatedAnalizerDriver : IAnalizerDriver
    {
        int deviceCount;

        public bool IsConnected => false;
        public bool IsCapturing => false;
        public bool IsNetwork => false;
        public EmulatedAnalizerDriver(int DeviceCount)
        {
            deviceCount = DeviceCount;
            Channels = deviceCount * 24;
            DeviceVersion = $"EMULATED_ANALIZER_{DeviceCount}_DEVICES";
        }

        public string? DeviceVersion { get; private set; }

        public AnalyzerDriverType DriverType { get { return AnalyzerDriverType.Emulated; } }

        public int Channels { get; private set; }

        public event EventHandler<CaptureEventArgs> CaptureCompleted;

        public void Dispose()
        {
            
        }

        private byte GetCaptureMode(int[] Channels)
        {
            var split = SplitChannelsPerDevice(Channels);
            var maxChannel = split.Select(c => c.DefaultIfEmpty(0).Max()).DefaultIfEmpty(0).Max();
            return (byte)(maxChannel < 8 ? 0 : (maxChannel < 16 ? 1 : 2));
        }
        private int[][] SplitChannelsPerDevice(int[] Channels)
        {
            List<int[]> channelsPerDevice = new List<int[]>();

            for (int buc = 0; buc < deviceCount; buc++)
            {
                int firstChan = buc * 24;
                int lastChan = (buc + 1) * 24;

                int[] devChan = Channels.Where(c => c >= firstChan && c < lastChan).Select(c => c - firstChan).ToArray();
                channelsPerDevice.Add(devChan);
            }

            return channelsPerDevice.ToArray();
        }
        public CaptureLimits GetLimits(int[] Channels)
        {
            var mode = GetCaptureMode(Channels);
            return CaptureModes.Modes[mode];
        }

        public bool SendNetworkConfig(string AccesPointName, string Password, string IPAddress, ushort Port)
        {
            throw new NotSupportedException();
        }

        public CaptureError StartCapture(int Frequency, int PreSamples, int PostSamples, int LoopCount, int[] Channels, int TriggerChannel, bool TriggerInverted, Action<CaptureEventArgs>? CaptureCompletedHandler = null)
        {
            throw new NotSupportedException();
        }

        public CaptureError StartPatternCapture(int Frequency, int PreSamples, int PostSamples, int[] Channels, int TriggerChannel, int TriggerBitCount, ushort TriggerPattern, bool Fast, Action<CaptureEventArgs>? CaptureCompletedHandler = null)
        {
            throw new NotSupportedException();
        }

        public string? GetVoltageStatus()
        {
            return "UNSUPPORTED";
        }

        public bool StopCapture()
        {
            return true;
        }
    }
}
