using Avalonia;
using Avalonia.Controls;
using Avalonia.Markup.Xaml;
using Avalonia.Media;
using Avalonia.Platform;
using Avalonia.Threading;
using AvaloniaEdit.Document;
using LogicAnalyzer.Classes;
using LogicAnalyzer.Interfaces;
using LogicAnalyzer.Protocols;
using System;
using System.Collections.Generic;
using System.Diagnostics;
using System.Globalization;
using System.Linq;

namespace LogicAnalyzer.Controls
{

    public partial class AnnotationViewer : UserControl, ISampleDisplay, IMarkerDisplay, IRegionDisplay
    {

        List<ProtocolAnalyzedAnnotation> annotations = new List<ProtocolAnalyzedAnnotation>();
        bool isUpdating = false;

        const int ANNOTATION_HEIGHT = 32;
        const int ANNOTATION_NAME_WIDTH = 140;

        public int VisibleSamples { get; private set; }

        public int FirstSample { get; private set; }

        public int? UserMarker { get; private set; }

        AnnotationRenderer renderer = new AnnotationRenderer();

        public ProtocolAnalyzedAnnotation[] Annotations
        {
            get
            {
                return annotations.ToArray();
            }
        }

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
            var height = annotations.Count * ANNOTATION_HEIGHT;

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


            for (int buc = 0; buc < annotations.Count; buc++)
            {
                var annotation = annotations[buc];

                var y = buc * ANNOTATION_HEIGHT;

                var rectName = new Rect(1, y + 1, ANNOTATION_NAME_WIDTH - 2, ANNOTATION_HEIGHT - 2);
                var rectData = new Rect(ANNOTATION_NAME_WIDTH + 1, y + 1, (this.Bounds.Width - ANNOTATION_NAME_WIDTH) - 2, ANNOTATION_HEIGHT - 2);
                renderer.RenderAnnotation(annotation, FirstSample, VisibleSamples, rectName, rectData, context);
            }
            
            if (UserMarker != null)
            {
                
                double lineX = (UserMarker.Value - FirstSample) * ratio + ANNOTATION_NAME_WIDTH + 1;
                context.DrawLine(GraphicObjectsCache.GetPen(AnalyzerColors.UserLineColor, 2, DashStyle.DashDot), new Point(lineX, 0), new Point(lineX, this.Bounds.Height));
            }

            

            base.Render(context);
        }

        public void AddAnnotation(ProtocolAnalyzedAnnotation Annotation)
        {
            annotations.Add(Annotation);
            Update();
        }
        public void AddAnnotations(IEnumerable<ProtocolAnalyzedAnnotation> Annotations)
        {
            annotations.AddRange(Annotations);
            Update();
        }
        public bool RemoveAnnotation(ProtocolAnalyzedAnnotation Annotation)
        {
            var res = annotations.Remove(Annotation);
            Update();
            return res;
        }
        public void ClearAnnotation()
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
            static Color[] itemPalette = new Color[]
            {
            Color.FromArgb(255, 255, 69, 0),    // OrangeRed
            Color.FromArgb(255, 50, 205, 50),   // LimeGreen
            Color.FromArgb(255, 0, 191, 255),   // DeepSkyBlue
            Color.FromArgb(255, 255, 20, 147),  // DeepPink
            Color.FromArgb(255, 238, 130, 238), // Violet
            Color.FromArgb(255, 255, 215, 0),   // Gold
            Color.FromArgb(255, 72, 61, 139),   // DarkSlateBlue
            Color.FromArgb(255, 32, 178, 170),  // LightSeaGreen
            Color.FromArgb(255, 218, 112, 214), // Orchid
            Color.FromArgb(255, 60, 179, 113),  // MediumSeaGreen
            Color.FromArgb(255, 240, 128, 128), // LightCoral
            Color.FromArgb(255, 70, 130, 180),  // SteelBlue
            Color.FromArgb(255, 123, 104, 238), // MediumSlateBlue
            Color.FromArgb(255, 199, 21, 133),  // MediumVioletRed
            Color.FromArgb(255, 144, 238, 144), // LightGreen
            Color.FromArgb(255, 255, 160, 122), // LightSalmon
            Color.FromArgb(255, 32, 178, 170),  // LightSeaGreen
            Color.FromArgb(255, 95, 158, 160),  // CadetBlue
            Color.FromArgb(255, 255, 69, 0),    // OrangeRed
            Color.FromArgb(255, 0, 128, 128),   // Teal
            Color.FromArgb(255, 255, 105, 180), // HotPink
            Color.FromArgb(255, 0, 206, 209),   // DarkTurquoise
            Color.FromArgb(255, 46, 139, 87),   // SeaGreen
            Color.FromArgb(255, 255, 20, 147),  // DeepPink
            Color.FromArgb(255, 255, 99, 71),   // Tomato
            Color.FromArgb(255, 0, 255, 127),   // SpringGreen
            Color.FromArgb(255, 221, 160, 221), // Plum
            Color.FromArgb(255, 176, 224, 230), // PowderBlue
            Color.FromArgb(255, 128, 128, 0),   // Olive
            Color.FromArgb(255, 255, 140, 0),   // DarkOrange
            Color.FromArgb(255, 139, 69, 19),   // SaddleBrown
            Color.FromArgb(255, 34, 139, 34),   // ForestGreen
            Color.FromArgb(255, 255, 165, 0),   // Orange
            Color.FromArgb(255, 205, 92, 92),   // IndianRed
            Color.FromArgb(255, 0, 139, 139),   // DarkCyan
            Color.FromArgb(255, 238, 232, 170), // PaleGoldenrod
            Color.FromArgb(255, 255, 127, 80),  // Coral
            Color.FromArgb(255, 186, 85, 211),  // MediumOrchid
            Color.FromArgb(255, 107, 142, 35),  // OliveDrab
            Color.FromArgb(255, 147, 112, 219), // MediumPurple
            Color.FromArgb(255, 188, 143, 143), // RosyBrown
            Color.FromArgb(255, 240, 230, 140), // Khaki
            Color.FromArgb(255, 210, 105, 30),  // Chocolate
            Color.FromArgb(255, 127, 255, 212), // Aquamarine
            Color.FromArgb(255, 255, 228, 181), // Moccasin
            Color.FromArgb(255, 154, 205, 50),  // YellowGreen
            Color.FromArgb(255, 255, 228, 225), // MistyRose
            Color.FromArgb(255, 255, 239, 213), // PapayaWhip
            Color.FromArgb(255, 139, 0, 139),   // DarkMagenta
            Color.FromArgb(255, 245, 222, 179), // Wheat
            Color.FromArgb(255, 240, 255, 240), // Honeydew
            Color.FromArgb(255, 255, 248, 220), // Cornsilk
            Color.FromArgb(255, 218, 165, 32),  // Goldenrod
            Color.FromArgb(255, 192, 192, 192), // Silver
            Color.FromArgb(255, 255, 218, 185), // PeachPuff
            Color.FromArgb(255, 238, 130, 238), // Violet
            Color.FromArgb(255, 175, 238, 238), // PaleTurquoise
            Color.FromArgb(255, 72, 61, 139),   // DarkSlateBlue
            Color.FromArgb(255, 255, 160, 122), // LightSalmon
            Color.FromArgb(255, 255, 255, 0),   // Yellow
            Color.FromArgb(255, 189, 183, 107), // DarkKhaki
            Color.FromArgb(255, 0, 255, 255)    // Cyan
            };

            internal void RenderAnnotation(ProtocolAnalyzedAnnotation annotation, int firstSample, int inScreen, Rect rectName, Rect rectData, DrawingContext context)
            {
                var lastSample = firstSample + inScreen - 1;
                var segments = annotation.Segments.Where(s => s.LastSample >= firstSample && s.FirstSample <= lastSample).ToArray();

                using (context.PushClip(rectName))
                {
                    var text = new FormattedText(annotation.AnnotationName, System.Globalization.CultureInfo.InvariantCulture, FlowDirection.LeftToRight, new Typeface("Segoe UI"), 12, Brushes.White);

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

                        var rect = new Rect(rectData.X + xStart, rectData.Y, xEnd - xStart, rectData.Height);
                        RenderSegment(segment, context, rect);
                    }
                }
            }

            internal void RenderSegment(ProtocolAnalyzedAnnotationSegment Segment, DrawingContext G, Rect RenderArea)
            {

                var color = itemPalette[Segment.TypeId % 64];
                var textColor = color.FindContrast();

                double midY = RenderArea.Y + (RenderArea.Height / 2.0);
                double rectHeight = RenderArea.Height - 2;
                double topY = RenderArea.Y + 1;
                double bottomY = topY + rectHeight;

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

                        break;

                    case ProtocolAnalyzerSegmentShape.Rectangle:

                        G.DrawRectangle(GraphicObjectsCache.GetBrush(color), GraphicObjectsCache.GetPen(Colors.Black, 1), RenderArea);

                        break;

                    case ProtocolAnalyzerSegmentShape.RoundRectangle:

                        G.DrawRectangle(GraphicObjectsCache.GetBrush(color), GraphicObjectsCache.GetPen(Colors.Black, 1), RenderArea, 5, 5);

                        break;

                    case ProtocolAnalyzerSegmentShape.Circle:

                        G.DrawEllipse(GraphicObjectsCache.GetBrush(color), GraphicObjectsCache.GetPen(Colors.Black, 1), RenderArea);

                        break;
                }

                FormattedText? text = GetBestText(RenderArea.Width - 10, Segment.Value, textColor);

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