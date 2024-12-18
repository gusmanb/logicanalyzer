using Avalonia.Media;
using LogicAnalyzer.Protocols;
using Newtonsoft.Json.Linq;
using System.Net.Http.Headers;
using System.Text;
using static System.Runtime.InteropServices.JavaScript.JSType;

namespace USBProtocolAnalyzer
{
    public class USBAnalyzer : ProtocolAnalyzerBase
    {
        private SimpleSegmentRenderer renderer = new SimpleSegmentRenderer();

        static List<char> SYNC_BITS = new List<char> { 'K', 'J', 'K', 'J', 'K', 'J', 'K', 'K' };
        static List<char> EOP_BITS = new List<char> { '0', '0' };


        // the below data corresponds to entire 8 bits of PID i.e PID(0:3) + PID inverted bits(4:7s).
        enum PID
        {
            OUT = 0b11100001, IN = 0b01101001, SOF = 0b10100101, SETUP = 0b00101101,
            DATA0 = 0b11000011, DATA1 = 0b01001011, DATA2 = 0b10000111, MDATA = 0b00001111,
            ACK = 0b11010010, NAK = 0b01011010, STALL = 0b00011110, NYET = 0b10010110,
            ERR = 0b00111100, SPLIT = 0b01111000, PING = 0b10110100,
            RESERVED = 0b11110000
        }

        // again, this is considering the last two bits of full pid (original + inverted). 
        enum PACKET_TYPE
        {
            SPECIAL,
            TOKEN,
            HANDSHAKE,
            DATA
        }

        static int PID_SIZE = 8;
        static int TOKEN_CRC_SIZE = 5;
        static int DATA_CRC_SIZE = 16;
        static int ADDR_SIZE = 7;
        static int ENDP_SIZE = 4;
        static int FRAME_NO_SIZE = 11;
        public override string ProtocolName
        {
            get
            {
                return "USB";
            }
        }

        static ProtocolAnalyzerSetting[] settings = new ProtocolAnalyzerSetting[]
        {
            new ProtocolAnalyzerSetting
            {
                Caption = "Speed",
                ListValues = new string[]{"Low Speed", "Full speed"},
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
                Required = true,
                SignalName = "D+"
            },
            new ProtocolAnalyzerSignal
            {
                Required = true,
                SignalName = "D-"
            }
        };
        public override ProtocolAnalyzerSignal[] Signals
        {
            get
            {
                return signals;
            }
        }

        public override bool ValidateSettings(ProtocolAnalyzerSettingValue[] SelectedSettings, ProtocolAnalyzerSelectedChannel[] SelectedChannels)
        {
            if (SelectedChannels == null || SelectedChannels.Length != 2)
                return false;

            var setSpeed = SelectedSettings.Where(s => s.SettingIndex == 0).FirstOrDefault();

            if (setSpeed == null)
                return false;

            return true;
        }

        public override ProtocolAnalyzedChannel[] Analyze(int SamplingRate, int TriggerSample, ProtocolAnalyzerSettingValue[] SelectedSettings, ProtocolAnalyzerSelectedChannel[] SelectedChannels)
        {
            var D_Plus_Channel = SelectedChannels.Where(c => c.SignalName == "D+").FirstOrDefault();
            var D_Minus_Channel = SelectedChannels.Where(c => c.SignalName == "D-").FirstOrDefault();

            bool isFullSpeed = SelectedSettings[0].Value.ToString() == "Full speed" ? true : false;
            int samplesPerBit = getSamplesPerBit(SamplingRate, isFullSpeed);

            int D_Plus_FirstTransitionSample = getFirstTransitionSampleOfChannel(D_Plus_Channel);
            int D_Minus_FirstTransitionSample = getFirstTransitionSampleOfChannel(D_Minus_Channel);


            List<BitRange> D_Plus_bits, D_Minus_bits;

            Tuple<List<BitRange>, List<BitRange>> BitChannels;

            // D_plus_channel is consiered primary, since decoded packet data is overlayed on that channel
            BitChannels = ConvertToBitArray(D_Plus_Channel, D_Minus_Channel, samplesPerBit, D_Plus_FirstTransitionSample);
            D_Plus_bits = BitChannels.Item1;
            D_Minus_bits = BitChannels.Item2;

            List<ProtocolAnalyzedChannel> results = new List<ProtocolAnalyzedChannel>();

            List<ProtocolAnalyzerDataSegment> Decoded_Packet_segments = new List<ProtocolAnalyzerDataSegment>();
            List<PacketRange> Packet_segments = new List<PacketRange>();

            List<ProtocolAnalyzerDataSegment> D_Minus_segments = new List<ProtocolAnalyzerDataSegment>();

            List<BitRange> SymbolizedData = SymbolizeDiffPair(D_Plus_bits, D_Minus_bits, isFullSpeed);

            //for (int i = 0; i < SymbolizedData.Count; i++)
            //{
            //    D_Minus_segments.Add(new ProtocolAnalyzerDataSegment { FirstSample = SymbolizedData[i].FirstSample, LastSample = SymbolizedData[i].LastSample, Value = (SymbolizedData[i].Value).ToString() });
            //}

            Packet_segments = PacketFinder(SymbolizedData);

            for (int i = 0; i < Packet_segments.Count; i++)
            {
                D_Minus_segments.Add(new ProtocolAnalyzerDataSegment
                {
                    FirstSample = SymbolizedData[Packet_segments[i].FirstSample].FirstSample,
                    LastSample = SymbolizedData[Packet_segments[i].LastSample].LastSample,
                    Value = "Packet no: " + i.ToString(),
                });
            }

            for (int i = 0; i < Packet_segments.Count; i++)
            {
                Decoded_Packet_segments.AddRange(PacketDecoder(Packet_segments[i], SymbolizedData));
            }

            var D_Minus_result = new ProtocolAnalyzedChannel(D_Minus_Channel.SignalName, D_Minus_Channel.ChannelIndex, renderer, D_Minus_segments.ToArray(), Colors.White, Color.FromArgb(90, Colors.Blue.R, Colors.Blue.G, Colors.Blue.B));
            var D_Plus_result = new ProtocolAnalyzedChannel(D_Plus_Channel.SignalName, D_Plus_Channel.ChannelIndex, renderer, Decoded_Packet_segments.ToArray(), Colors.White, Color.FromArgb(90, Colors.Blue.R, Colors.Blue.G, Colors.Blue.B));

            results.Add(D_Minus_result);
            results.Add(D_Plus_result);

            return results.ToArray();
        }

        private List<ProtocolAnalyzerDataSegment> PacketDecoder(PacketRange Packet, List<BitRange> SymbolizedData)
        {
            List<ProtocolAnalyzerDataSegment> DecodedSegments = new List<ProtocolAnalyzerDataSegment>();

            // adding SYNC segment. 
            DecodedSegments.Add(new ProtocolAnalyzerDataSegment
            {
                FirstSample = SymbolizedData[Packet.FirstSample].FirstSample,
                LastSample = SymbolizedData[Packet.FirstSample + (SYNC_BITS.Count - 1)].LastSample,
                Value = "SYNC"
            });

            // adding PID segment
            int PID_START = Packet.FirstSample + SYNC_BITS.Count;
            int PID_END = Packet.FirstSample + SYNC_BITS.Count + PID_SIZE - 1;

            PID packet_PID = (PID)Decode_NRZI(SymbolizedData, PID_START, PID_END);
            DecodedSegments.Add(new ProtocolAnalyzerDataSegment
            {
                FirstSample = SymbolizedData[PID_START].FirstSample,
                LastSample = SymbolizedData[PID_END].LastSample,
                Value = packet_PID.ToString()
            });

            // adding CRC segments.

            PACKET_TYPE packetType = (PACKET_TYPE)((int)packet_PID & 0b11);

            int CRC_START = 0;
            int CRC_END = Packet.LastSample - EOP_BITS.Count;

            if (packetType == PACKET_TYPE.TOKEN || packetType == PACKET_TYPE.DATA)
            {

                CRC_START = packetType == PACKET_TYPE.TOKEN ?
                            Packet.LastSample - (EOP_BITS.Count + TOKEN_CRC_SIZE - 1) :
                            Packet.LastSample - (EOP_BITS.Count + DATA_CRC_SIZE - 1);

                uint CRC_DATA = Decode_NRZI(SymbolizedData, CRC_START, CRC_END);

                DecodedSegments.Add(new ProtocolAnalyzerDataSegment
                {
                    FirstSample = SymbolizedData[CRC_START].FirstSample,
                    LastSample = SymbolizedData[CRC_END].LastSample,
                    Value = "CRC - 0x" + CRC_DATA.ToString("X")
                });
            }

            // adding DATA segment.

            if (packetType == PACKET_TYPE.DATA)
            {
                uint Data = Decode_NRZI(SymbolizedData, PID_END + 1, CRC_START - 1);
                DecodedSegments.Add(new ProtocolAnalyzerDataSegment
                {
                    FirstSample = SymbolizedData[PID_END + 1].FirstSample,
                    LastSample = SymbolizedData[CRC_START - 1].LastSample,
                    Value = "DATA - 0x" + Data.ToString("X")
                });
            }

            // adding SOF Frame segment

            if (packet_PID == PID.SOF)
            {
                int FRAME_NO_START = PID_END + 1;
                int FRAME_NO_END = PID_END + FRAME_NO_SIZE;
                uint FRAME_NO_DATA = Decode_NRZI(SymbolizedData, FRAME_NO_START, FRAME_NO_END);

                DecodedSegments.Add(new ProtocolAnalyzerDataSegment
                {
                    FirstSample = SymbolizedData[FRAME_NO_START].FirstSample,
                    LastSample = SymbolizedData[FRAME_NO_END].LastSample,
                    Value = "FRAME NO - 0x" + FRAME_NO_DATA.ToString("X")
                });
            }

            // adding Token Segment.

            if (packetType == PACKET_TYPE.TOKEN && packet_PID != PID.SOF)
            {
                int ADDR_START = PID_END + 1;
                int ADDR_END = PID_END + ADDR_SIZE;
                uint ADDR_DATA = Decode_NRZI(SymbolizedData, ADDR_START, ADDR_END);

                DecodedSegments.Add(new ProtocolAnalyzerDataSegment
                {
                    FirstSample = SymbolizedData[ADDR_START].FirstSample,
                    LastSample = SymbolizedData[ADDR_END].LastSample,
                    Value = "ADDR - 0x" + ADDR_DATA.ToString("X")
                });

                int ENDP_START = ADDR_END + 1;
                int ENDP_END = ADDR_END + ENDP_SIZE;
                uint ENDP_DATA = Decode_NRZI(SymbolizedData, ENDP_START, ENDP_END);

                DecodedSegments.Add(new ProtocolAnalyzerDataSegment
                {
                    FirstSample = SymbolizedData[ENDP_START].FirstSample,
                    LastSample = SymbolizedData[ENDP_END].LastSample,
                    Value = "ENDP - 0x" + ENDP_DATA.ToString("X")
                });
            }

            // adding EOP segment.
            DecodedSegments.Add(new ProtocolAnalyzerDataSegment
            {
                FirstSample = SymbolizedData[Packet.LastSample - (EOP_BITS.Count - 1)].FirstSample,
                LastSample = SymbolizedData[Packet.LastSample].LastSample,
                Value = "EOP"
            });

            return DecodedSegments;
        }

        private uint Decode_NRZI(List<BitRange> SymbolizedData, int start, int end)
        {
            uint data = 0;
            int pow = 0;

            for (int i = start; i <= end; i++)
            {
                if (SymbolizedData[i].Value == SymbolizedData[i - 1].Value)
                {
                    data += ((uint)1 << pow);
                }
                pow++;
            }

            return data;
        }

        private List<PacketRange> PacketFinder(List<BitRange> symbolizedData)
        {
            List<int> SOF_Samples = new List<int>();
            List<int> EOP_Samples = new List<int>();

            int i = 0;

            List<PacketRange> packets = new List<PacketRange>();

            SOF_Samples = matchBitPattern(symbolizedData, SYNC_BITS);
            EOP_Samples = matchBitPattern(symbolizedData, EOP_BITS);


            // below code is written such that SOF packets between a pair of SOF and EOP packets are ignored.
            for (int j = 0; j < EOP_Samples.Count; j++)
            {

                packets.Add(new PacketRange
                {
                    FirstSample = SOF_Samples[i],
                    LastSample = EOP_Samples[j] + 1,
                    Value = j.ToString()[0]
                });

                while (symbolizedData[SOF_Samples[i]].FirstSample < symbolizedData[EOP_Samples[j] + 1].LastSample)
                {
                    i++;
                    if (i == SOF_Samples.Count) break;
                }

                if (i == SOF_Samples.Count) break;
            }

            return packets;
        }
        private int getFirstTransitionSampleOfChannel(ProtocolAnalyzerSelectedChannel inChannel)
        {
            int transitionSample = 0;

            for (int i = 1; i < inChannel.Samples.Length; i++)
            {
                if (inChannel.Samples[i] != inChannel.Samples[i - 1])
                {
                    transitionSample = i;
                    break;
                }
            }

            return transitionSample;
        }

        private Tuple<List<BitRange>, List<BitRange>> ConvertToBitArray(ProtocolAnalyzerSelectedChannel primaryChannel, ProtocolAnalyzerSelectedChannel secondaryChannel, int samplesPerBit, int startSample)
        {
            List<BitRange> PrimarybitChannel = new List<BitRange>();
            List<BitRange> SecondarybitChannel = new List<BitRange>();

            List<BitRange> transistionChannel = new List<BitRange>();

            int lastTransition = startSample, bitMidSample = 0;
            decimal transitionLength = 0;
            decimal estimatedCycles = 0;

            // to find the position of each transition
            for (int i = 1; i < primaryChannel.Samples.Length; i++)
            {
                if (primaryChannel.Samples[i] != primaryChannel.Samples[i - 1])
                {
                    transistionChannel.Add(new BitRange
                    {
                        FirstSample = lastTransition,
                        LastSample = i - 1,
                        Value = ((primaryChannel.Samples[i - 1]).ToString())[0]
                    });
                    lastTransition = i;
                }
            }

            // Guessing no of bits between each transition 
            for (int i = 0; i < transistionChannel.Count; i++)
            {
                transitionLength = transistionChannel[i].LastSample - transistionChannel[i].FirstSample;
                estimatedCycles = transitionLength / samplesPerBit;

                if (estimatedCycles * 10 < 5) continue;    // to avoid tranisition periods less than 10% of expected period.  

                estimatedCycles = Math.Round(estimatedCycles, MidpointRounding.ToEven);

                lastTransition = transistionChannel[i].FirstSample;
                while (estimatedCycles > 1)
                {
                    PrimarybitChannel.Add(new BitRange { FirstSample = lastTransition, LastSample = lastTransition + samplesPerBit - 1, Value = transistionChannel[i].Value });
                    lastTransition = lastTransition + samplesPerBit;
                    estimatedCycles--;
                }

                PrimarybitChannel.Add(new BitRange { FirstSample = lastTransition, LastSample = transistionChannel[i].LastSample, Value = transistionChannel[i].Value });
            }

            // Ideally, both the D+ and D- channel should be perfectly aligned.
            // But due to sampling descrepancies, there could be instances where both the channels aren't aligned properly.  
            // We designate one channel as the primary and extract data from the secondary channel at the sample corresponding to the center of the samples in the primary channel.
            for (int i = 0; i < PrimarybitChannel.Count; i++)
            {
                bitMidSample = (PrimarybitChannel[i].FirstSample + PrimarybitChannel[i].LastSample) / 2;
                SecondarybitChannel.Add(new BitRange
                {
                    FirstSample = PrimarybitChannel[i].FirstSample,
                    LastSample = PrimarybitChannel[i].LastSample,
                    Value = (secondaryChannel.Samples[bitMidSample].ToString())[0]
                });
            }

            return Tuple.Create(PrimarybitChannel, SecondarybitChannel);
        }

        private int getSamplesPerBit(int SamplingRate, bool isFullSpeed)
        {
            int FullSpeed = 12000000;
            int LowSpeed = 1500000;

            int USBSpeed = isFullSpeed ? FullSpeed : LowSpeed;

            int SampleCount = SamplingRate / USBSpeed;

            return SampleCount;
        }

        private List<BitRange> SymbolizeDiffPair(List<BitRange> D_Plus_Channel, List<BitRange> D_Minus_Channel, bool isFullSpeed)
        {
            List<BitRange> symbols = new List<BitRange>();
            int DP_bit, DM_bit;
            BitRange symbolizedBit = new BitRange();

            int runSize = Math.Min(D_Plus_Channel.Count, D_Minus_Channel.Count);

            for (int i = 0; i < runSize; i++)
            {
                DP_bit = D_Plus_Channel[i].Value - '0';
                DM_bit = D_Minus_Channel[i].Value - '0';

                // assuming we are using D+ channel to show packet segments

                symbolizedBit = new BitRange();
                symbolizedBit.FirstSample = D_Plus_Channel[i].FirstSample;
                symbolizedBit.LastSample = D_Plus_Channel[i].LastSample;

                if ((DP_bit ^ DM_bit) == 1)     // differential pair
                {
                    if (isFullSpeed) symbolizedBit.Value = DP_bit == 1 ? 'J' : 'K';
                    else symbolizedBit.Value = DP_bit == 1 ? 'K' : 'J';
                }
                else                            // single-ended pair
                {
                    if (DP_bit == 0) symbolizedBit.Value = '0';
                    else symbolizedBit.Value = '1';
                }

                symbols.Add(symbolizedBit);
            }

            return symbols;
        }

        //below two functions are used for pattern matching. they are something called boyre-moore algorithm

        static int NO_OF_CHARS = 256;
        private void badCharHeuristic(List<char> str, int size, int[] badchar)
        {
            int i;
            // Initialize all occurrences as -1
            for (i = 0; i < NO_OF_CHARS; i++)
            {
                badchar[i] = -1;
            }

            // Fill the actual value of last occurrence
            // of a character
            for (i = 0; i < size; i++)
            {
                badchar[(int)str[i]] = i;
            }
        }

        private List<int> matchBitPattern(List<BitRange> txt, List<char> pat)
        {
            int m = pat.Count;
            int n = txt.Count;
            List<int> matchingIndices = new List<int>();

            int[] badchar = new int[NO_OF_CHARS];

            badCharHeuristic(pat, m, badchar);

            int s = 0;
            while (s <= (n - m))
            {
                int j = m - 1;

                while (j >= 0 && pat[j] == txt[s + j].Value)
                {
                    j--;
                }

                if (j < 0)
                {
                    matchingIndices.Add(s);
                    s += (s + m < n) ? m - badchar[txt[s + m].Value] : 1;
                }

                else
                {
                    s += Math.Max(1, j - badchar[txt[s + j].Value]);
                }
            }
            return matchingIndices;
        }

        class BitRange
        {
            public int FirstSample { get; set; }
            public int LastSample { get; set; }
            public char Value { get; set; }

            public int Length { get { return LastSample - FirstSample; } }
        }

        class PacketRange : BitRange { };
    }
}
