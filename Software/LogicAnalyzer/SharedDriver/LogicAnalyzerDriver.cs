using System.Diagnostics;
using System.IO.Ports;
using System.Net;
using System.Net.Http;
using System.Net.Sockets;
using System.Runtime.CompilerServices;
using System.Runtime.InteropServices;
using System.Text;
using System.Text.RegularExpressions;

namespace SharedDriver
{

    public class LogicAnalyzerDriver : AnalyzerDriverBase
    {
        #region Constants and static vars

        static Regex regAddressPort = new Regex("([0-9]+\\.[0-9]+\\.[0-9]+\\.[0-9]+)\\:([0-9]+)");
        static Regex regChan = new Regex("^CHANNELS:([0-9]+)$");
        static Regex regBuf = new Regex("^BUFFER:([0-9]+)$");
        static Regex regFreq = new Regex("^FREQ:([0-9]+)$");
        #endregion

        #region Properties
        public override bool IsCapturing { get { return capturing; } }
        public override bool IsNetwork { get { return isNetwork; } }
        public override string? DeviceVersion { get { return version; } }
        public override int ChannelCount { get { return channelCount; } }
        public override int MaxFrequency { get { return maxFrequency; } }
        public override int BufferSize { get { return bufferSize; } }
        public override AnalyzerDriverType DriverType
        {
            get
            {
                return isNetwork ?
                    AnalyzerDriverType.Network :
                    AnalyzerDriverType.Serial;
            }
        }
        #endregion

        #region Events
        public override event EventHandler<CaptureEventArgs>? CaptureCompleted;
        #endregion

        #region Variables
        //General data
        bool capturing = false;
        bool isNetwork;
        string? version;
        int channelCount;
        int maxFrequency;
        int bufferSize;
        string? devAddr;
        ushort devPort;

        //Current capture data
        private int captureChannels;
        private int triggerChannel;
        private int preSamples;
        private int postSamples;
        private int loopCount;
        private bool measure;
        private int frequency;

        //Comms variables
        StreamReader? readResponse;
        BinaryReader? readData;
        Stream? baseStream;
        SerialPort? sp;
        TcpClient? tcpClient;
        
        //Optional callback
        private Action<CaptureEventArgs>? currentCaptureHandler;
        #endregion

        public LogicAnalyzerDriver(string ConnectionString)
        {
            if (ConnectionString == null)
                throw new ArgumentNullException(ConnectionString);

            if (ConnectionString.IndexOf(":") != -1)
                InitNetwork(ConnectionString);
            else
                InitSerialPort(ConnectionString, 115200);
        }

        #region Initialization code

        private void InitSerialPort(string SerialPort, int Bauds)
        {
            sp = new SerialPort(SerialPort, Bauds);
            sp.RtsEnable = true;
            sp.DtrEnable = true;
            sp.NewLine = "\n";
            sp.ReadBufferSize = 1024 * 1024;
            sp.WriteBufferSize = 1024 * 1024;

            sp.Open();
            baseStream = sp.BaseStream;

            readResponse = new StreamReader(baseStream);
            readData = new BinaryReader(baseStream);

            OutputPacket pack = new OutputPacket();
            pack.AddByte(0);

            baseStream.Write(pack.Serialize());

            baseStream.ReadTimeout = 10000;
            version = readResponse.ReadLine();

            var devVersion = VersionValidator.GetVersion(version);

            if (!devVersion.IsValid)
            {
                Dispose();
                throw new DeviceConnectionException($"Invalid device version {DeviceVersion}, minimum supported version: V{VersionValidator.MAJOR_VERSION}_{VersionValidator.MINOR_VERSION}");
            }

            var freq = readResponse.ReadLine();
            if (!GetFrequency(freq))
            {
                Dispose();
                throw new DeviceConnectionException("Invalid device frequency response.");
            }

            var bufString = readResponse.ReadLine();
            if (!GetBufferSize(bufString))
            {
                Dispose();
                throw new DeviceConnectionException("Invalid device buffer size response.");
            }

            var chanString = readResponse.ReadLine();
            if (!GetChannelCount(chanString))
            {
                Dispose();
                throw new DeviceConnectionException("Invalid device channel count response.");
            }

            baseStream.ReadTimeout = Timeout.Infinite;
        }
        private void InitNetwork(string AddressPort)
        {
            var match = regAddressPort.Match(AddressPort);

            if (match == null || !match.Success)
                throw new ArgumentException("Specified address/port is invalid");

            devAddr = match.Groups[1].Value;
            string port = match.Groups[2].Value;

            if (!ushort.TryParse(port, out devPort))
                throw new ArgumentException("Specified address/port is invalid");

            tcpClient = new TcpClient();

            tcpClient.Connect(devAddr, devPort);
            baseStream = tcpClient.GetStream();

            readResponse = new StreamReader(baseStream);
            readData = new BinaryReader(baseStream);

            OutputPacket pack = new OutputPacket();
            pack.AddByte(0);

            baseStream.Write(pack.Serialize());

            baseStream.ReadTimeout = 10000;
            version = readResponse.ReadLine();

            var devVersion = VersionValidator.GetVersion(version);

            if (!devVersion.IsValid)
            {
                Dispose();
                throw new DeviceConnectionException($"Invalid device version {DeviceVersion}, minimum supported version: V{VersionValidator.MAJOR_VERSION}_{VersionValidator.MINOR_VERSION}");
            }

            var freq = readResponse.ReadLine();
            if (!GetFrequency(freq))
            {
                Dispose();
                throw new DeviceConnectionException("Invalid device frequency response.");
            }

            var bufString = readResponse.ReadLine();
            if (!GetBufferSize(bufString))
            {
                Dispose();
                throw new DeviceConnectionException("Invalid device buffer size response.");
            }

            var chanString = readResponse.ReadLine();
            if (!GetChannelCount(chanString))
            {
                Dispose();
                throw new DeviceConnectionException("Invalid device channel count response.");
            }

            baseStream.ReadTimeout = Timeout.Infinite;

            isNetwork = true;
        }
        private bool GetChannelCount(string? chanString)
        {

            var match = regChan.Match(chanString ?? "");
            if (!match.Success || !match.Groups[1].Success)
                return false;

            var chanStr = match.Groups[1].Value;
            if (!int.TryParse(chanStr, out int chanVal))
                return false;

            channelCount = chanVal;
            return true;
        }
        private bool GetBufferSize(string? bufString)
        {

            var match = regBuf.Match(bufString ?? "");
            if (!match.Success || !match.Groups[1].Success)
                return false;

            var bufStr = match.Groups[1].Value;
            if (!int.TryParse(bufStr, out int bufVal))
                return false;

            bufferSize = bufVal;
            return true;
        }
        private bool GetFrequency(string? freq)
        {

            var match = regFreq.Match(freq ?? "");
            if (!match.Success || !match.Groups[1].Success)
                return false;

            var freqStr = match.Groups[1].Value;
            if (!int.TryParse(freqStr, out int freqVal))
                return false;

            maxFrequency = freqVal;
            return true;
        }

        #endregion

        #region Capture code

        public override CaptureError StartCapture(int Frequency, int PreSamples, int PostSamples, int LoopCount, bool MeasureBursts, int[] Channels, int TriggerChannel, bool TriggerInverted, Action<CaptureEventArgs>? CaptureCompletedHandler = null)
        {

            try
            {
                if (capturing || baseStream == null || readResponse == null)
                    return CaptureError.Busy;

                if (Channels == null || Channels.Length < 0)
                    return CaptureError.BadParams;

                int requestedSamples = PreSamples + (PostSamples * ((byte)LoopCount + 1));

                var captureLimits = GetLimits(Channels);
                var captureMode = GetCaptureMode(Channels);

                if (
                Channels.Min() < captureLimits.MinChannel ||
                Channels.Max() > captureLimits.MaxChannel ||
                TriggerChannel < 0 ||
                TriggerChannel > captureLimits.MaxChannel + 1 || //MaxChannel + 1 = ext trigger
                PreSamples < captureLimits.MinPreSamples ||
                PostSamples < captureLimits.MinPostSamples ||
                PreSamples > captureLimits.MaxPreSamples ||
                PostSamples > captureLimits.MaxPreSamples ||
                requestedSamples > captureLimits.MaxTotalSamples ||
                Frequency < captureLimits.MinFrequency ||
                Frequency > captureLimits.MaxFrequency ||
                    LoopCount > 254
                )
                    return CaptureError.BadParams;


                captureChannels = Channels.Length;
                triggerChannel = TriggerChannel;
                preSamples = PreSamples;
                postSamples = PostSamples;
                loopCount = LoopCount;
                measure = MeasureBursts;
                frequency = Frequency;

                currentCaptureHandler = CaptureCompletedHandler;

                CaptureRequest request = new CaptureRequest
                {
                    triggerType = 0,
                    trigger = (byte)TriggerChannel,
                    invertedOrCount = TriggerInverted ? (byte)1 : (byte)0,
                    channels = new byte[32],
                    channelCount = (byte)Channels.Length,
                    frequency = (uint)Frequency,
                    preSamples = (uint)PreSamples,
                    postSamples = (uint)PostSamples,
                    loopCount = (byte)LoopCount,
                    measure = MeasureBursts ? (byte)1 : (byte)0,
                    captureMode = (byte)captureMode
                };

                for (int buc = 0; buc < Channels.Length; buc++)
                    request.channels[buc] = (byte)Channels[buc];

                OutputPacket pack = new OutputPacket();
                pack.AddByte(1);
                pack.AddStruct(request);

                baseStream.Write(pack.Serialize());
                baseStream.Flush();

                baseStream.ReadTimeout = 10000;
                var result = readResponse.ReadLine();
                baseStream.ReadTimeout = Timeout.Infinite;

                if (result == "CAPTURE_STARTED")
                {
                    capturing = true;
                    Task.Run(() => ReadCapture(requestedSamples, captureMode));
                    return CaptureError.None;
                }
                return CaptureError.HardwareError;
            }
            catch { return CaptureError.UnexpectedError; }
        }
        public override CaptureError StartPatternCapture(int Frequency, int PreSamples, int PostSamples, int[] Channels, int TriggerChannel, int TriggerBitCount, UInt16 TriggerPattern, bool Fast, Action<CaptureEventArgs>? CaptureCompletedHandler = null)
        {
            try
            {
                if (capturing || baseStream == null || readResponse == null)
                    return CaptureError.Busy;

                if (Channels == null || Channels.Length < 0)
                    return CaptureError.BadParams;

                var captureLimits = GetLimits(Channels);
                var captureMode = GetCaptureMode(Channels);

                if (
                Channels.Min() < captureLimits.MinChannel ||
                Channels.Max() > captureLimits.MaxChannel ||
                TriggerBitCount < 1 ||
                TriggerBitCount > 16 ||
                TriggerChannel < 0 ||
                TriggerChannel > 15 ||
                PreSamples < captureLimits.MinPreSamples ||
                PostSamples < captureLimits.MinPostSamples ||
                PreSamples > captureLimits.MaxPreSamples ||
                PostSamples > captureLimits.MaxPreSamples ||
                PreSamples + PostSamples > captureLimits.MaxTotalSamples ||
                Frequency < captureLimits.MinFrequency ||
                Frequency > captureLimits.MaxFrequency
                )
                    return CaptureError.BadParams;



                double samplePeriod = 1000000000.0 / Frequency;
                double delay = Fast ? TriggerDelays.FastTriggerDelay : TriggerDelays.ComplexTriggerDelay;
                int offset = (int)(Math.Round((delay / samplePeriod) + 0.3, 0));

                captureChannels = Channels.Length;
                triggerChannel = TriggerChannel;
                preSamples = PreSamples;
                currentCaptureHandler = CaptureCompletedHandler;
                loopCount = 0;
                measure = false;

                CaptureRequest request = new CaptureRequest
                {
                    triggerType = (byte)(Fast ? 2 : 1),
                    trigger = (byte)TriggerChannel,
                    invertedOrCount = (byte)TriggerBitCount,
                    triggerValue = (UInt16)TriggerPattern,
                    channels = new byte[32],
                    channelCount = (byte)Channels.Length,
                    frequency = (uint)Frequency,
                    preSamples = (uint)(PreSamples + offset),
                    postSamples = (uint)(PostSamples - offset),
                    captureMode = (byte)captureMode
                };

                for (int buc = 0; buc < Channels.Length; buc++)
                    request.channels[buc] = (byte)Channels[buc];

                OutputPacket pack = new OutputPacket();
                pack.AddByte(1);
                pack.AddStruct(request);

                baseStream.Write(pack.Serialize());
                baseStream.Flush();

                baseStream.ReadTimeout = 10000;
                var result = readResponse.ReadLine();
                baseStream.ReadTimeout = Timeout.Infinite;

                if (result == "CAPTURE_STARTED")
                {
                    capturing = true;
                    Task.Run(() => ReadCapture(PreSamples + PostSamples, captureMode));
                    return CaptureError.None;
                }
                return CaptureError.HardwareError;
            }
            catch { return CaptureError.UnexpectedError; }
        }

        private void ReadCapture(int Samples, CaptureMode Mode)
        {
            try
            {
                if (readData == null)
                    throw new Exception("No data reader available");

                uint length = readData.ReadUInt32();
                UInt128[] samples = new UInt128[length];
                UInt64[] timestamps = new UInt64[loopCount == 0 || !measure ? 0 : loopCount + 2];

                BinaryReader rdData;

                if (isNetwork)
                    rdData = readData;
                else
                {
                    int bufLen = Samples * (Mode == CaptureMode.Channels_8 ? 1 : (Mode == CaptureMode.Channels_16 ? 2 : 4));

                    if (loopCount == 0 || !measure)
                        bufLen += 1;
                    else
                        bufLen += 1 + (loopCount + 2) * 4;

                    byte[] readBuffer = new byte[bufLen];
                    int left = readBuffer.Length;
                    int pos = 0;

                    while (left > 0 && sp.IsOpen)
                    {
                        pos += sp.Read(readBuffer, pos, left);
                        left = readBuffer.Length - pos;
                    }

                    MemoryStream ms = new MemoryStream(readBuffer);
                    rdData = new BinaryReader(ms);
                }

                switch (Mode)
                {
                    case CaptureMode.Channels_8:
                        for (int buc = 0; buc < length; buc++)
                            samples[buc] = rdData.ReadByte();
                        break;
                    case CaptureMode.Channels_16:
                        for (int buc = 0; buc < length; buc++)
                            samples[buc] = rdData.ReadUInt16();
                        break;
                    case CaptureMode.Channels_24:
                        for (int buc = 0; buc < length; buc++)
                            samples[buc] = rdData.ReadUInt32();
                        break;
                }

                byte stampLength = rdData.ReadByte();

                if (stampLength > 0)
                {
                    for (int buc = 0; buc < loopCount + 2; buc++)
                        timestamps[buc] = rdData.ReadUInt32();
                }

                List<BurstInfo> bursts = new List<BurstInfo>();

                //If there are timestamps, we need to adjust them, there can be a jitter up to 1us caused
                //by the device, so we need to adjust the timestamps to be more accurate
                if (timestamps.Length > 0)
                {
                    //First we invert the lower part of the timestamps as systick counts in decreasing order
                    for (int buc = 0; buc < timestamps.Length; buc++)
                    {
                        Debug.WriteLine(timestamps[buc].ToString("X8"));
                        UInt64 tt = timestamps[buc];
                        tt = (tt & 0xFF000000) | (0x00FFFFFF - (tt & 0x00FFFFFF));
                        timestamps[buc] = tt;
                    }

                    //Next we calculate the ns per sample and the ns per burst
                    double nsPerSample = 1000000000.0 / frequency;
                    double ticksPerSample = nsPerSample / 5;
                    double nsPerBurst = nsPerSample * postSamples;

                    //We calculate the ticks per burst, as we know the device's CPU runs at 200Mhz we know that each
                    //tick is 5ns, so we can determine how many ticks happen per burst
                    double ticksPerBurst = nsPerBurst / 5;

                    for (int buc = 1; buc < timestamps.Length; buc++)
                    {

                        //In case of rollback, we need to adjust the timestamps
                        ulong top = timestamps[buc] < timestamps[buc - 1] ? timestamps[buc] + 0xFFFFFFFF : timestamps[buc];

                        //If the difference between the timestamps is less than the ticks per burst, we adjust the timestamps
                        if (top - timestamps[buc - 1] <= ticksPerBurst)
                        {
                            Debug.WriteLine($"Adjusting timestamp {buc}");
                            uint diff = (uint)(ticksPerBurst - (top - timestamps[buc - 1]) + (ticksPerSample * 2));

                            for (int buc2 = buc; buc2 < timestamps.Length; buc2++)
                                timestamps[buc2] += (uint)diff;
                        }
                    }

                    //Finally we calculate the delays between each burst.
                    //First timestamp is a sync timestamp, second timestamp is the end of the initial burst
                    //so they are discarded
                    var delays = new UInt64[timestamps.Length - 2];

                    for (int buc = 2; buc < timestamps.Length; buc++)
                    {
                        //In case of rollback, we need to adjust the timestamps
                        ulong top = timestamps[buc] < timestamps[buc - 1] ? timestamps[buc] + 0xFFFFFFFF : timestamps[buc];
                        delays[buc - 2] = (UInt64)((top - timestamps[buc - 1]) - ticksPerBurst) * 5;
                        Debug.WriteLine(delays[buc - 2]);
                    }

                    for (int buc = 1; buc < timestamps.Length; buc++)
                    {
                        if (buc == 1)
                        {
                            BurstInfo burst = new BurstInfo
                            {
                                BurstSampleStart = preSamples,
                                BurstSampleEnd = preSamples + postSamples,
                                BurstSampleGap = 0,
                                BurstTimeGap = 0
                            };

                            bursts.Add(burst);
                        }
                        else
                        {
                            BurstInfo burst = new BurstInfo
                            {
                                BurstSampleStart = preSamples + (postSamples * (buc - 1)),
                                BurstSampleEnd = preSamples + (postSamples * buc),
                                BurstSampleGap = (ulong)(delays[buc - 2] / nsPerSample),
                                BurstTimeGap = (ulong)(delays[buc - 2])
                            };

                            bursts.Add(burst);
                        }
                    }
                    //timestamps = delays;
                }

                if (currentCaptureHandler != null)
                    currentCaptureHandler(new CaptureEventArgs { SourceType = isNetwork ? AnalyzerDriverType.Network : AnalyzerDriverType.Serial, Samples = samples, ChannelCount = captureChannels, TriggerChannel = triggerChannel, PreSamples = preSamples, LoopCount = loopCount, Bursts = bursts.ToArray() });
                else if (CaptureCompleted != null)
                    CaptureCompleted(this, new CaptureEventArgs { SourceType = isNetwork ? AnalyzerDriverType.Network : AnalyzerDriverType.Serial, Samples = samples, ChannelCount = captureChannels, TriggerChannel = triggerChannel, PreSamples = preSamples, LoopCount = loopCount, Bursts = bursts.ToArray() });

                if (!isNetwork)
                {
                    try
                    {
                        rdData.BaseStream.Close();
                        rdData.BaseStream.Dispose();
                    }
                    catch { }

                    try
                    {
                        rdData.Close();
                        rdData.Dispose();
                    }
                    catch { }
                }
                capturing = false;
            }
            catch (Exception ex)
            {
                if (currentCaptureHandler != null)
                    currentCaptureHandler(new CaptureEventArgs { SourceType = isNetwork ? AnalyzerDriverType.Network : AnalyzerDriverType.Serial, Samples = null, ChannelCount = captureChannels, TriggerChannel = triggerChannel, PreSamples = preSamples });
                else if (CaptureCompleted != null)
                    CaptureCompleted(this, new CaptureEventArgs { SourceType = isNetwork ? AnalyzerDriverType.Network : AnalyzerDriverType.Serial, Samples = null, ChannelCount = captureChannels, TriggerChannel = triggerChannel, PreSamples = preSamples });
            }
        }

        public override bool StopCapture()
        {
            if (!capturing)
                return false;

            capturing = false;

            try
            {
                if (isNetwork)
                {
                    baseStream?.WriteByte(0xff);
                    baseStream?.Flush();
                    Thread.Sleep(2000);
                    tcpClient?.Close();
                    Thread.Sleep(1);
                    tcpClient = new TcpClient();
                    tcpClient.Connect(devAddr, devPort);
                    baseStream = tcpClient.GetStream();
                    readResponse = new StreamReader(baseStream);
                    readData = new BinaryReader(baseStream);
                }
                else
                {

                    sp?.Write(new byte[] { 0xFF }, 0, 1);
                    sp?.BaseStream.Flush();
                    Thread.Sleep(2000);
                    sp?.Close();
                    Thread.Sleep(1);
                    sp?.Open();
                    baseStream = sp?.BaseStream;
                    readResponse = new StreamReader(baseStream);
                    readData = new BinaryReader(baseStream);
                }
            }
            catch { }

            return true;
        }

        #endregion

        #region Network-related functions
        public override unsafe bool SendNetworkConfig(string AccesPointName, string Password, string IPAddress, ushort Port)
        {
            if (isNetwork || baseStream == null || readResponse == null)
                return false;

            NetConfig request = new NetConfig { Port = Port };
            byte[] name = Encoding.ASCII.GetBytes(AccesPointName);
            byte[] pass = Encoding.ASCII.GetBytes(Password);
            byte[] addr = Encoding.ASCII.GetBytes(IPAddress);

            Marshal.Copy(name, 0, new IntPtr(request.AccessPointName), name.Length);
            Marshal.Copy(pass, 0, new IntPtr(request.Password), pass.Length);
            Marshal.Copy(addr, 0, new IntPtr(request.IPAddress), addr.Length);

            OutputPacket pack = new OutputPacket();
            pack.AddByte(2);
            pack.AddStruct(request);

            baseStream.Write(pack.Serialize());
            baseStream.Flush();

            baseStream.ReadTimeout = 5000;
            var result = readResponse.ReadLine();
            baseStream.ReadTimeout = Timeout.Infinite;

            if (result == "SETTINGS_SAVED")
                return true;

            return false;
        }
        public override string? GetVoltageStatus()
        {
            if (!isNetwork)
                return "UNSUPPORTED";

            if(baseStream == null || readResponse == null)
                return "DISCONNECTED";

            OutputPacket pack = new OutputPacket();
            pack.AddByte(3);

            baseStream.Write(pack.Serialize());
            baseStream.Flush();

            baseStream.ReadTimeout = Timeout.Infinite;
            var result = readResponse.ReadLine();
            baseStream.ReadTimeout = Timeout.Infinite;

            return result;
        }
        #endregion

        #region IDisposable implementation
        public override void Dispose()
        {
            try
            {
                sp.Close();
                sp.Dispose();
            }
            catch { }

            try
            {
                tcpClient.Close();
                tcpClient.Dispose();

            }
            catch { }

            try
            {
                baseStream.Close();
                baseStream.Dispose();
            }
            catch { }

            try
            {
                readData.Close();
                readData.Dispose();
            }
            catch { }

            try
            {
                readResponse.Close();
                readResponse.Dispose();
            }
            catch { }

            sp = null;
            baseStream = null;
            readData = null;
            readData = null;

            CaptureCompleted = null;
        }
        #endregion
    }
}