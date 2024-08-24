using SigrokDecoderBridge;
using System;
using System.Collections.Generic;
using System.Linq;
using System.Text;
using System.Threading.Tasks;

namespace LogicAnalyzer.SigrokDecoderBridge
{
    public class SigrokDecodingTree
    {
        public List<SigrokDecodingBranch> Branches { get; } = new List<SigrokDecodingBranch>();
    }

    public class SigrokDecodingBranch
    {
        public required string Name { get; set; }
        public required SigrokDecoderBase Decoder { get; set; }
        public required SigrokOptionValue[] Options { get; set; }
        public required SigrokSelectedChannel[] Channels { get; set; }
        public List<SigrokDecodingBranch> Children { get; } = new List<SigrokDecodingBranch>();

    }
}
