using Avalonia;
using Avalonia.Controls;
using Avalonia.Markup.Xaml;
using Avalonia.Media;
using Avalonia.Platform;
using Avalonia.Threading;
using AvaloniaEdit.Document;
using AvaloniaEdit.Utils;
using LogicAnalyzer.Classes;
using LogicAnalyzer.Interfaces;
using SigrokDecoderBridge;
using System;
using System.Collections.Generic;
using System.Diagnostics;
using System.Globalization;
using System.Linq;

namespace LogicAnalyzer.Controls
{

    public partial class AnnotationViewer : UserControl, ISampleDisplay, IMarkerDisplay, IRegionDisplay
    {

        List<AnnotationsGroup> annotations = new List<AnnotationsGroup>();
        bool isUpdating = false;

        const int ANNOTATION_HEIGHT = 24;
        const int ANNOTATION_NAME_WIDTH = 150;

        public int VisibleSamples { get; private set; }

        public int FirstSample { get; private set; }

        public int? UserMarker { get; private set; }

        AnnotationRenderer renderer = new AnnotationRenderer();

        List<SampleRegion> regions = new List<SampleRegion>();

        public SampleRegion[] Regions { get { return regions.ToArray(); } }

        public AnnotationViewer()
        {
            InitializeComponent();
        }
        public void BeginUpdate()
        {
            isUpdating = true;
        }
        public void EndUpdate()
        {
            isUpdating = false;
            this.InvalidateVisual();
        }
        private void Update()
        {
            if (isUpdating)
                return;

            var height = annotations.Count * ANNOTATION_HEIGHT;

            if (this.Height != height)
                this.Height = height;

            this.InvalidateVisual();
        }

        public override void Render(DrawingContext context)
        {
            var height = annotations.Sum(a => a.Annotations.Length) * ANNOTATION_HEIGHT;

            if (this.Height != height)
            {
                Dispatcher.UIThread.Post(() => this.Height = height);
            }

            var rectContainerName = new Rect(0, 0, ANNOTATION_NAME_WIDTH, this.Bounds.Height);
            var rectContainerData = new Rect(ANNOTATION_NAME_WIDTH, 0, this.Bounds.Width - ANNOTATION_NAME_WIDTH, this.Bounds.Height);

            context.FillRectangle(GraphicObjectsCache.GetBrush(AnalyzerColors.BgChannelColors[1]), rectContainerName);
            context.FillRectangle(GraphicObjectsCache.GetBrush(AnalyzerColors.BgChannelColors[0]), rectContainerData);


            var ratio = (double)((this.Bounds.Width - ANNOTATION_NAME_WIDTH) - 2) / (double)VisibleSamples;

            var regionsInRange = regions.Where(r => r.LastSample >= FirstSample && r.FirstSample <= FirstSample + VisibleSamples - 1).ToArray();

            foreach (var region in regionsInRange)
            {
                var xStart = (region.FirstSample - FirstSample) * ratio + ANNOTATION_NAME_WIDTH;
                var xEnd = (region.LastSample - FirstSample) * ratio + ANNOTATION_NAME_WIDTH;

                var rect = new Rect(xStart, 0, xEnd - xStart, this.Bounds.Height);
                context.FillRectangle(GraphicObjectsCache.GetBrush(region.RegionColor), rect);
            }


            context.DrawRectangle(null, GraphicObjectsCache.GetPen(Colors.Black, 1), rectContainerName);
            context.DrawRectangle(null, GraphicObjectsCache.GetPen(Colors.Black, 1), rectContainerData);


            int annNum = 0;

            foreach (var grp in annotations)
            {
                for (int buc = 0; buc < grp.Annotations.Length; buc++)
                {
                    var annotation = grp.Annotations[buc];

                    var y = annNum++ * ANNOTATION_HEIGHT;

                    var rectName = new Rect(1, y + 1, ANNOTATION_NAME_WIDTH - 2, ANNOTATION_HEIGHT - 2);
                    var rectData = new Rect(ANNOTATION_NAME_WIDTH + 1, y + 1, (this.Bounds.Width - ANNOTATION_NAME_WIDTH) - 2, ANNOTATION_HEIGHT - 2);
                    renderer.RenderAnnotation(grp.GroupColor, annotation, FirstSample, VisibleSamples, rectName, rectData, context);
                }
            }
            if (UserMarker != null)
            {
                
                double lineX = (UserMarker.Value - FirstSample) * ratio + ANNOTATION_NAME_WIDTH + 1;
                context.DrawLine(GraphicObjectsCache.GetPen(AnalyzerColors.UserLineColor, 2, DashStyle.DashDot), new Point(lineX, 0), new Point(lineX, this.Bounds.Height));
            }

            

            base.Render(context);
        }

        public void AddAnnotationsGroup(AnnotationsGroup Group)
        {
            annotations.Add(Group);
            Update();
        }

        public void ClearAnnotations()
        {
            annotations.Clear();
            Update();
        }





        public void AddRegion(SampleRegion Region)
        {
            regions.Add(Region);
            this.InvalidateVisual();
        }
        public void AddRegions(IEnumerable<SampleRegion> Regions)
        {
            regions.AddRange(Regions);
            this.InvalidateVisual();
        }
        public bool RemoveRegion(SampleRegion Region)
        {
            var res = regions.Remove(Region);

            if (res)
                this.InvalidateVisual();

            return res;
        }
        public void ClearRegions()
        {
            regions.Clear();
            this.InvalidateVisual();
        }


        public void UpdateVisibleSamples(int FirstSample, int VisibleSamples)
        {
            this.FirstSample = FirstSample;
            this.VisibleSamples = VisibleSamples;

            if(!isUpdating)
                this.InvalidateVisual();
        }

        public void SetUserMarker(int? UserMarker)
        {
            this.UserMarker = UserMarker;

            if (!isUpdating)
                this.InvalidateVisual();
        }

        class AnnotationRenderer
        {
            

            internal void RenderAnnotation(Color GroupColor, SigrokAnnotation annotation, int firstSample, int inScreen, Rect rectName, Rect rectData, DrawingContext context)
            {
                var lastSample = firstSample + inScreen - 1;
                var segments = annotation.Segments.Where(s => s.LastSample >= firstSample && s.FirstSample <= lastSample).ToArray();

                using (context.PushClip(rectName))
                {

                    context.DrawEllipse(GraphicObjectsCache.GetBrush(GroupColor), GraphicObjectsCache.GetPen(Colors.Black, 1), new Point(rectName.X + 8, rectName.Y + rectName.Height / 2), 8, 8);

                    var text = new FormattedText(annotation.AnnotationName, System.Globalization.CultureInfo.InvariantCulture, FlowDirection.LeftToRight, new Typeface("Segoe UI"), 12, Brushes.White);

                    rectName = new Rect(rectName.X + 17, rectName.Y, rectName.Width - 17, rectName.Height);

                    var x = rectName.X + (rectName.Width - text.Width) / 2;
                    var y = rectName.Y + (rectName.Height - text.Height) / 2;
                    context.DrawText(text, new Point(x, y));
                }
                using (context.PushClip(rectData))
                {
                    foreach (var segment in segments)
                    {
                        var xStart = (segment.FirstSample - firstSample) * rectData.Width / inScreen;
                        var xEnd = (segment.LastSample - firstSample) * rectData.Width / inScreen;

                        int samples = segment.LastSample - segment.FirstSample;

                        Rect rc;

                        if (samples < 2)
                        {
                            segment.Shape = ProtocolAnalyzerSegmentShape.Circle;
                            rc = new Rect(rectData.X + xStart, rectData.Y, rectData.Height, rectData.Height);
                        }
                        else
                        {
                            rc = new Rect(rectData.X + xStart, rectData.Y, xEnd - xStart, rectData.Height);

                            if(rc.Width < 20)
                                segment.Shape = ProtocolAnalyzerSegmentShape.RoundRectangle;
                            else
                                segment.Shape = ProtocolAnalyzerSegmentShape.Hexagon;
                        }

                        RenderSegment(segment, context, rc);
                    }
                }
            }

            internal void RenderSegment(SigrokAnnotationSegment Segment, DrawingContext G, Rect RenderArea)
            {

                var color = AnalyzerColors.AnnColors[Segment.TypeId % 64];
                var textColor = color.FindContrast();

                double midY = RenderArea.Y + (RenderArea.Height / 2.0);
                double rectHeight = RenderArea.Height - 2;
                double topY = RenderArea.Y + 1;
                double bottomY = topY + rectHeight;

                int margin = 0;

                switch (Segment.Shape)
                {
                    case ProtocolAnalyzerSegmentShape.Hexagon:

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

                        G.DrawGeometry(GraphicObjectsCache.GetBrush(color), GraphicObjectsCache.GetPen(Colors.Black, 1), gContainer);

                        margin = 10;

                        break;

                    case ProtocolAnalyzerSegmentShape.Rectangle:

                        G.DrawRectangle(GraphicObjectsCache.GetBrush(color), GraphicObjectsCache.GetPen(Colors.Black, 1), RenderArea);
                        margin = 2;
                        break;

                    case ProtocolAnalyzerSegmentShape.RoundRectangle:

                        G.DrawRectangle(GraphicObjectsCache.GetBrush(color), GraphicObjectsCache.GetPen(Colors.Black, 1), RenderArea, 5, 5);

                        margin = 2;

                        break;

                    case ProtocolAnalyzerSegmentShape.Circle:

                        G.DrawEllipse(GraphicObjectsCache.GetBrush(color), GraphicObjectsCache.GetPen(Colors.Black, 1), RenderArea);
                        margin = 2;

                        break;
                }

                FormattedText? text = GetBestText(RenderArea.Width - margin, Segment.Value, textColor);

                if (text == null)
                    return;

                G.DrawText(text, new Point(RenderArea.X + (RenderArea.Width / 2 - text.Width / 2), RenderArea.Y + (RenderArea.Height / 2 - text.Height / 2)));
            }

            private FormattedText? GetBestText(double AvailableWidth, string[] PossibleValues, Color TextColor)
            {
                foreach (var value in PossibleValues)
                {
                    FormattedText text = new FormattedText(value, CultureInfo.InvariantCulture, FlowDirection.LeftToRight, new Typeface("Segoe UI"), 12, GraphicObjectsCache.GetBrush(TextColor));

                    if(text.Width <= AvailableWidth)
                        return text;
                }

                return null;
            }
        }
    }
}