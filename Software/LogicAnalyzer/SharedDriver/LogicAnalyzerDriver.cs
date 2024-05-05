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
    public class LogicAnalyzerDriver : IDisposable, IAnalizerDriver
    {
        const int MAJOR_VERSION = 5;
        const int MINOR_VERSION = 1;


        Regex regVersion = new Regex(".*?(V([0-9]+)_([0-9]+))$");
        Regex regAddressPort = new Regex("([0-9]+\\.[0-9]+\\.[0-9]+\\.[0-9]+)\\:([0-9]+)");
        StreamReader readResponse;
        BinaryReader readData;
        Stream baseStream;
        SerialPort sp;
        TcpClient tcpClient;
        string devAddr;
        ushort devPort;

        public bool IsCapturing { get { return capturing; } }
        public bool IsNetwork { get { return isNetwork; } }

        public object Tag { get; set; }
        public string? DeviceVersion { get; private set; }
        public int Channels { get { return 24; } }
        public event EventHandler<CaptureEventArgs>? CaptureCompleted;

        bool capturing = false;
        private int channelCount;
        private int triggerChannel;
        private int preSamples;
        private Action<CaptureEventArgs>? currentCaptureHandler;

        bool isNetwork;

        public AnalyzerDriverType DriverType 
        { 
            get 
            { 
                return isNetwork ? 
                    AnalyzerDriverType.Network : 
                    AnalyzerDriverType.Serial; 
            } 
        }

        public LogicAnalyzerDriver (string ConnectionString)
        {
            if(ConnectionString == null) 
                throw new ArgumentNullException(ConnectionString);

            if (ConnectionString.IndexOf(":") != -1)
                InitNetwork(ConnectionString);
            else
                InitSerialPort(ConnectionString, 115200);
        }
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
            DeviceVersion = readResponse.ReadLine();

            if (!ValidateVersion())
            {
                Dispose();
                throw new DeviceConnectionException($"Invalid device version {DeviceVersion}, minimum supported version: V{MAJOR_VERSION}_{MINOR_VERSION}");
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

            if(!ushort.TryParse(port, out devPort))
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
            DeviceVersion = readResponse.ReadLine();
            
            if (!ValidateVersion())
            {
                Dispose();
                throw new DeviceConnectionException($"Invalid device version {DeviceVersion}, minimum supported version: V{MAJOR_VERSION}_{MINOR_VERSION}");
            }
            
            baseStream.ReadTimeout = Timeout.Infinite;
            
            isNetwork = true;
        }

        private bool ValidateVersion()
        {
            var verMatch = regVersion.Match(DeviceVersion ?? "");

            if (verMatch == null || !verMatch.Success || !verMatch.Groups[2].Success)
                return false;

            int majorVer = int.Parse(verMatch.Groups[2].Value);
            int minorVer = int.Parse(verMatch.Groups[3].Value);

            if (majorVer < MAJOR_VERSION)
                return false;

            if (majorVer == MAJOR_VERSION && minorVer < MINOR_VERSION)
                return false;

            return true;
            
        }

        public unsafe bool SendNetworkConfig(string AccesPointName, string Password, string IPAddress, ushort Port)
        {
            if(isNetwork) 
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
        public CaptureError StartCapture(int Frequency, int PreSamples, int PostSamples, int LoopCount, int[] Channels, int TriggerChannel, bool TriggerInverted, Action<CaptureEventArgs>? CaptureCompletedHandler = null)
        {

            if (capturing)
                return CaptureError.Busy;

            if (Channels == null || 
                Channels.Length == 0 || 
                Channels.Min() < 0 ||
                Channels.Max() > 23 ||
                TriggerChannel < 0 ||
                TriggerChannel > 24 ||
                PreSamples < 2 || 
                PostSamples < 512 || 
                Frequency < 3100 || 
                Frequency > 100000000
                )
                return CaptureError.BadParams;

            var captureMode = GetCaptureMode(Channels);

            int requestedSamples = PreSamples + (PostSamples * ((byte)LoopCount + 1));

            try
            {
                switch (captureMode)
                {
                    case 0:

                        if (PreSamples > 98303 || PostSamples > 131069 || requestedSamples > 131071)
                            return CaptureError.BadParams;
                        break;

                    case 1:

                        if (PreSamples > 49151 || PostSamples > 65533 || requestedSamples > 65535)
                            return CaptureError.BadParams;
                        break;

                    case 2:

                        if (PreSamples > 24576 || PostSamples > 32765 || requestedSamples > 32767)
                            return CaptureError.BadParams;
                        break;
                }

                channelCount = Channels.Length;
                triggerChannel = TriggerChannel;
                preSamples = PreSamples;
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
                    captureMode = captureMode
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
        public CaptureError StartPatternCapture(int Frequency, int PreSamples, int PostSamples, int[] Channels, int TriggerChannel, int TriggerBitCount, UInt16 TriggerPattern, bool Fast, Action<CaptureEventArgs>? CaptureCompletedHandler = null)
        {
            try
            {
                if (capturing)
                    return CaptureError.Busy;

                if (Channels == null ||
                Channels.Length == 0 ||
                Channels.Min() < 0 ||
                Channels.Max() > 23 ||
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

                var captureMode = GetCaptureMode(Channels);
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
                    captureMode = captureMode
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

        private byte GetCaptureMode(int[] Channels)
        {
            var maxChannel = Channels.DefaultIfEmpty(0).Max();
            return(byte)(maxChannel < 8 ? 0 : (maxChannel < 16 ? 1 : 2));
        }
        private void ReadCapture(int Samples, byte Mode)
        {
            try
            {
                uint length = readData.ReadUInt32();
                UInt128[] samples = new UInt128[length];

                BinaryReader rdData;

                if (isNetwork)
                    rdData = readData;
                else
                {
                    byte[] readBuffer = new byte[Samples * (Mode == 0 ? 1 : (Mode == 1 ? 2 : 4))];
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
                    case 0:
                        for (int buc = 0; buc < length; buc++)
                            samples[buc] = rdData.ReadByte();
                        break;
                    case 1:
                        for (int buc = 0; buc < length; buc++)
                            samples[buc] = rdData.ReadUInt16();
                        break;
                    case 2:
                        for (int buc = 0; buc < length; buc++)
                            samples[buc] = rdData.ReadUInt32();
                        break;
                }

                if (currentCaptureHandler != null)
                    currentCaptureHandler(new CaptureEventArgs { SourceType = isNetwork ? AnalyzerDriverType.Network : AnalyzerDriverType.Serial, Samples = samples, ChannelCount = channelCount, TriggerChannel = triggerChannel, PreSamples = preSamples });
                else if (CaptureCompleted != null)
                    CaptureCompleted(this, new CaptureEventArgs { SourceType = isNetwork ? AnalyzerDriverType.Network : AnalyzerDriverType.Serial, Samples = samples, ChannelCount = channelCount, TriggerChannel = triggerChannel, PreSamples = preSamples });

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
                //if(ex.GetType() != typeof(OperationCanceledException))
                //    Console.WriteLine(ex.Message + " - " + ex.StackTrace);

                if (currentCaptureHandler != null)
                    currentCaptureHandler(new CaptureEventArgs { SourceType = isNetwork ? AnalyzerDriverType.Network : AnalyzerDriverType.Serial, Samples = null, ChannelCount = channelCount, TriggerChannel = triggerChannel, PreSamples = preSamples });
                else if (CaptureCompleted != null)
                    CaptureCompleted(this, new CaptureEventArgs { SourceType = isNetwork ? AnalyzerDriverType.Network : AnalyzerDriverType.Serial, Samples = null, ChannelCount = channelCount, TriggerChannel = triggerChannel, PreSamples = preSamples });
            }
        }
        public bool StopCapture()
        {
            if (!capturing)
                return false;

            capturing = false;

            if (isNetwork)
            {
                baseStream.WriteByte(0xff);
                baseStream.Flush();
                Thread.Sleep(2000);
                tcpClient.Close();
                Thread.Sleep(1);
                tcpClient = new TcpClient();
                tcpClient.Connect(devAddr, devPort);
                baseStream = tcpClient.GetStream();
                readResponse = new StreamReader(baseStream);
                readData = new BinaryReader(baseStream);
            }
            else
            {

                sp.Write(new byte[] { 0xFF }, 0, 1);
                sp.BaseStream.Flush();
                Thread.Sleep(2000);
                sp.Close();
                Thread.Sleep(1);
                sp.Open();
                baseStream = sp.BaseStream;
                readResponse = new StreamReader(baseStream);
                readData = new BinaryReader(baseStream);
            }

            return true;
        }

        public CaptureLimits GetLimits(int[] Channels)
        {
            var mode = GetCaptureMode(Channels);
            return CaptureModes.Modes[mode];
        }

        public string? GetVoltageStatus() 
        {
            if (!isNetwork)
                return "UNSUPPORTED";

            OutputPacket pack = new OutputPacket();
            pack.AddByte(3);

            baseStream.Write(pack.Serialize());
            baseStream.Flush();

            baseStream.ReadTimeout = Timeout.Infinite;
            var result = readResponse.ReadLine();
            baseStream.ReadTimeout = Timeout.Infinite;

            return result;
        }

        public void Dispose()
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

            } catch { }

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
      
        class OutputPacket
        {
            List<byte> dataBuffer = new List<byte>();

            public void AddByte(byte newByte)
            {
                dataBuffer.Add(newByte);
            }

            public void AddBytes(IEnumerable<byte> newBytes)
            {
                dataBuffer.AddRange(newBytes);
            }

            public void AddString(string newString)
            {
                dataBuffer.AddRange(Encoding.ASCII.GetBytes(newString));
            }

            public void AddStruct(object newStruct)
            {
                int rawSize = Marshal.SizeOf(newStruct);
                IntPtr buffer = Marshal.AllocHGlobal(rawSize);
                Marshal.StructureToPtr(newStruct, buffer, false);
                byte[] rawDatas = new byte[rawSize];
                Marshal.Copy(buffer, rawDatas, 0, rawSize);
                Marshal.FreeHGlobal(buffer);
                dataBuffer.AddRange(rawDatas);
            }

            public void Clear()
            {
                dataBuffer.Clear();
            }

            public byte[] Serialize()
            {
                List<byte> finalData = new List<byte>();
                finalData.Add(0x55);
                finalData.Add(0xAA);

                for (int buc = 0; buc < dataBuffer.Count; buc++)
                {
                    if (dataBuffer[buc] == 0xAA || dataBuffer[buc] == 0x55 || dataBuffer[buc] == 0xF0)
                    {
                        finalData.Add(0xF0);
                        finalData.Add((byte)(dataBuffer[buc] ^ 0xF0));
                    }
                    else
                        finalData.Add(dataBuffer[buc]);
                }


                finalData.Add(0xAA);
                finalData.Add(0x55);

                return finalData.ToArray();

            }
        }

        [StructLayout(LayoutKind.Sequential)]
        struct CaptureRequest
        {
            public byte triggerType;
            public byte trigger;
            public byte invertedOrCount;
            public UInt16 triggerValue;
            [MarshalAs(UnmanagedType.ByValArray, SizeConst = 24)]
            public byte[] channels;
            public byte channelCount;
            public UInt32 frequency;
            public UInt32 preSamples;
            public UInt32 postSamples;
            public byte loopCount;
            public byte captureMode;
        }

        [StructLayout(LayoutKind.Sequential)]
        unsafe struct NetConfig
        {
            public fixed byte AccessPointName[33];
            public fixed byte Password[64];
            public fixed byte IPAddress[16];
            public UInt16 Port;
        }     
    }
}