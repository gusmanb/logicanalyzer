using Avalonia;
using Avalonia.Controls.Shapes;
using Avalonia.Media;
using LogicAnalyzer.Classes;
using System;
using System.Collections;
using System.Collections.Generic;
using System.Globalization;
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
            FormattedText text = new FormattedText(Segment.Value, segmentFont, 12, TextAlignment.Left, TextWrapping.NoWrap, Size.Infinity);

            double midY = RenderArea.Y + (RenderArea.Height / 2.0);
            double rectHeight = text.Bounds.Height + 10;
            double topY = midY - (rectHeight / 2.0);
            double bottomY = midY + (rectHeight / 2.0);
            double minWidth = text.Bounds.Width + 10.0;

            PathFigure container = new PathFigure();
            container.StartPoint = new Point(RenderArea.X, midY);
            container.Segments.Add(new LineSegment { Point = new Point(RenderArea.X + 5, topY) });
            container.Segments.Add(new LineSegment { Point = new Point(RenderArea.X + RenderArea.Width - 5, topY) });
            container.Segments.Add(new LineSegment { Point = new Point(RenderArea.X + RenderArea.Width, midY) });
            container.Segments.Add(new LineSegment { Point = new Point(RenderArea.X + RenderArea.Width - 5, bottomY) });
            container.Segments.Add(new LineSegment { Point = new Point(RenderArea.X + 5, bottomY) });
            container.Segments.Add(new LineSegment { Point = new Point(RenderArea.X, midY) });
            container.IsClosed = true;

            PathGeometry gContainer = new PathGeometry();
            gContainer.Figures.Add(container);

            G.DrawGeometry(GraphicObjectsCache.GetBrush(Channel.BackColor), GraphicObjectsCache.GetPen(Channel.ForeColor, 1), gContainer);

            if (RenderArea.Width < minWidth)
                return;

            G.DrawText(GraphicObjectsCache.GetBrush(Channel.ForeColor), new Point(RenderArea.X + (RenderArea.Width / 2 - text.Bounds.Width / 2), RenderArea.Y + (RenderArea.Height / 2 - text.Bounds.Height / 2)), text);
        }
    }
}
