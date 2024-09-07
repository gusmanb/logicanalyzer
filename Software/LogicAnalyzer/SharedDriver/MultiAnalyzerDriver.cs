using System;
using System.Collections.Generic;
using System.ComponentModel.DataAnnotations;
using System.Diagnostics;
using System.IO.Ports;
using System.Linq;
using System.Net.Sockets;
using System.Runtime.InteropServices;
using System.Text;
using System.Text.RegularExpressions;
using System.Threading.Tasks;

namespace SharedDriver
{
    public class MultiAnalyzerDriver : AnalyzerDriverBase
    {

        #region Properties
        public override bool IsCapturing { get { return capturing; } }
        public override bool IsNetwork { get { return false; } }
        public override string? DeviceVersion { get { return version; } }
        public override int ChannelCount { get { return connectedDevices.Min(d => d.ChannelCount) * connectedDevices.Length; } }
        public override int MaxFrequency { get { return connectedDevices.Min(d => d.MaxFrequency); } }
        public override int MinFrequency { get { return connectedDevices.Max(d => d.MinFrequency); } }
        public override int BufferSize { get { return connectedDevices.Min(d => d.BufferSize); } }
        public override AnalyzerDriverType DriverType
        {
            get
            {
                return AnalyzerDriverType.Multi;
            }
        }
        #endregion

        #region Events
        public override event EventHandler<CaptureEventArgs>? CaptureCompleted;
        #endregion

        #region Variables

        //Multidevice variables
        LogicAnalyzerDriver[] connectedDevices;
        UInt128[][]? tempCapture;
        bool[]? captureFinished;
        int[][]? tempChannels;
        object locker = new object();

        //General data
        bool capturing = false;
        string? version;
        int channelCount;

        //Current capture data
        private int triggerChannel;
        private int preSamples;

        //Optional callback
        private Action<CaptureEventArgs>? currentCaptureHandler;
        #endregion

        public MultiAnalyzerDriver(string[] ConnectionStrings) //First connection string must belong to the master device
        {
            if (ConnectionStrings == null || ConnectionStrings.Length < 2 || ConnectionStrings.Length > 5)
                throw new ArgumentOutOfRangeException(nameof(ConnectionStrings), $"Invalid devices specified, 2 to 5 connection strings must be provided");

            int pos = 0;
            connectedDevices = new LogicAnalyzerDriver[ConnectionStrings.Length];

            try
            {
                for (pos = 0; pos < ConnectionStrings.Length; pos++)
                {
                    connectedDevices[pos] = new LogicAnalyzerDriver(ConnectionStrings[pos]);
                }
                foreach (var dev in connectedDevices)
                    dev.CaptureCompleted += Dev_CaptureCompleted;


            }
            catch (Exception ex)
            {
                for (int buc = 0; buc < connectedDevices.Length; buc++)
                {
                    if (connectedDevices[buc] != null)
                        connectedDevices[buc].Dispose();
                }

                throw new DeviceConnectionException($"Error connecting to device {ConnectionStrings[pos]}.", ex);
            }

            DeviceVersion? masterVersion = null;

            foreach (var device in connectedDevices)
            {

                var devVer = VersionValidator.GetVersion(device.DeviceVersion);

                if (!devVer.IsValid)
                {
                    Dispose();
                    throw new DeviceConnectionException($"Invalid device version ({device.DeviceVersion}) found on device {ConnectionStrings[(int)device.Tag]}");
                }

                if (masterVersion == null)
                    masterVersion = devVer;
                else
                {
                    if (masterVersion.Major != devVer.Major || masterVersion.Minor != devVer.Minor)
                    {
                        Dispose();
                        throw new DeviceConnectionException($"Different device versions found. Master version: V{masterVersion.Major}_{masterVersion.Minor}, device {ConnectionStrings[(int)device.Tag]} version: V{devVer.Major}_{devVer.Minor}.");
                    }
                }
            }

            if (masterVersion == null)
                throw new DeviceConnectionException("No devices found.");

            version = $"MULTI_ANALYZER_{masterVersion.Major}_{masterVersion.Minor}";
        }

        #region Capture code

        public override CaptureError StartCapture(int Frequency, int PreSamples, int PostSamples, int LoopCount, bool MeasureBursts, int[] Channels, int TriggerChannel, bool TriggerInverted, Action<CaptureEventArgs>? CaptureCompletedHandler = null)
        {

            return CaptureError.HardwareError;
        }
        public override CaptureError StartPatternCapture(int Frequency, int PreSamples, int PostSamples, int[] Channels, int TriggerChannel, int TriggerBitCount, UInt16 TriggerPattern, bool Fast, Action<CaptureEventArgs>? CaptureCompletedHandler = null)
        {
            try
            {
                if (capturing)
                    return CaptureError.Busy;

                if (Channels == null || Channels.Length < 0)
                    return CaptureError.BadParams;

                var captureLimits = GetLimits(Channels);
                var captureMode = GetCaptureMode(Channels);

                if (
                Channels.Min() < 0 ||
                Channels.Max() > ChannelCount - 1 ||
                TriggerBitCount < 1 ||
                TriggerBitCount > 16 ||
                TriggerChannel < 0 ||
                TriggerChannel > 15 ||
                PreSamples < captureLimits.MinPreSamples ||
                PostSamples < captureLimits.MinPostSamples ||
                PreSamples > captureLimits.MaxPreSamples ||
                PostSamples > captureLimits.MaxPostSamples ||
                PreSamples + PostSamples > captureLimits.MaxTotalSamples ||
                Frequency < MinFrequency ||
                Frequency > MaxFrequency
                )
                    return CaptureError.BadParams;


                int[][] channelsPerDevice = SplitChannelsPerDevice(Channels);

                if (channelsPerDevice.Length > Channels.Length)
                    return CaptureError.BadParams;

                if (channelsPerDevice[0].Length < 1)
                    return CaptureError.BadParams;

                double samplePeriod = 1000000000.0 / Frequency;
                double delay = Fast ? TriggerDelays.FastTriggerDelay : TriggerDelays.ComplexTriggerDelay;
                int offset = (int)(Math.Round((delay / samplePeriod) + 0.3, 0));

                channelCount = Channels.Length;
                triggerChannel = TriggerChannel;
                preSamples = PreSamples;
                currentCaptureHandler = CaptureCompletedHandler;

                capturing = true;

                int channelsCapturing = 1;

                //Start capturing on all devices except master, master will be the last one to start
                for (int buc = 1; buc < channelsPerDevice.Length; buc++)
                {
                    var chan = channelsPerDevice[buc];

                    if (chan.Length == 0)
                        continue;

                    connectedDevices[buc].Tag = channelsCapturing;
                    var err = connectedDevices[buc].StartCapture(Frequency, PreSamples + offset, PostSamples - offset, 0, false, chan, 24, false);

                    if (err != CaptureError.None)
                    {
                        StopCapture();
                        return err;
                    }

                    channelsCapturing++;
                }

                connectedDevices[0].Tag = 0;
                tempCapture = new UInt128[channelsCapturing][];
                captureFinished = new bool[channelsCapturing];
                tempChannels = channelsPerDevice.Where(c => c.Length > 0).ToArray();

                var chanMaster = channelsPerDevice[0];

                var errMaster = connectedDevices[0].StartPatternCapture(Frequency, PreSamples, PostSamples, chanMaster, TriggerChannel, TriggerBitCount, TriggerPattern, Fast);

                if (errMaster != CaptureError.None)
                {
                    StopCapture();
                    return errMaster;
                }

                return CaptureError.None;
            }
            catch { return CaptureError.UnexpectedError; }
        }

        public override bool StopCapture()
        {
            if (!capturing)
                return false;

            foreach (var dev in connectedDevices)
                dev.StopCapture();

            capturing = false;

            return true;
        }

        private void Dev_CaptureCompleted(object? sender, CaptureEventArgs e)
        {
            lock (locker)
            {
                int idx = (int)((sender as LogicAnalyzerDriver).Tag);

                tempCapture[idx] = e.Samples;
                captureFinished[idx] = true;

                if (captureFinished.All(c => c))
                {
                    UInt128[] finalSamples = new UInt128[tempCapture[idx].Length];

                    for (int buc = 0; buc < finalSamples.Length; buc++)
                    {
                        int bitPos = 0;

                        for (int devNum = 0; devNum < tempCapture.Length; devNum++)
                        {
                            int len = tempChannels[idx].Length;

                            UInt128 devMask = ((UInt128)1 << len) - 1;

                            UInt128 devSample = tempCapture[devNum][buc] & devMask;

                            finalSamples[buc] |= devSample << bitPos;
                            bitPos += len;
                        }
                    }

                    if (currentCaptureHandler != null)
                        currentCaptureHandler(new CaptureEventArgs { Samples = finalSamples, ChannelCount = channelCount, TriggerChannel = triggerChannel, PreSamples = preSamples });
                    else if (CaptureCompleted != null)
                        CaptureCompleted(this, new CaptureEventArgs { Samples = finalSamples, ChannelCount = channelCount, TriggerChannel = triggerChannel, PreSamples = preSamples });

                    capturing = false;
                }
            }
        }

        #endregion

        #region Device information functions
        public override CaptureMode GetCaptureMode(int[] Channels)
        {
            var split = SplitChannelsPerDevice(Channels);
            var maxChannel = split.Select(c => c.DefaultIfEmpty(0).Max()).DefaultIfEmpty(0).Max();
            return maxChannel < 8 ? CaptureMode.Channels_8 : (maxChannel < 16 ? CaptureMode.Channels_16 : CaptureMode.Channels_24);
        }

        private int[][] SplitChannelsPerDevice(int[] Channels)
        {
            List<int[]> channelsPerDevice = new List<int[]>();

            var maxChanPerDev = connectedDevices.Min(c => c.ChannelCount);

            for (int buc = 0; buc < connectedDevices.Length; buc++)
            {
                int firstChan = buc * maxChanPerDev;
                int lastChan = (buc + 1) * maxChanPerDev;

                int[] devChan = Channels.Where(c => c >= firstChan && c < lastChan).Select(c => c - firstChan).ToArray();
                channelsPerDevice.Add(devChan);
            }

            return channelsPerDevice.ToArray();
        }

        public override CaptureLimits GetLimits(int[] Channels)
        {

            var split = SplitChannelsPerDevice(Channels);
            var limits = connectedDevices.Select((dev, idx) => dev.GetLimits(split[idx])).ToArray();

            var minimalLimits = new CaptureLimits
            {
                MinPreSamples = limits.Max(l => l.MinPreSamples),
                MaxPreSamples = limits.Min(l => l.MaxPreSamples),
                MinPostSamples = limits.Max(l => l.MinPostSamples),
                MaxPostSamples = limits.Min(l => l.MaxPostSamples),
                /*
                MinFrequency = limits.Max(l => l.MinFrequency),
                MaxFrequency = limits.Min(l => l.MaxFrequency),
                MinChannel = 0,
                MaxChannel = limits.Min(l => l.MaxChannelCount) * connectedDevices.Length - 1,
                MaxChannelCount = limits.Min(l => l.MaxChannelCount) * connectedDevices.Length */
            };

            return minimalLimits;
        }
        #endregion

        #region Network-related functions
        public override unsafe bool SendNetworkConfig(string AccesPointName, string Password, string IPAddress, ushort Port)
        {
            return false;
        }
        public override string? GetVoltageStatus()
        {
            return "UNSUPPORTED";
        }
        #endregion

        #region IDisposable implementation
        public override void Dispose()
        {
            foreach (var dev in connectedDevices)
                dev.Dispose();
        }
        #endregion
    }
}
