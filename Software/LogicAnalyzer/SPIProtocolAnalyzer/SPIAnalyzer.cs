using Avalonia.Media;
using LogicAnalyzer.Protocols;
using System.Text;

namespace SPIProtocolAnalyzer
{
    public class SPIAnalyzer : ProtocolAnalyzerBase
    {

        private SimpleSegmentRenderer renderer = new SimpleSegmentRenderer();

        public override string ProtocolName
        {
            get
            {
                return "SPI";
            }
        }

        static ProtocolAnalyzerSetting[] settings = new ProtocolAnalyzerSetting[]
        {
            new ProtocolAnalyzerSetting
            {
                Caption = "Shift order",
                ListValues = new string[]{ "Right-to-Left", "Left-to-Right" },
                SettingType = ProtocolAnalyzerSetting.ProtocolAnalyzerSettingType.List
            },
            new ProtocolAnalyzerSetting
            {
                Caption ="CPOL",
                ListValues=new string[]{ "0", "1" },
                SettingType = ProtocolAnalyzerSetting.ProtocolAnalyzerSettingType.List
            },
            new ProtocolAnalyzerSetting
            {
                Caption ="CPHA",
                ListValues=new string[]{ "0", "1" },
                SettingType = ProtocolAnalyzerSetting.ProtocolAnalyzerSettingType.List
            }
        };

        public override ProtocolAnalyzerSetting[] Settings
        {
            get
            {
                return settings;
            }
        }

        static ProtocolAnalyzerSignal[] signals = new ProtocolAnalyzerSignal[]
        {
            new ProtocolAnalyzerSignal
            {
                Required = false,
                SignalName= "CS"
            },
            new ProtocolAnalyzerSignal
            {
                Required = true,
                SignalName = "CK"
            },
            new ProtocolAnalyzerSignal
            {
                Required = false,
                SignalName ="MISO"
            },
            new ProtocolAnalyzerSignal
            {
                Required = false,
                SignalName = "MOSI"
            }
        };

        public override ProtocolAnalyzerSignal[] Signals
        {
            get
            {
                return signals;
            }
        }

        public override ProtocolAnalyzedChannel[] Analyze(int SamplingRate, int TriggerSample, ProtocolAnalyzerSettingValue[] SelectedSettings, ProtocolAnalyzerSelectedChannel[] SelectedChannels)
        {
            string shiftOrder = SelectedSettings[0].Value.ToString();
            int cpol = int.Parse(SelectedSettings[1].Value.ToString());
            int cpha = int.Parse(SelectedSettings[2].Value.ToString());

            var csChannel = SelectedChannels.Where(c => c.SignalName == "CS").FirstOrDefault();
            var ckChannel = SelectedChannels.Where(c => c.SignalName == "CK").FirstOrDefault();
            var misoChannel = SelectedChannels.Where(c => c.SignalName == "MISO").FirstOrDefault();
            var mosiChannel = SelectedChannels.Where(c => c.SignalName == "MOSI").FirstOrDefault();

            var ranges = FindActiveRanges(csChannel, ckChannel.Samples.Length);

            List<ProtocolAnalyzedChannel> results = new List<ProtocolAnalyzedChannel>();

            results.Add(AnalyzeClock(ranges, ckChannel, cpol));
            results.AddRange(AnalyzeChannels(ranges, ckChannel, misoChannel, mosiChannel, shiftOrder, cpol, cpha));

            return results.ToArray();
        }

        private ProtocolAnalyzedChannel AnalyzeClock(IEnumerable<ActiveRange> ranges, ProtocolAnalyzerSelectedChannel ckChannel, int cpol)
        {
            List<ProtocolAnalyzerDataSegment> segments = new List<ProtocolAnalyzerDataSegment>();

            foreach (var range in ranges)
            {
                var clockRange = ckChannel.Samples.Skip(range.FirstSample).Take(range.Length).ToArray();

                if (clockRange[0] != cpol)
                {
                    var errorEnd = FindSample(0, clockRange, cpol);

                    if (errorEnd == -1)
                        errorEnd = clockRange.Length;

                    segments.Add(new ProtocolAnalyzerDataSegment { FirstSample = range.FirstSample, LastSample = errorEnd + range.FirstSample });
                }
            }

            var result = new ProtocolAnalyzedChannel(ckChannel.SignalName, ckChannel.ChannelIndex, renderer, segments.ToArray(), Colors.White, Color.FromArgb(90, Colors.Blue.R, Colors.Blue.G, Colors.Blue.B));

            return result;
        }

        private IEnumerable<ProtocolAnalyzedChannel> AnalyzeChannels(IEnumerable<ActiveRange> ranges, ProtocolAnalyzerSelectedChannel ckChannel, ProtocolAnalyzerSelectedChannel? misoChannel, ProtocolAnalyzerSelectedChannel? mosiChannel, string? shiftOrder, int cpol, int cpha)
        {
            List<ProtocolAnalyzedChannel> results = new List<ProtocolAnalyzedChannel>();

            if (misoChannel != null)
                results.Add(AnalyzeChannel(ranges, ckChannel, misoChannel, shiftOrder, cpol, cpha, Color.FromArgb(100, Colors.Red.R, Colors.Red.G, Colors.Red.B)));

            if (mosiChannel != null)
                results.Add(AnalyzeChannel(ranges, ckChannel, mosiChannel, shiftOrder, cpol, cpha, Color.FromArgb(100, Colors.Green.R, Colors.Green.G, Colors.Green.B)));

            return results;
        }

        private ProtocolAnalyzedChannel AnalyzeChannel(IEnumerable<ActiveRange> ranges, ProtocolAnalyzerSelectedChannel ckChannel, ProtocolAnalyzerSelectedChannel dataChannel, string? shiftOrder, int cpol, int cpha, Color channelColor)
        {


            List<ProtocolAnalyzerDataSegment> segments = new List<ProtocolAnalyzerDataSegment>();

            foreach (var range in ranges)
            {
                var clockRange = ckChannel.Samples.Skip(range.FirstSample).Take(range.Length).ToArray();
                var dataRange = dataChannel.Samples.Skip(range.FirstSample).Take(range.Length).ToArray();

                int firstClockSample = FindFirstSampleClock(0, clockRange, cpol, cpha);

                if (firstClockSample == -1)
                {
                    ProtocolAnalyzerDataSegment segment = new ProtocolAnalyzerDataSegment { FirstSample = range.FirstSample, LastSample = range.LastSample, Value = "Frame error" };
                    segments.Add(segment);
                    continue;
                }
                else
                {
                    int lastSample;
                    int value = GetByte(firstClockSample, clockRange, dataRange, shiftOrder, cpha, out lastSample);

                    while (value != -1)
                    {

                        string asciival = value >= 0x20 && value <= 0x7e ? Encoding.ASCII.GetString(new byte[] { (byte)value }) : "·";

                        ProtocolAnalyzerDataSegment segment = new ProtocolAnalyzerDataSegment { FirstSample = range.FirstSample + firstClockSample, LastSample = range.FirstSample + lastSample, Value = $"0x{value.ToString("X2")} '{asciival}'" };
                        segments.Add(segment);

                        firstClockSample = FindFirstSampleClock(lastSample, clockRange, cpol, cpha);

                        if (firstClockSample == -1)
                            value = -1;
                        else
                            value = GetByte(firstClockSample, clockRange, dataRange, shiftOrder, cpha, out lastSample);

                    }
                }
            }

            var result = new ProtocolAnalyzedChannel(dataChannel.SignalName, dataChannel.ChannelIndex, renderer, segments.ToArray(), Colors.White, channelColor);

            return result;
        }

        private int GetByte(int firstClockSample, byte[] clockRange, byte[] dataRange, string? shiftOrder, int cpha, out int lastSample)
        {
            lastSample = 0;
            byte[] values = new byte[8];

            int currentSample = firstClockSample;

            values[0] = dataRange[firstClockSample];

            for (int buc = 1; buc < 8; buc++)
            {
                if (currentSample == -1)
                    return -1;

                int edgeIndex = FindSample(currentSample, clockRange, cpha == 0 ? 1 : 0);
                if (edgeIndex == -1)
                    return -1;

                values[buc] = dataRange[edgeIndex];
                currentSample = FindSample(edgeIndex, clockRange, cpha);

            }

            int value;

            if (shiftOrder == settings[0].ListValues[1])
            {
                value = values[0] |
                    (values[1] << 1) |
                    (values[2] << 2) |
                    (values[3] << 3) |
                    (values[4] << 4) |
                    (values[5] << 5) |
                    (values[6] << 6) |
                    (values[7] << 7);
            }
            else
            {
                value = values[7] |
                    (values[6] << 1) |
                    (values[5] << 2) |
                    (values[4] << 3) |
                    (values[3] << 4) |
                    (values[2] << 5) |
                    (values[1] << 6) |
                    (values[0] << 7);
            }

            lastSample = currentSample == -1 ? dataRange.Length - 1 : currentSample;

            return value;
        }

        private int FindFirstSampleClock(int start, byte[] clockRange, int cpol, int cpha)
        {
            int pos = start;

            if (cpol == 0 && cpha == 0)
            {
                //Low-high
                pos = FindSample(pos, clockRange, 0);

                if (pos == -1)
                    return -1;

                return FindSample(pos, clockRange, 1);

            }
            else if (cpol == 0 && cpha == 1)
            {
                //Low-high-low
                pos = FindSample(pos, clockRange, 0);

                if (pos == -1)
                    return -1;

                pos = FindSample(pos, clockRange, 1);

                if (pos == -1)
                    return -1;

                return FindSample(pos, clockRange, 0);
            }
            else if (cpol == 1 && cpha == 0)
            {
                //High-low
                pos = FindSample(pos, clockRange, 1);

                if (pos == -1)
                    return -1;


                return FindSample(pos, clockRange, 0);

            }
            else if (cpol == 1 && cpha == 1)
            {
                //High-log-high

                pos = FindSample(pos, clockRange, 1);

                if (pos == -1)
                    return -1;

                pos = FindSample(pos, clockRange, 0);

                if (pos == -1)
                    return -1;

                return FindSample(pos, clockRange, 1);

            }

            return -1;
        }

        private int FindSample(int Start, byte[] Samples, int Value)
        {
            for (int i = Start; i < Samples.Length; i++)
                if (Samples[i] == Value)
                    return i;

            return -1;
        }

        private IEnumerable<ActiveRange> FindActiveRanges(ProtocolAnalyzerSelectedChannel? csChannel, int length)
        {
            if (csChannel == null)
                return new ActiveRange[] { new ActiveRange { FirstSample = 0, LastSample = length - 1 } };

            List<ActiveRange> ranges = new List<ActiveRange>();

            ActiveRange? underConstruction = null;

            for (int buc = 0; buc < csChannel.Samples.Length; buc++)
            {
                if (csChannel.Samples[buc] == 0)
                {
                    if (underConstruction == null)
                        underConstruction = new ActiveRange { FirstSample = buc, LastSample = buc };
                    else
                        underConstruction.LastSample = buc;
                }
                else
                {
                    if (underConstruction == null)
                        continue;

                    underConstruction.LastSample = buc;
                    ranges.Add(underConstruction);
                    underConstruction = null;
                }

            }

            if (underConstruction != null)
            {
                ranges.Add(underConstruction);
                underConstruction = null;
            }

            return ranges;
        }

        public override bool ValidateSettings(ProtocolAnalyzerSettingValue[] SelectedSettings, ProtocolAnalyzerSelectedChannel[] SelectedChannels)
        {
            var setOrder = SelectedSettings.Where(s => s.SettingIndex == 0).FirstOrDefault();

            if (setOrder == null || setOrder.Value is not string || !settings[0].ListValues.Contains(setOrder.Value.ToString()))
                return false;

            var setCPOL = SelectedSettings.Where(s => s.SettingIndex == 1).FirstOrDefault();

            if (setCPOL == null || setCPOL.Value is not string || !settings[1].ListValues.Contains(setCPOL.Value.ToString()))
                return false;

            var setCPHA = SelectedSettings.Where(s => s.SettingIndex == 2).FirstOrDefault();

            if (setCPHA == null || setCPHA.Value is not string || !settings[2].ListValues.Contains(setCPHA.Value.ToString()))
                return false;

            if (!SelectedChannels.Any(s => (s.SignalName == "MISO" || s.SignalName == "MOSI") && s.ChannelIndex > -1))
                return false;

            return true;
        }

        class ActiveRange
        {
            public int FirstSample { get; set; }
            public int LastSample { get; set; }

            public int Length { get { return LastSample - FirstSample + 1; } }
        }
    }
}