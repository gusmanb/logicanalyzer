using System;
using System.Collections.Generic;
using System.Linq;
using System.Text;
using System.Threading.Tasks;

namespace LogicAnalyzer.Interfaces
{
    internal interface ISampleDisplay
    {
        int FirstSample { get; }
        int VisibleSamples { get; }
        void UpdateVisibleSamples(int FirstSample, int VisibleSamples);
    }
}
