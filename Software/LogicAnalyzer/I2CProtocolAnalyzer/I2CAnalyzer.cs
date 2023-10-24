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
            string addr = "";
            string op = "";
            string addr_space = "";
            byte value;
            bool ack;
            bool frameError;
            bool foundStartStop;

            bool repeatStart = false;
            bool addressByte = true;
            bool address10 = false;
            bool address10read = false;
            byte firstAddressByte = 0;

            int pos = FindStartCondition(0, scl, sda, out startPosition, out endPosition);

            if (pos == -1)
                // If no start is found no further analysis
                return new ProtocolAnalyzedChannel[0];

            segments.Add(new ProtocolAnalyzerDataSegment { FirstSample = startPosition, LastSample = endPosition, Value = $"START" });

            while (pos < sda.Samples.Length)
            {
                // iterate through samples byte by byte
                pos = ReadByte(pos, scl, sda, out startPosition, out endPosition, out value, out ack, out frameError);

                // no (more) bytes stop processing
                if (pos == -1)
                    break;

                // Create New Empty Segment
                var segment = new ProtocolAnalyzerDataSegment { FirstSample = startPosition, LastSample = endPosition, Value = "" };

                // convert byte value to printable ascii or '.'
                string asciival = value >= 0x20 && value <= 0x7e ? Encoding.ASCII.GetString(new byte[] { (byte)value }) : "·";


                if (address10read)
                {
                    address10read = false;
                    // Check for 10 bit high address pattern
                    // 0b11110NNN
                    if ((value & 0xf8) == 0xf0)
                    {
                        // current byte is firstAddressByte with read set
                        if ((firstAddressByte | 1) == value)
                        {
                            // Reset addressByte from repeat start
                            addressByte = false;
                            segment.Value += "10b Op Change";
                            segment.Value += $"\r\nAddress: {addr}";
                            segment.Value += $" Op: {op}";
                            // Don't change op until after adding current segment value
                            op = "Read";

                        }
                        // else This is a new start with a new address
                    }
                }

                // Check/Parse address byte(s)
                if (addressByte)
                {
                    addressByte = false;

                    op = (value & 1) == 1 ? "Read" : "Write";

                    // Check 10bit High Byte address mask
                    // 0x11110NNN
                    if ((value & 0xf8) == 0xf0)
                    {
                        // Mark for 10 bit second byte address parsing 
                        address10 = true;
                        firstAddressByte = value;
                        segment.Value += "10b High Addr Byte";
                        addr_space = "10b";
                        addr = $">= {((value & 6) >> 1) << 7}";
                    }
                    else
                    {
                        addr = $"0x{value >> 1:X2}";
                        addr_space = "7b";
                        // Add 7Bit Address to Segment
                        // Address (7b): 0x12
                        segment.Value += $"{addr_space} Address: {addr}";
                    }
                    // Add Operation to segment for address Byte
                    segment.Value += $"\r\nOp: {op}";

                }
                // Parse 10 bit low address byte
                else if (address10)
                {
                    address10 = false;
                    addr = $"0x{((firstAddressByte & 6) << 7) | value:X4}";
                    // Add 10 bit address to segment using high byte address bits and current byte value
                    // Address (10b): 0x031A
                    segment.Value += "10b Low Addr Byte";
                    segment.Value += $"\r\nAddress: {addr} Op: {op}";

                    // enable check for high address byte repeat with read bit 
                    address10read = true;
                }

                if (segment.Value == "")
                {
                    // Add Addr Data to Empty Segment
                    segment.Value += $"{addr_space} {addr}";
                }
                // Add Byte Data to Segment
                // HEX_VALUE 'ASCII_VALUE' <A(CK)/N(ACK)/F(rame Error)>
                // 0x3A ':' <A>
                segment.Value += $"\r\n{op}: 0x{value.ToString("X2")} '{asciival}' <{(ack ? "A" : "N")}{(frameError ? "F" : "")}>";

                // Add segment for processed byte
                segments.Add(segment);

                bool isStart;

                // Search for next start 
                pos = FindStartStopCondition(pos, scl, sda, out isStart, out startPosition, out endPosition, out foundStartStop);

                // no more start/stop processing complete
                // TODO: REMOVE? this assumes capture ends with whole transaction? 
                if (pos == -1)
                    break;

                if (foundStartStop)
                {
                    string start_stop = (repeatStart && isStart) ? "RE-START" : (isStart ? "START" : "STOP");
                    // Add START/STOP segment
                    segments.Add(new ProtocolAnalyzerDataSegment { FirstSample = startPosition, LastSample = endPosition, Value = start_stop });
                    repeatStart = isStart;
                    addressByte = true;
                }

                // If last start/stop is not start look for following start 
                if (foundStartStop && !isStart)
                {
                    pos = FindStartCondition(pos, scl, sda, out startPosition, out endPosition);

                    if (pos == -1)
                        break;

                    segments.Add(new ProtocolAnalyzerDataSegment { FirstSample = startPosition, LastSample = endPosition, Value = $"START" });

                }
            }

            ProtocolAnalyzedChannel channel = new ProtocolAnalyzedChannel("SDA", sda.ChannelIndex, renderer, segments.ToArray(), Colors.White, Color.FromUInt32(0x7f008b8b));

            return new ProtocolAnalyzedChannel[] { channel
    };
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