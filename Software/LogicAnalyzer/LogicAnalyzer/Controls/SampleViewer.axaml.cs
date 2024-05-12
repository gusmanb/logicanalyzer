using Avalonia;
using Avalonia.Controls;
using Avalonia.Controls.Shapes;
using Avalonia.Markup.Xaml;
using Avalonia.Media;
using LogicAnalyzer.Classes;
using LogicAnalyzer.Protocols;
using System;
using System.Collections.Generic;
using System.Linq;

namespace LogicAnalyzer.Controls
{
    public partial class SampleViewer : UserControl
    {
        const int MIN_CHANNEL_HEIGHT = 48;

        public int PreSamples { get; set; }
        public int[]? Bursts { get; set; }
        public UInt128[] Samples { get; set; }

        public CaptureChannel[]? Channels { get; set; }
        //public int ChannelCount { get; set; }
        public int SamplesInScreen { get; set; }
        public int FirstSample { get; set; }
        public int? UserMarker { get; set; }

        bool updating = false;

        List<SampleRegion> regions = new List<SampleRegion>();

        public SampleRegion[] SelectedRegions { get { return regions.ToArray(); } }

        List<ProtocolAnalyzedChannel> analysisData = new List<ProtocolAnalyzedChannel>();
        Color sampleLineColor = Color.FromRgb(60, 60, 60);
        Color sampleDashColor = Color.FromArgb(60, 60, 60, 60);
        Color triggerLineColor = Colors.White;
        Color burstLineColor = Colors.Azure;
        Color userLineColor = Colors.Cyan;

        public SampleViewer()
        {
            InitializeComponent();
            byte t = 0;
        }

        public void BeginUpdate()
        {
            updating = true;
        }

        public void EndUpdate()
        {
            updating = false;
            this.InvalidateVisual();
        }
        public void AddRegion(SampleRegion Region)
        {
            regions.Add(Region);
        }
        public void AddRegions(IEnumerable<SampleRegion> Regions)
        {
            regions.AddRange(Regions);
        }
        public bool RemoveRegion(SampleRegion Region)
        {
            return regions.Remove(Region);
        }
        public void ClearRegions()
        {
            regions.Clear();
        }
        public void AddAnalyzedChannel(ProtocolAnalyzedChannel Data)
        {
            analysisData.Add(Data);
        }
        public void AddAnalyzedChannels(IEnumerable<ProtocolAnalyzedChannel> Data)
        {
            analysisData.AddRange(Data);
        }
        public bool RemoveAnalyzedChannel(ProtocolAnalyzedChannel Data)
        {
            return analysisData.Remove(Data);
        }

        public void ClearAnalyzedChannels()
        {
            foreach (var data in analysisData)
                data.Dispose();

            analysisData.Clear();
        }

        public override void Render(DrawingContext context)
        {

            int ChannelCount = Channels?.Length ?? 0;

            int minSize = ChannelCount * MIN_CHANNEL_HEIGHT;

            if (Parent.Bounds.Height > minSize && this.Height != double.NaN)
                this.Height = double.NaN;
            else if(Bounds.Height < minSize)
                this.Height = minSize;

            base.Render(context);
            Rect thisBounds = new Rect(0, 0, Bounds.Width, Bounds.Height);
            using (context.PushClip(thisBounds))
            {
                //context.FillRectangle(GraphicObjectsCache.GetBrush(AnalyzerColors.BgChannelColors[0]), thisBounds);

                if (Samples == null || ChannelCount == 0 || SamplesInScreen == 0 || updating)
                    return;

                double channelHeight = thisBounds.Height / (double)ChannelCount;
                double sampleWidth = thisBounds.Width / (double)SamplesInScreen;
                double margin = channelHeight / 5;

                int lastSample = Math.Min(SamplesInScreen + FirstSample, Samples.Length);

                
                for (int chan = 0; chan < ChannelCount; chan++)
                {
                    context.FillRectangle(GraphicObjectsCache.GetBrush(AnalyzerColors.BgChannelColors[chan % 2]), new Rect(0, chan * channelHeight, thisBounds.Width, channelHeight));
                }
                
                if (regions.Count > 0)
                {
                    foreach (var region in regions)
                    {
                        int first = Math.Min(region.FirstSample, region.LastSample);
                        double start = (first - FirstSample) * sampleWidth;
                        double end = sampleWidth * region.SampleCount;
                        context.FillRectangle(GraphicObjectsCache.GetBrush(region.RegionColor), new Rect(start, 0, end, this.Bounds.Height));
                    }
                }

                for (int buc = FirstSample; buc < lastSample; buc++)
                {

                    UInt128 sample = Samples[buc];
                    UInt128 prevSample = buc == 0 ? 0 : Samples[buc - 1];
                    double lineX = (buc - FirstSample) * sampleWidth;

                    if (SamplesInScreen < 201)
                    {
                        context.DrawLine(GraphicObjectsCache.GetPen(sampleLineColor, 1), new Point(lineX + sampleWidth / 2, 0), new Point(lineX + sampleWidth / 2, thisBounds.Height));

                        if (SamplesInScreen < 101)
                        {
                            context.DrawLine(GraphicObjectsCache.GetPen(sampleDashColor, 1), new Point(lineX, 0), new Point(lineX, thisBounds.Height));
                        }

                    }

                    if (buc == PreSamples)
                        context.DrawLine(GraphicObjectsCache.GetPen(triggerLineColor, 2), new Point(lineX, 0), new Point(lineX, thisBounds.Height));

                    if (Bursts != null)
                    {
                        if (Bursts.Any(b => b == buc))
                        {
                            context.DrawLine(GraphicObjectsCache.GetPen(burstLineColor, 2, DashStyle.DashDot), new Point(lineX, 0), new Point(lineX, thisBounds.Height));
                        }
                    }

                    if(UserMarker != null && UserMarker == buc)
                        context.DrawLine(GraphicObjectsCache.GetPen(userLineColor, 2, DashStyle.DashDot), new Point(lineX, 0), new Point(lineX, thisBounds.Height));

                    for (int chan = 0; chan < ChannelCount; chan++)
                    {
                        double lineY;

                        UInt128 curVal = sample & ((UInt128)1 << chan);
                        UInt128 prevVal = prevSample & ((UInt128)1 << chan);
                        if (curVal != 0)
                            lineY = chan * channelHeight + margin;
                        else
                            lineY = (chan + 1) * channelHeight - margin;

                        context.DrawLine(GraphicObjectsCache.GetPen(Channels?[chan].ChannelColor ?? AnalyzerColors.FgChannelColors[chan], 2), new Point(lineX, lineY), new Point(lineX + sampleWidth, lineY));

                        if (curVal != prevVal && buc != 0)
                        {
                            lineY = chan * channelHeight + margin;
                            context.DrawLine(GraphicObjectsCache.GetPen(Channels?[chan].ChannelColor ?? AnalyzerColors.FgChannelColors[chan], 2), new Point(lineX, lineY), new Point(lineX, lineY + channelHeight - margin * 2));
                        }
                    }

                }

                if (UserMarker != null && UserMarker == lastSample)
                {
                    double lineX = (lastSample - FirstSample) * sampleWidth;
                    context.DrawLine(GraphicObjectsCache.GetPen(userLineColor, 2, DashStyle.DashDot), new Point(lineX, 0), new Point(lineX, thisBounds.Height));
                }
                if (analysisData != null && analysisData.Count > 0)
                {
                    foreach (var channel in analysisData)
                    {
                        var overlappingSegments = channel.Segments.Where(s => s.FirstSample <= s.LastSample && s.LastSample >= FirstSample);

                        if (overlappingSegments.Any())
                        {
                            double yStart = channel.ChannelIndex * channelHeight + channelHeight * 0.25f;
                            double yEnd = channelHeight * 0.5f;

                            foreach (var segment in overlappingSegments)
                            {

                                double xStart = (segment.FirstSample - FirstSample) * sampleWidth;
                                double xEnd = sampleWidth * (segment.LastSample - segment.FirstSample + 1);

                                Rect area = new Rect(xStart, yStart, xEnd, yEnd);

                                channel.Render(segment, context, area);
                            }
                        }
                    }
                }
            }
        }

    }
}
