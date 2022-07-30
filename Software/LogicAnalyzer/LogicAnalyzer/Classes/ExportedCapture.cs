using LogicAnalyzer.Classes;
using Newtonsoft.Json;
using SharedDriver;
using System;
using System.Collections.Generic;
using System.Linq;
using System.Text;
using System.Threading.Tasks;

namespace LogicAnalyzer
{
    public class ExportedCapture
    {
        public CaptureSettings Settings { get; set; }
        public uint[] Samples { get; set; }
        public string[] ChannelTexts { get; set; }
        public SelectedSampleRegion[]? SelectedRegions { get; set; }
    }
}
