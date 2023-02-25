using Avalonia;
using Avalonia.Media;
using System;
using System.Collections.Generic;
using System.Linq;
using System.Text;
using System.Threading.Tasks;

namespace LogicAnalyzer.Protocols
{
    /// <summary>
    /// Base class to be implemented by segment renderers
    /// </summary>
    public abstract class ProtocolAnalyzerSegmentRendererBase
    {
        /// <summary>
        /// Function called to render an on-screen segment
        /// </summary>
        /// <param name="Channel">Analyzed channel where the data will be rendered</param>
        /// <param name="Segment">Segment to render</param>
        /// <param name="Context">Graphics context</param>
        /// <param name="RenderArea">Rectangle where the segment must be rendered</param>
        public abstract void RenderSegment(ProtocolAnalyzedChannel Channel, ProtocolAnalyzerDataSegment Segment, DrawingContext Context, Rect RenderArea);
    }
}
