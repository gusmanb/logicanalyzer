using LogicAnalyzer.Classes;
using System;
using System.Collections.Generic;
using System.Linq;
using System.Text;
using System.Threading.Tasks;

namespace LogicAnalyzer.Interfaces
{
    internal interface IRegionDisplay
    {
        SampleRegion[] Regions { get; }
        void AddRegion(SampleRegion Region);
        void AddRegions(IEnumerable<SampleRegion> Regions);
        bool RemoveRegion(SampleRegion Region);
        void ClearRegions();
    }
}
