using Avalonia;
using Avalonia.Controls;
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
        public int PreSamples { get; set; }
        public uint[] Samples { get; set; }
        public int ChannelCount { get; set; }
        public int SamplesInScreen { get; set; }
        public int FirstSample { get; set; }

        public int? UserMarker { get; set; }

        bool updating = false;

        List<SelectedSampleRegion> regions = new List<SelectedSampleRegion>();

        public SelectedSampleRegion[] SelectedRegions { get { return regions.ToArray(); } }

        List<ProtocolAnalyzedChannel> analysisData = new List<ProtocolAnalyzedChannel>();
        Color sampleLineColor = Color.FromRgb(60, 60, 60);
        Color triggerLineColor = Colors.White;
        Color userLineColor = Colors.Cyan;
        DashStyle halfDash = new DashStyle(new double[] { 1, 8 }, 0);
        DashStyle fullDash = new DashStyle(new double[] { 4, 5 }, 0);
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
        public void AddRegion(SelectedSampleRegion Region)
        {
            regions.Add(Region);
        }
        public void AddRegions(IEnumerable<SelectedSampleRegion> Regions)
        {
            regions.AddRange(Regions);
        }
        public bool RemoveRegion(SelectedSampleRegion Region)
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
            base.Render(context);
            Rect thisBounds = new Rect(0, 0, Bounds.Width, Bounds.Height);
            using (context.PushClip(thisBounds))
            {
                //context.FillRectangle(GraphicObjectsCache.GetBrush(AnalyzerColors.BgChannelColors[0]), thisBounds);

                if (PreSamples == 0 || Samples == null || ChannelCount == 0 || SamplesInScreen == 0 || updating)
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

                    uint sample = Samples[buc];
                    uint prevSample = buc == 0 ? 0 : Samples[buc - 1];
                    double lineX = (buc - FirstSample) * sampleWidth;

                    context.DrawLine(GraphicObjectsCache.GetPen(sampleLineColor, 1, fullDash), new Point(lineX + sampleWidth / 2, 0), new Point(lineX + sampleWidth / 2, thisBounds.Height));

                    context.DrawLine(GraphicObjectsCache.GetPen(sampleLineColor, 1, halfDash), new Point(lineX, 0), new Point(lineX, thisBounds.Height));

                    if (buc == PreSamples)
                        context.DrawLine(GraphicObjectsCache.GetPen(triggerLineColor, 2), new Point(lineX, 0), new Point(lineX, thisBounds.Height));

                    if(UserMarker != null && UserMarker == buc)
                        context.DrawLine(GraphicObjectsCache.GetPen(userLineColor, 2, DashStyle.DashDot), new Point(lineX, 0), new Point(lineX, thisBounds.Height));

                    for (int chan = 0; chan < ChannelCount; chan++)
                    {
                        double lineY;

                        uint curVal = (uint)(sample & (1 << chan));
                        uint prevVal = (uint)(prevSample & (1 << chan));
                        if (curVal != 0)
                            lineY = chan * channelHeight + margin;
                        else
                            lineY = (chan + 1) * channelHeight - margin;

                        context.DrawLine(GraphicObjectsCache.GetPen(AnalyzerColors.FgChannelColors[chan], 1), new Point(lineX, lineY), new Point(lineX + sampleWidth, lineY));

                        if (curVal != prevVal)
                        {
                            lineY = chan * channelHeight + margin;
                            context.DrawLine(GraphicObjectsCache.GetPen(AnalyzerColors.FgChannelColors[chan], 1), new Point(lineX, lineY), new Point(lineX, lineY + channelHeight - margin * 2));
                        }
                    }

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
