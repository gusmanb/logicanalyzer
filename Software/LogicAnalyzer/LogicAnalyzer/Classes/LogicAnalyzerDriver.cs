using System;
using System.Collections.Generic;
using System.IO.Ports;
using System.Linq;
using System.Runtime.InteropServices;
using System.Text;
using System.Threading.Tasks;

namespace LogicAnalyzer
{
    public class LogicAnalyzerDriver : IDisposable
    {
        StreamReader readResponse;
        BinaryReader readData;
        Stream baseStream;
        SerialPort sp;

        public string? DeviceVersion { get; set; }
        public event EventHandler<CaptureEventArgs> CaptureCompleted;

        bool capturing = false;
        private int channelCount;
        private int triggerChannel;
        private int preSamples;

        public LogicAnalyzerDriver(string SerialPort, int Bauds)
        {
            sp = new SerialPort(SerialPort, Bauds);
            sp.RtsEnable = true;
            sp.DtrEnable = true;
            sp.NewLine = "\n";

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

        public bool StartCapture(int Frequency, int PreSamples, int PostSamples, int[] Channels, int TriggerChannel, bool TriggerInverted)
        {

            if (capturing)
                return false;

            if (Channels == null || Channels.Length == 0 || PreSamples < 2  || PreSamples > (16 * 1024) || (PreSamples + PostSamples) >= (32 * 1024) || Frequency > 100000000)
                return false;

            /*
            bool oneFound = false;

            for (int bitCount = 0; bitCount < 32; bitCount++)
            {
                if (((PreSamples * 4) & (1 << bitCount)) != 0)
                {
                    if (oneFound)
                        return false;

                    oneFound = true;
                }
            }

            if (!oneFound)
                return false;
            */

            channelCount = Channels.Length;
            triggerChannel = Array.IndexOf(Channels, TriggerChannel);
            preSamples = PreSamples;

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

            for(int buc = 0; buc < Channels.Length; buc++)
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
                Task.Run(ReadCapture);
                return true;
            }
            return false;
        }
        public bool StartPatternCapture(int Frequency, int PreSamples, int PostSamples, int[] Channels, int TriggerChannel, int TriggerBitCount, UInt16 TriggerPattern, bool Fast)
        {

            if (capturing)
                return false;

            if (Channels == null || Channels.Length == 0 || PreSamples < 2 || PreSamples > (16 * 1024) || (PreSamples + PostSamples) >= (32 * 1024) || Frequency > 100000000)
                return false;

            /*
            bool oneFound = false;

            for (int bitCount = 0; bitCount < 32; bitCount++)
            {
                if (((PreSamples * 4) & (1 << bitCount)) != 0)
                {
                    if (oneFound)
                        return false;

                    oneFound = true;
                }
            }

            if (!oneFound)
                return false;
            */

            channelCount = Channels.Length;
            triggerChannel = Array.IndexOf(Channels, TriggerChannel);
            preSamples = PreSamples;

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
                Task.Run(ReadCapture);
                return true;
            }
            return false;
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

        void ReadCapture()
        {
            uint length = readData.ReadUInt32();

            uint[] samples = new uint[length]; 

            for(int buc = 0; buc < length; buc++)
                samples[buc] = readData.ReadUInt32();

            if (CaptureCompleted != null)
                CaptureCompleted(this, new CaptureEventArgs { Samples = samples, ChannelCount = channelCount, TriggerChannel = triggerChannel, PreSamples = preSamples });

            capturing = false;
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

                for(int buc = 0; buc < dataBuffer.Count; buc++)
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

    public class CaptureEventArgs : EventArgs
    {
        public int TriggerChannel { get; set; }
        public int ChannelCount { get; set; }
        public int PreSamples { get; set; }
        public uint[] Samples { get; set; }
    }
}
