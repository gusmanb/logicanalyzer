using System;
using System.Collections.Generic;
using System.Linq;
using System.Text;
using System.Threading.Tasks;

namespace SharedDriver
{

    public class EmulatedAnalyzerDriver : AnalyzerDriverBase
    {
        public override string? DeviceVersion { get { return version; } }

        public override int MaxFrequency { get { return 200000000; } }

        public override int ChannelCount { get { return channelCount; } }

        public override int BufferSize { get { return 1024 * 1024; } }

        public override AnalyzerDriverType DriverType { get { return AnalyzerDriverType.Emulated; } }

        public override bool IsNetwork { get { return false; } }

        public override bool IsCapturing { get { return false; } }

        public override event EventHandler<CaptureEventArgs>? CaptureCompleted;

        int deviceCount;
        int channelCount;
        string version;

        public EmulatedAnalyzerDriver(int DeviceCount)
        {
            deviceCount = DeviceCount;
            channelCount = deviceCount * 24;
            version = $"EMULATED_ANALIZER_{DeviceCount}_DEVICES";
        }

        public override CaptureError StartCapture(CaptureSession Session, Action<bool, CaptureSession>? CaptureCompletedHandler = null)
        {
            return CaptureError.HardwareError;
        }

        public override bool StopCapture()
        {
            return false;
        }


        public override CaptureMode GetCaptureMode(int[] Channels)
        {
            var split = SplitChannelsPerDevice(Channels);
            var maxChannel = split.Select(c => c.DefaultIfEmpty(0).Max()).DefaultIfEmpty(0).Max();
            return maxChannel < 8 ? CaptureMode.Channels_8 : (maxChannel < 16 ? CaptureMode.Channels_16 : CaptureMode.Channels_24);
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
        public override CaptureLimits GetLimits(int[] Channels)
        {
            var split = SplitChannelsPerDevice(Channels);
            var limits = Enumerable.Range(0, deviceCount).Select(i => base.GetLimits(split[i])).ToArray();

            var minimalLimits = new CaptureLimits
            {
                MinPreSamples = limits.Max(l => l.MinPreSamples),
                MaxPreSamples = limits.Min(l => l.MaxPreSamples),
                MinPostSamples = limits.Max(l => l.MinPostSamples),
                MaxPostSamples = limits.Min(l => l.MaxPostSamples)
            };

            return minimalLimits;
        }

    }
}
