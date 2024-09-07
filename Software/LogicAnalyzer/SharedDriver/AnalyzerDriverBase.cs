using System;
using System.Collections.Generic;
using System.Linq;
using System.Runtime.InteropServices;
using System.Text;
using System.Threading.Tasks;

namespace SharedDriver
{
    public abstract class AnalyzerDriverBase : IDisposable
    {
        #region Public Properties
        public abstract string? DeviceVersion { get; }
        public abstract int MaxFrequency { get; }
        public virtual int MinFrequency { get { return (MaxFrequency * 2) / 65535; } }
        public abstract int ChannelCount { get; }
        public abstract int BufferSize { get; }
        public abstract AnalyzerDriverType DriverType { get; }
        public abstract bool IsNetwork { get; }
        public abstract bool IsCapturing { get; }
        public object? Tag { get; set; }
        #endregion

        #region Events
        public abstract event EventHandler<CaptureEventArgs>? CaptureCompleted;
        #endregion

        #region Capture Methods
        public abstract CaptureError StartCapture(int Frequency, int PreSamples, int PostSamples, int LoopCount, bool Measure, int[] Channels, int TriggerChannel, bool TriggerInverted, Action<CaptureEventArgs>? CaptureCompletedHandler = null);
        public abstract CaptureError StartPatternCapture(int Frequency, int PreSamples, int PostSamples, int[] Channels, int TriggerChannel, int TriggerBitCount, UInt16 TriggerPattern, bool Fast, Action<CaptureEventArgs>? CaptureCompletedHandler = null);
        public abstract bool StopCapture();
        #endregion

        #region Device info
        public virtual CaptureMode GetCaptureMode(int[] Channels)
        {
            var maxChannel = Channels.DefaultIfEmpty(0).Max();
            return maxChannel < 8 ? CaptureMode.Channels_8 : (maxChannel < 16 ? CaptureMode.Channels_16 : CaptureMode.Channels_24);
        }
        public virtual CaptureLimits GetLimits(int[] Channels)
        {
            var mode = GetCaptureMode(Channels);

            int totalSamples = BufferSize / (mode == CaptureMode.Channels_8 ? 1 : (mode == CaptureMode.Channels_16 ? 2 : 4));

            var limits = new CaptureLimits
            {
                MinPreSamples = 2,
                MaxPreSamples = totalSamples / 10,
                MinPostSamples = 2,
                MaxPostSamples = totalSamples - 2,
            };

            return limits;
        }

        public virtual AnalyzerDeviceInfo GetDeviceInfo()
        {
            List<CaptureLimits> limits = new List<CaptureLimits>();

            limits.Add(GetLimits(Enumerable.Range(0,7).ToArray()));
            limits.Add(GetLimits(Enumerable.Range(0, 15).ToArray()));
            limits.Add(GetLimits(Enumerable.Range(0, 23).ToArray()));

            return new AnalyzerDeviceInfo
            {
                Name = DeviceVersion ?? "Unknown",
                MaxFrequency = MaxFrequency,
                Channels = ChannelCount,
                BufferSize = BufferSize,
                ModeLimits = limits.ToArray()
            };
        }

        #endregion

        #region Network Methods
        public virtual string? GetVoltageStatus()
        {
            return "UNSUPPORTED";
        }
        public virtual bool SendNetworkConfig(string AccesPointName, string Password, string IPAddress, ushort Port)
        {
            return false;
        }
        #endregion

        #region IDisposable Implementation
        public virtual void Dispose()
        {
        }
        #endregion

        #region Protected types
        protected class OutputPacket
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
        protected struct CaptureRequest
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
            public byte measure;
            public byte captureMode;
        }

        [StructLayout(LayoutKind.Sequential)]
        protected unsafe struct NetConfig
        {
            public fixed byte AccessPointName[33];
            public fixed byte Password[64];
            public fixed byte IPAddress[16];
            public UInt16 Port;
        }
        #endregion
    }

    public class AnalyzerDeviceInfo
    {
        public required string Name { get; set; }
        public int MaxFrequency { get; set; }
        public int Channels { get; set; }
        public int BufferSize { get; set; }
        public required CaptureLimits[] ModeLimits { get; set; }
    }
    public enum CaptureMode
    {
        Channels_8 = 0,
        Channels_16 = 1,
        Channels_24 = 2
    }
    public class CaptureEventArgs : EventArgs
    {
        public AnalyzerDriverType SourceType { get; set; }
        public int TriggerChannel { get; set; }
        public int ChannelCount { get; set; }
        public int PreSamples { get; set; }
        public UInt128[]? Samples { get; set; }
        public int LoopCount { get; set; }
        public BurstInfo[]? Bursts { get; set; }
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
