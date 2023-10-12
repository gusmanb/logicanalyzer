using Avalonia.Input.TextInput;
using Avalonia.Media;
using LogicAnalyzer.Protocols;
using Newtonsoft.Json.Linq;
using System.Data;
using System.Text;

namespace I2CProtocolAnalyzer
{
    public class I2CAnalyzer : ProtocolAnalyzerBase
    {
        private SimpleSegmentRenderer renderer = new SimpleSegmentRenderer();

        public override string ProtocolName
        {
            get
            {
                return "I2C";
            }
        }

        public override ProtocolAnalyzerSetting[] Settings
        {
            get
            {
                return new ProtocolAnalyzerSetting[0];
            }
        }

        public override ProtocolAnalyzerSignal[] Signals
        {
            get
            {
                return new ProtocolAnalyzerSignal[]
                {
                    new ProtocolAnalyzerSignal{ Required = true, SignalName = "SCL" },
                    new ProtocolAnalyzerSignal{ Required = true, SignalName = "SDA" },
                };
            }
        }

        public override ProtocolAnalyzedChannel[] Analyze(int SamplingRate, int TriggerSample, ProtocolAnalyzerSettingValue[] SelectedSettings, ProtocolAnalyzerSelectedChannel[] SelectedChannels)
        {
            var scl = SelectedChannels.Where(c => c.SignalName == "SCL").First();
            var sda = SelectedChannels.Where(c => c.SignalName == "SDA").First();

            List<ProtocolAnalyzerDataSegment> segments = new List<ProtocolAnalyzerDataSegment>();

            int startPosition;
            int endPosition;
            byte value;
            bool ack;
            bool frameError;
            bool foundStartStop;

            bool addressByte = true;
            bool address10 = false;
            byte firstAddressByte = 0;

            int pos = FindStartCondition(0, scl, sda, out startPosition, out endPosition);

            if (pos == -1)
                return new ProtocolAnalyzedChannel[0];

            segments.Add(new ProtocolAnalyzerDataSegment { FirstSample = startPosition, LastSample = endPosition, Value = $"START" });

            while (pos < sda.Samples.Length)
            {
                pos = ReadByte(pos, scl, sda, out startPosition, out endPosition, out value, out ack, out frameError);

                if (pos == -1)
                    break;

                string asciival = value >= 0x20 && value <= 0x7e ? Encoding.ASCII.GetString(new byte[] { (byte)value }) : "·";

                var segment = new ProtocolAnalyzerDataSegment { FirstSample = startPosition, LastSample = endPosition, Value = $"0x{value.ToString("X2")} '{asciival}' <{(ack ? "A" : "N")}{(frameError ? "F" : "")}>" };

                if (addressByte)
                {
                    addressByte = false;

                    segment.Value += $"\r\nOp: {((value & 1) == 1 ? "Read" : "Write")}";

                    if ((value & 0xf8) == 0xf7)
                    {
                        address10 = true;
                        firstAddressByte = value;
                    }
                    else
                        segment.Value += $"\r\nAddress (7b): 0x{(value >> 1).ToString("X2")}";

                }
                else if (address10)
                {
                    address10 = false;
                    segment.Value += $"\r\nAddress (10b): {(((firstAddressByte & 6) << 7) | value).ToString("X4")}";
                }

                segments.Add(segment);

                bool isStart;

                pos = FindStartStopCondition(pos, scl, sda, out isStart, out startPosition, out endPosition, out foundStartStop);

                if (pos == -1)
                    break;

                if (foundStartStop)
                    segments.Add(new ProtocolAnalyzerDataSegment { FirstSample = startPosition, LastSample = endPosition, Value = isStart ? "START" : "STOP" });

                if (foundStartStop && !isStart)
                {
                    pos = FindStartCondition(pos, scl, sda, out startPosition, out endPosition);

                    if (pos == -1)
                        break;

                    segments.Add(new ProtocolAnalyzerDataSegment { FirstSample = startPosition, LastSample = endPosition, Value = $"START" });

                    addressByte = true;
                }
            }

            ProtocolAnalyzedChannel channel = new ProtocolAnalyzedChannel("SDA", sda.ChannelIndex, renderer, segments.ToArray(), Colors.White, Color.FromUInt32(0x7f008b8b));

            return new ProtocolAnalyzedChannel[] { channel };
        }

        private int FindStartStopCondition(int pos, ProtocolAnalyzerSelectedChannel scl, ProtocolAnalyzerSelectedChannel sda, out bool isStart, out int startPosition, out int endPosition, out bool found)
        {
            int initialPosition = pos;
            isStart = false;
            startPosition = 0;
            endPosition = 0;
            found = false;

            while (pos < scl.Samples.Length && scl.Samples[pos] != 1)
                pos++;

            if (pos >= scl.Samples.Length)
                return -1;

            startPosition = pos;

            byte val = sda.Samples[pos];
            //Initial state will indicate if this may be an start or an stop
            isStart = val == 1;

            while (pos < scl.Samples.Length && scl.Samples[pos] == 1)
            {
                if (val != sda.Samples[pos])
                {
                    found = true;
                    break;
                }
                pos++;
            }

            if (pos >= scl.Samples.Length)
                return -1;

            if (!found)
                return initialPosition;

            endPosition = pos - 1;

            return pos;
        }

        private int FindStartCondition(int pos, ProtocolAnalyzerSelectedChannel scl, ProtocolAnalyzerSelectedChannel sda, out int startPosition, out int endPosition)
        {
            startPosition = 0; endPosition = 0;

            while (pos < scl.Samples.Length)
            {
                while (pos < scl.Samples.Length && scl.Samples[pos] != 1)
                    pos++;

                if (pos >= scl.Samples.Length)
                    return -1;

                startPosition = pos;
                bool foundStart = false;

                if (scl.Samples[pos] != 1) //SDA is low, it cannot be a start
                {
                    while (pos < scl.Samples.Length && scl.Samples[pos] == 1)
                        pos++;

                    if (pos >= scl.Samples.Length)
                        return -1;
                }
                else
                {
                    while (pos < scl.Samples.Length && scl.Samples[pos] == 1)
                    {
                        if (sda.Samples[pos] != 1)
                        {
                            foundStart = true;
                            break;
                        }

                        pos++;
                    }
                }

                if (foundStart)
                {
                    endPosition = pos - 1;
                    return pos;
                }
            }

            return -1;
        }

        private int ReadByte(int pos, ProtocolAnalyzerSelectedChannel scl, ProtocolAnalyzerSelectedChannel sda, out int byteStart, out int byteEnd, out byte value, out bool ack, out bool frameError)
        {
            byteStart = 0; byteEnd = 0; value = 0; ack = false; frameError = false;

            while (pos < scl.Samples.Length && scl.Samples[pos] == 1) //Find next low clock
                pos++;

            if (pos >= scl.Samples.Length) //
                return -1;

            byteStart = pos;

            for (int buc = 0; buc < 9; buc++)
            {
                while (pos < scl.Samples.Length && scl.Samples[pos] == 1) //Find next low clock
                    pos++;

                while (pos < scl.Samples.Length && scl.Samples[pos] == 0) //Find high clock
                    pos++;

                if (pos >= scl.Samples.Length) //
                    return -1;

                byte sampleValue = sda.Samples[pos];

                if (buc < 8)
                {
                    value |= (byte)(sampleValue << (7 - buc)); //Get the value

                }
                else
                    ack = sampleValue == 0; //Get the ACK/NACK

                //Check for frame errors, any change of SDA while SCL is high and is in the middle
                //of a byte is a frame error, SDA can change only while the bus is idle or at the end of a byte
                //indicating a start or a stop
                while (pos < scl.Samples.Length && scl.Samples[pos] == 1)
                {
                    if (sda.Samples[pos] != sampleValue)
                        frameError = true;

                    pos++;
                }
            }

            byteEnd = pos - 1;

            return pos;
        }

        public override bool ValidateSettings(ProtocolAnalyzerSettingValue[] SelectedSettings, ProtocolAnalyzerSelectedChannel[] SelectedChannels)
        {
            if (SelectedChannels == null || SelectedChannels.Length != 2)
                return false;

            return true;
        }
    }
}