using System;
using System.Collections.Generic;
using System.ComponentModel.DataAnnotations;
using System.Linq;
using System.Text;
using System.Text.RegularExpressions;
using System.Threading.Tasks;

namespace SharedDriver
{
    public class MultiAnalizerDriver : IDisposable, IAnalizerDriver
    {
        Regex regVersion = new Regex(".*?(V([0-9]+)_([0-9]+))$");
        LogicAnalyzerDriver[] connectedDevices;

        UInt128[][]? tempCapture;
        bool[]? captureFinished;
        int[][]? tempChannels;

        object locker = new object();
        
        public int Channels { get { return connectedDevices.Length * 24; } }
        public LogicAnalyzerDriver[] Devices { get { return connectedDevices; } }
        public event EventHandler<CaptureEventArgs>? CaptureCompleted;

        bool capturing = false;
        private int channelCount;
        private int triggerChannel;
        private int preSamples;

        private Action<CaptureEventArgs>? currentCaptureHandler;

        public bool IsCapturing { get { return capturing; } }
        public bool IsNetwork { get { return false; } }

        public string DeviceVersion { get; private set; }
        public AnalyzerDriverType DriverType
        {
            get
            {
                return AnalyzerDriverType.Multi;
            }
        }
        public MultiAnalizerDriver(string[] ConnectionStrings) //First connection string must belong to the master device
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
                foreach(var dev in connectedDevices)
                    dev.CaptureCompleted += Dev_CaptureCompleted;


            } catch(Exception ex) 
            {
                for (int buc = 0; buc < connectedDevices.Length; buc++)
                {
                    if (connectedDevices[buc] != null)
                        connectedDevices[buc].Dispose();
                }

                throw new DeviceConnectionException($"Error connecting to device {ConnectionStrings[pos]}.", ex);
            }

            string? ver = null;

            foreach (var device in connectedDevices)
            {
                var mVer = regVersion.Match(device.DeviceVersion);

                if (mVer == null || !mVer.Success)
                {
                    Dispose();
                    throw new DeviceConnectionException($"Invalid device version ({device.DeviceVersion}) found on device {ConnectionStrings[(int)device.Tag]}");
                }

                if (ver == null)
                {
                    ver = mVer.Groups[1].Value;

                    if (mVer == null || !mVer.Success || !mVer.Groups[2].Success)
                    {
                        Dispose();
                        throw new DeviceConnectionException($"Invalid device version V{(string.IsNullOrWhiteSpace(mVer?.Value) ? "(unknown)" : mVer?.Value)}, minimum supported version: V5_0");
                    }

                    int majorVer = int.Parse(mVer.Groups[2].Value);

                    if (majorVer < 5)
                    {
                        Dispose();
                        throw new DeviceConnectionException($"Invalid device version V{mVer.Value}, minimum supported version: V5_0");
                    }

                }
                else
                {
                    if (ver != mVer.Groups[1].Value)
                    {
                        Dispose();
                        throw new DeviceConnectionException($"Different device versions found. Master version: {ver}, device {ConnectionStrings[(int)device.Tag]} version: {mVer.Groups[1].Value}.");
                    }
                }
            }

            DeviceVersion = $"MULTI_ANALYZER_{ver}";
        }
        public bool SendNetworkConfig(string AccesPointName, string Password, string IPAddress, ushort Port)
        {
            throw new NotSupportedException();
        }
        public CaptureError StartCapture(int Frequency, int PreSamples, int PostSamples, int LoopCount, int[] Channels, int TriggerChannel, bool TriggerInverted, Action<CaptureEventArgs>? CaptureCompletedHandler = null)
        {
            throw new NotSupportedException();
        }
        public CaptureError StartPatternCapture(int Frequency, int PreSamples, int PostSamples, int[] Channels, int TriggerChannel, int TriggerBitCount, UInt16 TriggerPattern, bool Fast, Action<CaptureEventArgs>? CaptureCompletedHandler = null)
        {
            try
            {
                if (capturing)
                    return CaptureError.Busy;

                if (Channels == null ||
                Channels.Length == 0 ||
                Channels.Min() < 0 ||
                TriggerBitCount < 1 ||
                TriggerBitCount > 16 ||
                TriggerChannel < 0 ||
                TriggerChannel > 15 ||
                PreSamples < 2 ||
                PostSamples < 512 ||
                Frequency < 3100 ||
                Frequency > 100000000
                )
                    return CaptureError.BadParams;

                int maxChannel = connectedDevices.Length * 24;

                if (Channels.Max() >= maxChannel)
                    return CaptureError.BadParams;

                int[][] channelsPerDevice = SplitChannelsPerDevice(Channels);

                if (channelsPerDevice.Length > Channels.Length)
                    return CaptureError.BadParams;

                if (channelsPerDevice[0].Length < 1)
                    return CaptureError.BadParams;

                var captureLimits = GetLimits(Channels);

                if (PreSamples > captureLimits.MaxPreSamples || 
                    PostSamples > captureLimits.MaxPostSamples || 
                    PreSamples + PostSamples > captureLimits.MinPreSamples + captureLimits.MaxPostSamples)
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
                    var err = connectedDevices[buc].StartCapture(Frequency, PreSamples + offset, PostSamples - offset, 0, chan, 24, false);

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
        private byte GetCaptureMode(int[] Channels)
        {
            var split = SplitChannelsPerDevice(Channels);
            var maxChannel = split.Select(c => c.DefaultIfEmpty(0).Max()).DefaultIfEmpty(0).Max();
            return (byte)(maxChannel < 8 ? 0 : (maxChannel < 16 ? 1 : 2));
        }
        private int[][] SplitChannelsPerDevice(int[] Channels)
        {
            List<int[]> channelsPerDevice = new List<int[]>();

            for (int buc = 0; buc < connectedDevices.Length; buc++)
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

        public string? GetVoltageStatus()
        {
            return "UNSUPPORTED";
        }

        private void Dev_CaptureCompleted(object? sender, CaptureEventArgs e)
        {
            lock(locker) 
            {
                int idx = (int)((sender as LogicAnalyzerDriver).Tag);

                tempCapture[idx] = e.Samples;
                captureFinished[idx] = true;

                if (captureFinished.All(c => c))
                {
                    UInt128[] finalSamples = new UInt128[tempCapture[idx].Length];

                    for(int buc = 0; buc < finalSamples.Length; buc++) 
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
        public bool StopCapture()
        {
            if(!capturing) 
                return false;

            foreach(var dev in connectedDevices)
                dev.StopCapture();

            capturing = false;

            return true;
        }
        public void Dispose()
        {
            foreach (var dev in connectedDevices)
                dev.Dispose();
        }
    }

    public class DeviceConnectionException : Exception 
    { 
        public DeviceConnectionException(string message) : base(message) { }
        public DeviceConnectionException(string message, Exception innerException) : base(message, innerException) { }
    }
}
