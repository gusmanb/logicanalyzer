using SigrokDecoderBridge;
using System;
using System.Collections.Generic;
using System.Linq;
using System.Text;
using System.Threading.Tasks;

namespace LogicAnalyzer.Classes
{
    public class AnalysisSettings
    {
        public SigrokDecoderBase? Analyzer { get; set; }
        public SigrokSelectedChannel[]? Channels { get; set; }
        public SigrokOptionValue[]? Settings { get; set; }
    }
}
