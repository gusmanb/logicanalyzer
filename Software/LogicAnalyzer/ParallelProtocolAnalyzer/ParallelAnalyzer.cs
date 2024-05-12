using Avalonia.Media;
using AvaloniaEdit.Document;
using LogicAnalyzer.Controls;
using LogicAnalyzer.Protocols;
using System.Reflection;

namespace ParallelProtocolAnalyzer
{
    public class ParallelAnalyzer : ProtocolAnalyzerBase
    {
        private SimpleSegmentRenderer renderer = new SimpleSegmentRenderer();

        const string CS_SIGNAL_NAME = "CS";
        const string RD_SIGNAL_NAME = "RD";
        const string WR_SIGNAL_NAME = "WR";
        const string DATA_SIGNAL_NAME = "Data";
        const string ADDR_SIGNAL_NAME = "Address";
        const string RISING_EDGE = "Rising";
        const string FALLING_EDGE = "Falling";
        const string READ_OP = "Read";
        const string WRITE_OP = "Write";
        public override string ProtocolName
        {
            get
            {
                return "Parallel";
            }
        }

        static ProtocolAnalyzerSetting[] settings = new ProtocolAnalyzerSetting[] 
        {
            new ProtocolAnalyzerSetting
            {
                SettingType = ProtocolAnalyzerSetting.ProtocolAnalyzerSettingType.List,
                Caption = "CS edge",
                ListValues = new string[]{ RISING_EDGE, FALLING_EDGE }
            },
            new ProtocolAnalyzerSetting
            {
                SettingType = ProtocolAnalyzerSetting.ProtocolAnalyzerSettingType.List,
                Caption = "RD edge",
                ListValues = new string[]{ RISING_EDGE, FALLING_EDGE }
            },
            new ProtocolAnalyzerSetting
            {
                SettingType = ProtocolAnalyzerSetting.ProtocolAnalyzerSettingType.List,
                Caption = "WR edge",
                ListValues = new string[]{ RISING_EDGE, FALLING_EDGE }
            },
            new ProtocolAnalyzerSetting
            {
                SettingType = ProtocolAnalyzerSetting.ProtocolAnalyzerSettingType.Integer,
                Caption = "Read offset (in samples)",
                IntegerMinimumValue = 0,
                IntegerMaximumValue = 32
            },
            new ProtocolAnalyzerSetting
            {
                SettingType = ProtocolAnalyzerSetting.ProtocolAnalyzerSettingType.Integer,
                Caption = "Write offset (in samples)",
                IntegerMinimumValue = 0,
                IntegerMaximumValue = 32
            },
            new ProtocolAnalyzerSetting
            {
                SettingType = ProtocolAnalyzerSetting.ProtocolAnalyzerSettingType.Integer,
                Caption = "Data width",
                IntegerMinimumValue = 4,
                IntegerMaximumValue = 32
            },
            new ProtocolAnalyzerSetting
            {
                SettingType = ProtocolAnalyzerSetting.ProtocolAnalyzerSettingType.Integer,
                Caption = "Address width",
                IntegerMinimumValue = 0,
                IntegerMaximumValue = 32
            }
        };

        public override ProtocolAnalyzerSetting[] Settings
        {
            get
            {
                return settings;
            }
        }

        ProtocolAnalyzerSignal[] signals = new ProtocolAnalyzerSignal[] 
        {
            new ProtocolAnalyzerSignal
            {
                SignalName = CS_SIGNAL_NAME,
                Required = false
            },
            new ProtocolAnalyzerSignal
            {
                SignalName = RD_SIGNAL_NAME,
                Required = false
            },
            new ProtocolAnalyzerSignal
            {
                SignalName = WR_SIGNAL_NAME,
                Required = false
            },
            new ProtocolAnalyzerSignal
            {
                SignalName = DATA_SIGNAL_NAME,
                Required = true,
                IsBus = true
            },
            new ProtocolAnalyzerSignal
            {
                SignalName = ADDR_SIGNAL_NAME,
                Required = false,
                IsBus = true
            },
        };

        public override ProtocolAnalyzerSignal[] Signals
        {
            get
            {
                return signals;
            }
        }

        public override int GetBusWidth(ProtocolAnalyzerSignal Signal, ProtocolAnalyzerSettingValue[] SelectedSettings)
        {
            if (Signal.SignalName == DATA_SIGNAL_NAME)
                return (int)SelectedSettings[5].Value;

            if(Signal.SignalName == ADDR_SIGNAL_NAME)
                return (int)SelectedSettings[6].Value;

            return 0;
        }

        public override ProtocolAnalyzedChannel[] Analyze(int SamplingRate, int TriggerSample, ProtocolAnalyzerSettingValue[] SelectedSettings, ProtocolAnalyzerSelectedChannel[] SelectedChannels)
        {

            /*
             * The protocol analysis can work in two ways:
             * 1-The CS signal is provided, this is used as the sampling trigger, RD/WR signals will determine
             *   if the OP is read or write, if none of these are provided then the operation is undetermined.
             *   
             * 2-The CS signal is not provided, then the RD and/or WR signals will be used as trigger
             */

            bool csTrigger = false;
            bool useRD = false;
            bool useWR = false;

            //Check which trigger signals are used
            csTrigger = SelectedChannels.Any(c => c.SignalName == CS_SIGNAL_NAME);
            useRD = SelectedChannels.Any(c => c.SignalName == RD_SIGNAL_NAME);
            useWR = SelectedChannels.Any(c => c.SignalName == WR_SIGNAL_NAME);

            int csEdge = 0;
            int rdEdge = 0;
            int wrEdge = 0;

            //Obtain the edges
            if (csTrigger && SelectedSettings[0].Value?.ToString() == RISING_EDGE)
                csEdge = 1;

            if(useRD && SelectedSettings[1].Value?.ToString() == RISING_EDGE)
                rdEdge = 1;

            if(useWR && SelectedSettings[2].Value?.ToString() == RISING_EDGE)
                wrEdge = 1;

            //Get the sampling offsets
            int readOffset = (int)SelectedSettings[3].Value;
            int writeOffset = (int)SelectedSettings[4].Value;

            //Compose the control channels
            List<ControlChannel> controls = new List<ControlChannel>();

            if (csTrigger)
                controls.Add(new ControlChannel { Edge = (byte)csEdge, Samples = SelectedChannels.First(c => c.SignalName == CS_SIGNAL_NAME).Samples, SignalName = CS_SIGNAL_NAME });

            if(useRD)
                controls.Add(new ControlChannel { Edge = (byte)rdEdge, Samples = SelectedChannels.First(c => c.SignalName == RD_SIGNAL_NAME).Samples, SignalName = RD_SIGNAL_NAME });

            if(useWR)
                controls.Add(new ControlChannel { Edge = (byte)wrEdge, Samples = SelectedChannels.First(c => c.SignalName == WR_SIGNAL_NAME).Samples, SignalName = WR_SIGNAL_NAME });

            //Compose the data channels
            byte[][] dataBits = SelectedChannels.Where(c => c.SignalName == DATA_SIGNAL_NAME).OrderBy(c => c.BusIndex).Select(c => c.Samples).ToArray();

            //Compose the address channels
            byte[][] addressBits = SelectedChannels.Where(c => c.SignalName == ADDR_SIGNAL_NAME).OrderBy(c => c.BusIndex).Select(c => c.Samples).ToArray();

            //Find all ops
            List<OpData> foundOps = new List<OpData>();
            int offset = 0;

            OpData? next = FindNextOp(controls, dataBits, addressBits, readOffset, writeOffset, ref offset);

            while (next != null)
            {
                foundOps.Add(next);
                next = FindNextOp(controls, dataBits, addressBits, readOffset, writeOffset, ref offset);
            }

            //Compose all the data segments
            var segments = foundOps.Select(o => ComposeSegment(o, addressBits.Length, dataBits.Length));

            List<ProtocolAnalyzedChannel> results = new List<ProtocolAnalyzedChannel>();

            //If we are using a CS trigger...
            if (csTrigger)
            {
                var csChannel = SelectedChannels.First(c => c.SignalName == CS_SIGNAL_NAME);

                //All the operations are shown in the CS channel
                ProtocolAnalyzedChannel csChannelData = new ProtocolAnalyzedChannel(csChannel.SignalName, csChannel.ChannelIndex, renderer, segments.ToArray(), Colors.White, Color.FromArgb(100, Colors.Blue.R, Colors.Blue.G, Colors.Blue.B));

                results.Add(csChannelData);
            }
            else
            {
                if (useRD)
                {
                    var rdChannel = SelectedChannels.First(c => c.SignalName == RD_SIGNAL_NAME);

                    //Show read ops in RD channel
                    ProtocolAnalyzedChannel csChannelData = new ProtocolAnalyzedChannel(rdChannel.SignalName, rdChannel.ChannelIndex, renderer, segments.Where(s => s.Value.Contains(READ_OP)).ToArray(), Colors.White, Color.FromArgb(100, Colors.Green.R, Colors.Green.G, Colors.Green.B));

                    results.Add(csChannelData);
                }

                if (useWR)
                {
                    var wrChannel = SelectedChannels.First(c => c.SignalName == WR_SIGNAL_NAME);

                    //Show read ops in RD channel
                    ProtocolAnalyzedChannel csChannelData = new ProtocolAnalyzedChannel(wrChannel.SignalName, wrChannel.ChannelIndex, renderer, segments.Where(s => s.Value.Contains(WRITE_OP)).ToArray(), Colors.White, Color.FromArgb(100, Colors.Red.R, Colors.Red.G, Colors.Red.B));

                    results.Add(csChannelData);
                }
            }

            return results.ToArray();

        }

        private ProtocolAnalyzerDataSegment ComposeSegment(OpData o, int AddressBits, int DataBits)
        {
            int addressNibbles = (AddressBits / 4) + ((AddressBits % 4) == 0 ? 0 : 1);
            int dataNibbles = (DataBits / 4) + ((DataBits % 4) == 0 ? 0 : 1);

            ProtocolAnalyzerDataSegment segment = new ProtocolAnalyzerDataSegment();
            segment.FirstSample = o.Start;
            segment.LastSample = o.End - 1;
            string value = "";

            if (addressNibbles != 0 && o.Address != null)
                value += $"A: 0x{o.Address.Value.ToString($"X{addressNibbles}")}\r\n";

            if (o.Operation != null)
                value += $"{o.Operation}: 0x{o.Value.ToString($"X{dataNibbles}")}";
            else
                value += $"V: 0x{o.Value.ToString($"X{dataNibbles}")}";

            segment.Value = value;

            return segment;
        }

        private OpData? FindNextOp(IEnumerable<ControlChannel> controls, byte[][] dataBits, byte[][] addressBits, int readOffset, int writeOffset, ref int offset)
        {
            int max = dataBits[0].Length;

            int start = -1;
            int end = max;

            //Find the trigger and range
            if (controls.Any(c => c.SignalName == CS_SIGNAL_NAME))
            {
                var cs = controls.First(c => c.SignalName == CS_SIGNAL_NAME);

                for (int buc = offset; buc < max; buc++)
                {
                    if (cs.Samples[buc] == cs.Edge)
                    {
                        start = buc;
                        break;
                    }
                }

                if (start == -1)
                    return null;

                for (int buc = start; buc < max; buc++)
                {
                    if (cs.Samples[buc] != cs.Edge)
                    {
                        end = buc;
                        break;
                    }
                }
            }
            else
            {
                ControlChannel? trigger = null;

                for (int buc = offset; buc < max; buc++)
                {
                    foreach(var control in controls) 
                    {
                        if (control.Samples[buc] == control.Edge)
                        {
                            trigger = control;
                            start = buc;
                            break;
                        }
                    }

                    if (trigger != null)
                        break;
                }

                if (trigger == null)
                    return null;

                for (int buc = start; buc < max; buc++)
                {
                    if (trigger.Samples[buc] != trigger.Edge)
                    {
                        end = buc;
                        break;
                    }
                }
            }

            OpData op = new OpData { Start = start, End = end };

            int samplePos = start;

            op.Operation = GetOp(controls, samplePos);
            op.Address = GetAddress(addressBits, samplePos);

            if (op.Operation == READ_OP)
            {
                if (start + readOffset < end)
                    samplePos = start + readOffset;
                else
                    samplePos = end - 1;
            }
            else if (op.Operation == WRITE_OP)
            {
                if (start + writeOffset < end)
                    samplePos = start + writeOffset;
                else
                    samplePos = end - 1;
            }
            else
            {
                int maxOffset = readOffset > writeOffset ? readOffset : writeOffset;

                if (start + maxOffset < end)
                    samplePos = start + maxOffset;
                else
                    samplePos = end - 1;
            }

            op.Value = GetData(dataBits, samplePos);
            
            offset = end;

            return op;
        }

        private string? GetOp(IEnumerable<ControlChannel> controls, int samplePos)
        {
            var rdChannel = controls.FirstOrDefault(c => c.SignalName == RD_SIGNAL_NAME);
            var wrChannel = controls.FirstOrDefault(c => c.SignalName == WR_SIGNAL_NAME);

            if(rdChannel == null && wrChannel == null)
                return null;

            if (rdChannel != null && rdChannel.Samples[samplePos] == rdChannel.Edge)
                return READ_OP;

            if (wrChannel != null && wrChannel.Samples[samplePos] == wrChannel.Edge)
                return WRITE_OP;

            return null;
        }

        private uint? GetAddress(byte[][] addressBits, int samplePos)
        {
            if(addressBits == null || addressBits.Length == 0) 
                return null;

            uint address = 0;

            for (int buc = 0; buc < addressBits.Length; buc++)
                address |= (uint)(addressBits[buc][samplePos] << buc);

            return address;
        }

        private uint GetData(byte[][] dataBits, int samplePos)
        {
            uint value = 0;

            for(int buc = 0; buc <  dataBits.Length; buc++) 
                value |= (uint)(dataBits[buc][samplePos] << buc);
            
            return value;

        }

        public override bool ValidateSettings(ProtocolAnalyzerSettingValue[] SelectedSettings, ProtocolAnalyzerSelectedChannel[] SelectedChannels)
        {
            bool csTrigger = false;
            bool useRD = false;
            bool useWR = false;

            //Check which trigger signals are used
            csTrigger = SelectedChannels.Any(c => c.SignalName == CS_SIGNAL_NAME);
            useRD = SelectedChannels.Any(c => c.SignalName == RD_SIGNAL_NAME);
            useWR = SelectedChannels.Any(c => c.SignalName == WR_SIGNAL_NAME);

            //If no control signal selected then configuration is invalid
            if (!csTrigger && !useRD && !useWR)
                return false;

            //If CS signal is selected, check for the edge selection
            if(csTrigger && SelectedSettings[0].Value == null)
                return false;

            //If RD signal is selected, check for the edge selection
            if (useRD && SelectedSettings[1].Value == null)
                return false;

            //If WR signal is selected, check for the edge selection
            if (useWR && SelectedSettings[2].Value == null)
                return false;

            int addressSize = 0;

            if (SelectedSettings[5].Value != null)
                addressSize = (int)SelectedSettings[5].Value;

            //If an address size is provided check for its channels
            if (addressSize > 0 && !SelectedChannels.Any(c => c.SignalName == ADDR_SIGNAL_NAME))
                return false;

            //Check for the data channels
            if (!SelectedChannels.Any(c => c.SignalName == DATA_SIGNAL_NAME))
                return false;

            return true;
        }

        private class ControlChannel
        {
            public string SignalName { get; set; }
            public byte[] Samples { get; set; }
            public byte Edge { get; set; }
        }

        private class OpData
        {
            public int Start { get; set; }
            public int End { get; set; }
            public uint? Address { get; set; }
            public uint Value { get; set; }
            public string? Operation { get; set; }
        }
    }
}
