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
using System.Threading.Channels;
using System.Threading.Tasks;
using static System.Collections.Specialized.BitVector32;

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
        public override int BlastFrequency
        {
            get
            {
                throw new NotImplementedException();
            }
        }
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
        deviceCapture[]? tempCapture;
        CaptureSession? sourceSession;

        object locker = new object();

        //General data
        bool capturing = false;
        string? version;

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

        public override CaptureError StartCapture(CaptureSession Session, Action<CaptureEventArgs>? CaptureCompletedHandler = null)
        {
            if (Session.TriggerType == TriggerType.Edge)
                return CaptureError.BadParams;

            try
            {
                if (capturing)
                    return CaptureError.Busy;

                if (Session.CaptureChannels == null || Session.CaptureChannels.Length < 0)
                    return CaptureError.BadParams;

                var numChan = Session.CaptureChannels.Select(c => c.ChannelNumber).ToArray();

                var captureLimits = GetLimits(numChan);
                var captureMode = GetCaptureMode(numChan);

                if (
                numChan.Min() < 0 ||
                numChan.Max() > ChannelCount - 1 ||
                Session.TriggerBitCount < 1 ||
                Session.TriggerBitCount > 16 ||
                Session.TriggerChannel < 0 ||
                Session.TriggerChannel > 15 ||
                Session.TriggerChannel + Session.TriggerBitCount > (Session.TriggerType == TriggerType.Complex ? 16 : 5) ||
                Session.PreTriggerSamples < captureLimits.MinPreSamples ||
                Session.PostTriggerSamples < captureLimits.MinPostSamples ||
                Session.PreTriggerSamples > captureLimits.MaxPreSamples ||
                Session.PostTriggerSamples > captureLimits.MaxPostSamples ||
                Session.PreTriggerSamples + Session.PostTriggerSamples > captureLimits.MaxTotalSamples ||
                Session.Frequency < MinFrequency ||
                Session.Frequency > MaxFrequency
                )
                    return CaptureError.BadParams;


                int[][] channelsPerDevice = SplitChannelsPerDevice(numChan);

                if (channelsPerDevice.Length > numChan.Length)
                    return CaptureError.BadParams;

                if (channelsPerDevice[0].Length < 1)
                    return CaptureError.BadParams;

                double samplePeriod = 1000000000.0 / Session.Frequency;
                double delay = Session.TriggerType == TriggerType.Fast ? TriggerDelays.FastTriggerDelay : TriggerDelays.ComplexTriggerDelay;
                int offset = (int)(Math.Round((delay / samplePeriod) + 0.3, 0));

                tempCapture = new deviceCapture[connectedDevices.Length];

                for (int bc = 0; bc < tempCapture.Length; bc++)
                    tempCapture[bc] = new deviceCapture();

                currentCaptureHandler = CaptureCompletedHandler;
                sourceSession = Session;

                capturing = true;

                int channelsCapturing = 1;
                
                //Start capturing on all devices except master, master will be the last one to start
                for (int buc = 1; buc < channelsPerDevice.Length; buc++)
                {
                    var chan = channelsPerDevice[buc];

                    if (chan.Length == 0)
                    {
                        tempCapture[buc].Completed = true;
                        continue;
                    }

                    var devSes = Session.Clone();

                    devSes.CaptureChannels = new AnalyzerChannel[chan.Length];

                    for(int bChan = 0; bChan < chan.Length; bChan++)
                        devSes.CaptureChannels[bChan] = new AnalyzerChannel { ChannelNumber = chan[bChan] };

                    devSes.TriggerChannel = 24;
                    devSes.TriggerType = TriggerType.Edge;
                    devSes.PreTriggerSamples = Session.PreTriggerSamples + offset;
                    devSes.PostTriggerSamples = Session.PostTriggerSamples - offset;
                    devSes.LoopCount = 0;
                    devSes.MeasureBursts = false;
                    devSes.TriggerInverted = false;

                    connectedDevices[buc].Tag = channelsCapturing;
                    var err = connectedDevices[buc].StartCapture(devSes);

                    if (err != CaptureError.None)
                    {
                        StopCapture();
                        return err;
                    }

                    channelsCapturing++;
                }

                connectedDevices[0].Tag = 0;
                
                var chanMaster = channelsPerDevice[0];

                var masterSes = Session.Clone();
                masterSes.CaptureChannels = new AnalyzerChannel[chanMaster.Length];

                for (int bChan = 0; bChan < chanMaster.Length; bChan++)
                    masterSes.CaptureChannels[bChan] = new AnalyzerChannel { ChannelNumber = chanMaster[bChan] };

                var errMaster = connectedDevices[0].StartCapture(masterSes);

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
                if (!capturing)
                    return;

                if(!e.Success)
                {
                    StopCapture();

                    tempCapture = null;

                    if (currentCaptureHandler != null)
                        currentCaptureHandler(new CaptureEventArgs { Success = false, Session = sourceSession });
                    else if (CaptureCompleted != null)
                        CaptureCompleted(this, new CaptureEventArgs { Success = false, Session = sourceSession });

                    return;
                }

                int idx = (int)((sender as LogicAnalyzerDriver).Tag);

                tempCapture[idx].Session = e.Session;
                tempCapture[idx].Completed = true;

                if (tempCapture.All(c => c.Completed))
                {
                    var maxChanPerDev = connectedDevices.Min(c => c.ChannelCount);

                    for (int buc = 0; buc < tempCapture.Length; buc++)
                    {
                        if (tempCapture[buc].Session != null)
                        {
                            foreach(var chan in tempCapture[buc].Session.CaptureChannels)
                            {
                                var destChan = sourceSession.CaptureChannels.First(c => c.ChannelNumber == chan.ChannelNumber + buc * maxChanPerDev);

                                destChan.Samples = chan.Samples;
                            }
                        }
                    }

                    if (currentCaptureHandler != null)
                        currentCaptureHandler(new CaptureEventArgs { Success = true, Session = sourceSession });
                    else if (CaptureCompleted != null)
                        CaptureCompleted(this, new CaptureEventArgs { Success = true, Session = sourceSession });

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

        class deviceCapture
        {
            public bool Completed { get; set; }
            public CaptureSession? Session { get; set; }
        }
    }
}
