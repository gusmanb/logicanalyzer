using LogicAnalyzer.Protocols;
using System;
using System.Collections.Generic;
using System.Linq;
using System.Text;
using System.Threading.Tasks;

namespace LogicAnalyzer.Classes
{
    public class AnalysisSettings
    {
        public ProtocolAnalyzerBase? Analyzer { get; set; }
        public ProtocolAnalyzerSelectedChannel[]? Channels { get; set; }
        public ProtocolAnalyzerSettingValue[]? Settings { get; set; }
    }
}
