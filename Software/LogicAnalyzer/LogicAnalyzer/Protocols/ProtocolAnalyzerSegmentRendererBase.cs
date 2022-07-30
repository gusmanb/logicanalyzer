using Avalonia;
using Avalonia.Media;
using System;
using System.Collections.Generic;
using System.Linq;
using System.Text;
using System.Threading.Tasks;

namespace LogicAnalyzer.Protocols
{
    public abstract class ProtocolAnalyzerSegmentRendererBase
    {
        public abstract void RenderSegment(ProtocolAnalyzedChannel Channel, ProtocolAnalyzerDataSegment Segment, DrawingContext Context, Rect RenderArea);
    }
}
