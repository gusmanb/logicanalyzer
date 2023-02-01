using Avalonia.Controls;
using Avalonia.Media;
using LogicAnalyzer.Protocols;
using System.Text;

namespace SerialProtocolAnalyzer
{
    public class SerialAnalyzer : ProtocolAnalyzerBase
    {
        private SimpleSegmentRenderer renderer = new SimpleSegmentRenderer();

        static ProtocolAnalyzerSetting[] settings = new ProtocolAnalyzerSetting[]
        {
            new ProtocolAnalyzerSetting
            { 
                Caption = "Polarity",
                SettingType = ProtocolAnalyzerSetting.ProtocolAnalyzerSettingType.List,
                ListValues = new string[] { "Positive (TTL)", "Negative (RS232)" }
            },
            new ProtocolAnalyzerSetting
            {
                Caption = "Data bits",
                SettingType = ProtocolAnalyzerSetting.ProtocolAnalyzerSettingType.List,
                ListValues = new string[] { "8", "7" }
            },
            new ProtocolAnalyzerSetting
            {
                Caption = "Parity",
                SettingType = ProtocolAnalyzerSetting.ProtocolAnalyzerSettingType.List,
                ListValues = new string[] { "None", "Even", "Odd" }
            },
            new ProtocolAnalyzerSetting
            {
                Caption = "Stop bits",
                SettingType = ProtocolAnalyzerSetting.ProtocolAnalyzerSettingType.List,
                ListValues = new string[] { "1", "1.5", "2" }
            },
            new ProtocolAnalyzerSetting
            {
                Caption = "Bauds",
                SettingType = ProtocolAnalyzerSetting.ProtocolAnalyzerSettingType.Integer,
                IntegerMinimumValue= 200,
                IntegerMaximumValue= 20000000,
            }
        };
        static ProtocolAnalyzerSignal[] signals = new ProtocolAnalyzerSignal[] 
        {
            new ProtocolAnalyzerSignal{ SignalName = "RX", Required = false },
            new ProtocolAnalyzerSignal{ SignalName = "TX", Required = false },
        };
        public override string ProtocolName
        {
            get
            {
                return "Serial";
            }
        }

        public override ProtocolAnalyzerSetting[] Settings
        {
            get
            {
                return settings;
            }
        }

        public override ProtocolAnalyzerSignal[] Signals
        {
            get
            {
                return signals;
            }
        }

        public override ProtocolAnalyzedChannel[] Analyze(int SamplingRate, int TriggerSample, ProtocolAnalyzerSettingValue[] SelectedSettings, ProtocolAnalyzerSelectedChannel[] SelectedChannels)
        {
            double period = (double)SamplingRate / (double)(int)SelectedSettings[4].Value;

            if (period < 1)
                return new ProtocolAnalyzedChannel[0];

            int zero = SelectedSettings[0].Value.ToString() == settings[0].ListValues[0] ? 0 : 1;

            int dataBits = int.Parse(SelectedSettings[1].Value.ToString());
            string parity = SelectedSettings[2].Value.ToString();
            double stopBits = double.Parse(SelectedSettings[3].Value.ToString());
            List<ProtocolAnalyzedChannel> analyzed = new List<ProtocolAnalyzedChannel>();

            foreach(var channel in SelectedChannels)
                analyzed.Add(AnalyzeSerialData(dataBits, parity, stopBits, period, zero, channel));

            return analyzed.ToArray();
        }

        private ProtocolAnalyzedChannel AnalyzeSerialData(int dataBits, string? parity, double stopBits, double period, int zero, ProtocolAnalyzerSelectedChannel channel)
        {
            List<ProtocolAnalyzerDataSegment> segments = new List<ProtocolAnalyzerDataSegment>();

            int pos = 0;

            //Minimum samples needed for a byte, we skip the parity bits for the chance of getting a byte at the end
            //of the samples
            int samplesPerByte = (int)Math.Ceiling(period * (dataBits + (parity == "None" ? 0 : 1)));

            while (pos < channel.Samples.Length)
            {
                //Find idle
                while (pos < channel.Samples.Length && channel.Samples[pos] == zero)
                    pos++;

                //Find start condition
                while (pos < channel.Samples.Length && channel.Samples[pos] != zero)
                    pos++;

                //Not found? abort
                if (pos >= channel.Samples.Length)
                    break;

                byte value = 0;
                byte val = 0;
                bool parityError = false;
                bool frameError = false;
                int oneCount = 0;
                int startPos = pos;

                //If there are not enough bits for a byte end the loop
                if (pos + samplesPerByte >= channel.Samples.Length)
                    break;

                //Position our sampling "pointer" on the middle of the start bit
                double samplePos = pos + (period / 2) - 1; //

                for (int buc = 0; buc < dataBits; buc++)
                {
                    samplePos += period;
                    val = channel.Samples[(int)Math.Round(samplePos, 0)] == zero ? (byte)0 : (byte)1;
                    value |= (byte)(val << buc);
                    if (val == 1)
                        oneCount++;
                }

                if (parity != "None")
                {
                    samplePos += period;
                    val = channel.Samples[(int)Math.Round(samplePos, 0)] == zero ? (byte)0 : (byte)1;
                    if (val == 1)
                        oneCount++;

                    if((parity == "Even" && oneCount % 2 != 0) || (parity == "Odd" && oneCount % 2 == 0))
                        parityError = true;
                }

                samplePos += period;
                if (samplePos >= channel.Samples.Length)
                    break;
                val = channel.Samples[(int)Math.Round(samplePos, 0)] == zero ? (byte)0 : (byte)1;

                if(val != 1)
                    frameError = true;

                if (stopBits != 1)
                {
                    samplePos += stopBits == 2 ? period : period * 0.75f;
                    if (samplePos >= channel.Samples.Length)
                        break;
                    val = channel.Samples[(int)Math.Round(samplePos, 0)] == zero ? (byte)0 : (byte)1;

                    if (val != 1)
                        frameError = true;
                }

                int endPos = (int)Math.Round(samplePos, 0);

                ProtocolAnalyzerDataSegment newSegment = new ProtocolAnalyzerDataSegment();
                newSegment.Value = "0x" + value.ToString("X2") + "-'" + Encoding.ASCII.GetString(new byte[] { value }) + "'";
                newSegment.FirstSample = startPos;
                newSegment.LastSample = endPos;
                string errors = "";

                if (parityError)
                    errors += "P";
                if(frameError) 
                    errors += "F";

                if (errors != "")
                    newSegment.Value += "  <" + errors + ">";

                segments.Add(newSegment);

                pos = endPos; 
            }

            ProtocolAnalyzedChannel aChannel = new ProtocolAnalyzedChannel(channel.SignalName, channel.ChannelIndex, renderer, segments.ToArray(), Colors.White, channel.SignalName == "TX" ? Color.FromUInt32(0x7f006400) : Color.FromUInt32(0x7f8b0000));

            return aChannel;
        }

        public override bool ValidateSettings(ProtocolAnalyzerSettingValue[] SelectedSettings, ProtocolAnalyzerSelectedChannel[] SelectedChannels)
        {
            if (SelectedSettings == null || SelectedSettings.Length == 0)
                return false;

            if (SelectedChannels == null || SelectedChannels.Length == 0)
                return false;

            foreach (var setting in SelectedSettings)
                if (setting.Value == null)
                    return false;

            return true;
        }
    }
}