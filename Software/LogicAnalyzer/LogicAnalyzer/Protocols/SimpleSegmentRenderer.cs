using System;
using System.Collections.Generic;
using System.Linq;
using System.Text;
using System.Threading.Tasks;

namespace LogicAnalyzer.Protocols
{
    public class SimpleSegmentRenderer : ProtocolAnalyzerSegmentRendererBase
    {
        static StringFormat textFormatCenter = new StringFormat { LineAlignment = StringAlignment.Center, Alignment = StringAlignment.Center };

        static Font segmentFont = new Font("Segoe UI", 9, FontStyle.Regular);

        public override void RenderSegment(ProtocolAnalyzedChannel Channel, ProtocolAnalyzerDataSegment Segment, Graphics G, RectangleF RenderArea)
        {
            G.FillRectangle(Channel.BackBrush, RenderArea);
            G.DrawRectangle(Channel.ForePen, Rectangle.Round(RenderArea));
            G.DrawString(Segment.Value, segmentFont, Channel.ForeBrush, RenderArea, textFormatCenter);
        }
    }
}
