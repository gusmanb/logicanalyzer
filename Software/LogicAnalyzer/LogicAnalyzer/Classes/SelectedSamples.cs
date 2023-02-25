using System;
using System.Collections.Generic;
using System.Linq;
using System.Text;
using System.Threading.Tasks;

namespace LogicAnalyzer.Classes
{
    public class SelectedSamples
    {
        public int FirstSample { get; set; }
        public int LastSample { get; set; }
        public int Start { get { return Math.Min(FirstSample, LastSample); } }
        public int End { get { return Math.Max(FirstSample, LastSample); } }
        public int SampleCount { get { return Math.Abs(LastSample - FirstSample); } }
    }
}
