using System;
using System.Collections.Generic;
using System.Linq;
using System.Text;
using System.Threading.Tasks;

namespace LogicAnalyzer.Interfaces
{
    internal interface IMarkerDisplay
    {
        int? UserMarker { get; }
        void SetUserMarker(int? Marker);
    }
}
