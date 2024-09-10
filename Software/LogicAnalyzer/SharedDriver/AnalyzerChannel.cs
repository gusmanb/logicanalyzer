using System;
using System.Collections.Generic;
using System.Drawing;
using System.Linq;
using System.Text;
using System.Threading.Tasks;

namespace SharedDriver
{
    public class AnalyzerChannel
    {
        public string TextualChannelNumber { get { return $"Channel {ChannelNumber + 1}"; } }
        public int ChannelNumber { get; set; }
        public string ChannelName { get; set; } = "";
        public uint? ChannelColor { get; set; }
        public bool Hidden { get; set; }
        public byte[]? Samples { get; set; }

        public override string ToString()
        {
            return ChannelName ?? TextualChannelNumber;
        }

        public AnalyzerChannel Clone()
        {
            var newInst = (AnalyzerChannel)MemberwiseClone();
            newInst.Samples = Samples?.ToArray();
            return newInst;
        }
    }
}
