using Avalonia;
using Avalonia.Media;
using LogicAnalyzer.Classes;
using System;
using System.Collections.Generic;
using System.Linq;
using System.Text;
using System.Threading.Tasks;

namespace LogicAnalyzer.Protocols
{
    public class SimpleSegmentRenderer : ProtocolAnalyzerSegmentRendererBase
    {
        static Typeface segmentFont = new Typeface("Segoe UI");

        public override void RenderSegment(ProtocolAnalyzedChannel Channel, ProtocolAnalyzerDataSegment Segment, DrawingContext G, Rect RenderArea)
        {
            G.FillRectangle(GraphicObjectsCache.GetBrush(Channel.BackColor), RenderArea);
            G.DrawRectangle(GraphicObjectsCache.GetPen(Channel.ForeColor, 1), RenderArea);
            FormattedText text = new FormattedText(Segment.Value, segmentFont, 12, TextAlignment.Center, TextWrapping.NoWrap, Size.Infinity);
            G.DrawText(GraphicObjectsCache.GetBrush(Channel.ForeColor), new Point(RenderArea.X + (RenderArea.Width / 2 - text.Bounds.Width / 2), RenderArea.Y + (RenderArea.Height / 2 - text.Bounds.Height / 2)), text);
        }
    }
}
