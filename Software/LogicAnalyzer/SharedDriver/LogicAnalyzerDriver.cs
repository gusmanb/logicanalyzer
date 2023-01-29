using System.IO.Ports;
using System.Runtime.InteropServices;
using System.Text;

namespace SharedDriver
{
    public class LogicAnalyzerDriver : IDisposable
    {
        StreamReader readResponse;
        BinaryReader readData;
        Stream baseStream;
        SerialPort sp;

        public string? DeviceVersion { get; set; }
        public event EventHandler<CaptureEventArgs>? CaptureCompleted;

        bool capturing = false;
        private int channelCount;
        private int triggerChannel;
        private int preSamples;
        private Action<CaptureEventArgs>? currentCaptureHandler;

        public LogicAnalyzerDriver(string SerialPort, int Bauds)
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
            baseStream.ReadTimeout = Timeout.Infinite;
        }

        public CaptureError StartCapture(int Frequency, int PreSamples, int PostSamples, int[] Channels, int TriggerChannel, bool TriggerInverted, Action<CaptureEventArgs>? CaptureCompletedHandler = null)
        {

            if (capturing)
                return CaptureError.Busy;

            if (Channels == null || Channels.Length == 0 || PreSamples < 2 || PreSamples > (30 * 1024 - 1) || PostSamples < 512 || (PreSamples + PostSamples) >= (32 * 1024) || Frequency < 3100 || Frequency > 100000000)
                return CaptureError.BadParams;

            channelCount = Channels.Length;
            triggerChannel = Array.IndexOf(Channels, TriggerChannel);
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
                postSamples = (uint)PostSamples
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
                Task.Run(() => ReadCapture(PreSamples + PostSamples));
                return CaptureError.None;
            }
            return CaptureError.HardwareError;
        }
        public CaptureError StartPatternCapture(int Frequency, int PreSamples, int PostSamples, int[] Channels, int TriggerChannel, int TriggerBitCount, UInt16 TriggerPattern, bool Fast, Action<CaptureEventArgs>? CaptureCompletedHandler = null)
        {

            if (capturing)
                return CaptureError.Busy;

            if (Channels == null || Channels.Length == 0 || PreSamples < 2 || PreSamples > (30 * 1024 - 1) || PostSamples < 512 || (PreSamples + PostSamples) >= (32 * 1024) || Frequency < 3100 || Frequency > 100000000)
                return CaptureError.BadParams;

            channelCount = Channels.Length;
            triggerChannel = Array.IndexOf(Channels, TriggerChannel);
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
                preSamples = (uint)PreSamples,
                postSamples = (uint)PostSamples
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
                Task.Run(() => ReadCapture(PreSamples + PostSamples));
                return CaptureError.None;
            }
            return CaptureError.HardwareError;
        }

        public bool StopCapture()
        {
            if (!capturing)
                return false;

            capturing = false;

            sp.Write(new byte[] { 0xFF }, 0, 1);
            sp.BaseStream.Flush();
            Thread.Sleep(1);
            sp.Close();
            Thread.Sleep(1);
            sp.Open();
            baseStream = sp.BaseStream;
            readResponse = new StreamReader(baseStream);
            readData = new BinaryReader(baseStream);

            return true;
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

            DeviceVersion = null;
            CaptureCompleted = null;
        }
        void ReadCapture(int Samples)
        {

            try
            {

                byte[] readBuffer = new byte[Samples * 4 + 4];

                int left = readBuffer.Length;
                int pos = 0;

                while (left > 0 && sp.IsOpen)
                { 
                    pos += sp.Read(readBuffer, pos, left);
                    left = readBuffer.Length - pos;
                }
                
                uint[] samples;
                
                using (MemoryStream ms = new MemoryStream(readBuffer))
                {
                    using (BinaryReader br = new BinaryReader(ms))
                    {
                        uint length = br.ReadUInt32();
                        samples = new uint[length];
                        for (int buc = 0; buc < length; buc++)
                            samples[buc] = br.ReadUInt32();
                    }
                }

                if (currentCaptureHandler != null)
                    currentCaptureHandler(new CaptureEventArgs { Samples = samples, ChannelCount = channelCount, TriggerChannel = triggerChannel, PreSamples = preSamples });
                else if (CaptureCompleted != null)
                    CaptureCompleted(this, new CaptureEventArgs { Samples = samples, ChannelCount = channelCount, TriggerChannel = triggerChannel, PreSamples = preSamples });

                capturing = false;
            }
            catch(Exception ex) 
            {
                Console.WriteLine(ex.Message + " - " + ex.StackTrace);
            }
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
        }

    }

    public enum CaptureError
    { 
        None,
        Busy,
        BadParams,
        HardwareError
    }

    public class CaptureEventArgs : EventArgs
    {
        public int TriggerChannel { get; set; }
        public int ChannelCount { get; set; }
        public int PreSamples { get; set; }
        public uint[] Samples { get; set; }
    }
}