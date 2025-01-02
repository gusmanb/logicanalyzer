using Avalonia;
using Avalonia.Controls;
using Avalonia.Input;
using Avalonia.Media;
using LogicAnalyzer.Classes;
using LogicAnalyzer.Extensions;
using LogicAnalyzer.Protocols;
using System;
using System.Collections.Generic;
using System.Linq;

namespace LogicAnalyzer.Controls
{
    public partial class SampleViewer : UserControl
    {
        const int MIN_CHANNEL_HEIGHT = 48;

        private Point? _lastPointerLocation;

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

        public int TimeStepNs { get; internal set; }

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
            else if (Bounds.Height < minSize)
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

                var horizontalLineSegments = new Dictionary<(int channel, double lineLevel), List<(double start, double end)>>();
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

                    if (UserMarker != null && UserMarker == buc)
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

                        // render performance penalty due to a lots of small lines being drawn
                        //context.DrawLine(GraphicObjectsCache.GetPen(Channels?[chan].ChannelColor ?? AnalyzerColors.FgChannelColors[chan], 2), new Point(lineX, lineY), new Point(lineX + sampleWidth, lineY));
                        // collect all horizontal lines needed, then merge them to draw one line at once
                        {
                            if (!horizontalLineSegments.TryGetValue((chan, lineY), out var lineSegments))
                                horizontalLineSegments[(chan, lineY)] = lineSegments = new List<(double start, double end)>();

                            lineSegments.Add((lineX, lineX + sampleWidth));
                        }

                        if (curVal != prevVal && buc != 0)
                        {
                            lineY = chan * channelHeight + margin;
                            context.DrawLine(GraphicObjectsCache.GetPen(Channels?[chan].ChannelColor ?? AnalyzerColors.FgChannelColors[chan], 2), new Point(lineX, lineY), new Point(lineX, lineY + channelHeight - margin * 2));
                        }
                    }
                }

                RenderHorizontalLines(context, horizontalLineSegments);

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

                if (IsPointerOver && _lastPointerLocation != null)
                    RenderPointerRuler(context, _lastPointerLocation.Value, sampleWidth, lastSample, channelHeight, margin);
            }
        }

        private void RenderHorizontalLines(DrawingContext context, Dictionary<(int channel, double lineLevel), List<(double start, double end)>> lines)
        {
            foreach (var channelLineSegments in lines)
            {
                var chan = channelLineSegments.Key.channel;
                var lineY = channelLineSegments.Key.lineLevel;

                for (int i = 0; i < channelLineSegments.Value.Count;)
                {
                    var seg = channelLineSegments.Value[i];
                    var start = seg.start;
                    var end = seg.end;
                    var innerIdx = i + 1;
                    while (innerIdx < channelLineSegments.Value.Count)
                    {
                        if (Math.Abs(end - channelLineSegments.Value[innerIdx].start) < 0.001)
                        {
                            end = channelLineSegments.Value[innerIdx].end;
                            innerIdx++;
                        }
                        else
                        {
                            break;
                        }
                    }

                    context.DrawLine(GraphicObjectsCache.GetPen(Channels?[chan].ChannelColor ?? AnalyzerColors.FgChannelColors[chan], 2), new Point(start, lineY), new Point(end, lineY));
                    i = innerIdx;
                }
            }
        }

        private void RenderPointerRuler(DrawingContext context, Point pointerLocation, double sampleWidth, int lastSample, double channelHeight, double channelMargin)
        {
            if (Channels == null)
                return;

            var sampleIdx = (int)(pointerLocation.X / sampleWidth + FirstSample);
            if (sampleIdx >= lastSample || sampleIdx < 0)
                return;

            var channelIdx = (int)(pointerLocation.Y / channelHeight);
            if (channelIdx >= Channels.Length)
                return;

            var channelTopMargin = channelIdx * channelHeight + channelMargin;
            var channelBotMargin = (channelIdx + 1) * channelHeight - channelMargin;
            if (pointerLocation.Y < channelTopMargin || pointerLocation.Y > channelBotMargin)
                return;

            var channelNum = Channels[channelIdx].ChannelNumber;

            UInt128 sample = Samples[sampleIdx];
            UInt128 sampleValue = getChannelValue(sample, channelNum);

            int leftSampleIdx = sampleIdx;
            UInt128 leftSampleValue = sampleValue;
            do
            {
                UInt128 leftSample = Samples[leftSampleIdx];
                leftSampleValue = getChannelValue(leftSample, channelNum);

                leftSampleIdx--;
            }
            while (leftSampleIdx >= 0 && leftSampleValue == sampleValue);
            if (leftSampleValue != sampleValue)
                leftSampleIdx++;
            else
                return;

            int rightSampleIdx = sampleIdx;
            UInt128 rightSampleValue = sampleValue;
            do
            {
                UInt128 rightSample = Samples[rightSampleIdx];
                rightSampleValue = getChannelValue(rightSample, channelNum);

                rightSampleIdx++;
            }
            while (rightSampleIdx < Samples.Length && rightSampleValue == sampleValue);
            if (rightSampleValue != sampleValue)
                rightSampleIdx--;
            else
                return;

            var lineStart = ((Math.Max(FirstSample, leftSampleIdx) - FirstSample) + 1) * sampleWidth;
            var lineEnd = (Math.Min(lastSample, rightSampleIdx) - FirstSample) * sampleWidth;

            const int arrowSize = 5;

            context.DrawLine(GraphicObjectsCache.GetPen(userLineColor, 1, DashStyle.DashDot), new Point(lineStart, pointerLocation.Y), new Point(lineEnd, pointerLocation.Y));

            if (leftSampleIdx >= FirstSample)
            {
                context.DrawLine(GraphicObjectsCache.GetPen(userLineColor, 1), new Point(lineStart, pointerLocation.Y), new Point(lineStart + arrowSize, pointerLocation.Y + arrowSize));
                context.DrawLine(GraphicObjectsCache.GetPen(userLineColor, 1), new Point(lineStart, pointerLocation.Y), new Point(lineStart + arrowSize, pointerLocation.Y - arrowSize));
            }

            if (rightSampleIdx <= lastSample)
            {
                context.DrawLine(GraphicObjectsCache.GetPen(userLineColor, 1), new Point(lineEnd, pointerLocation.Y), new Point(lineEnd - arrowSize, pointerLocation.Y + arrowSize));
                context.DrawLine(GraphicObjectsCache.GetPen(userLineColor, 1), new Point(lineEnd, pointerLocation.Y), new Point(lineEnd - arrowSize, pointerLocation.Y - arrowSize));
            }

            var samplesWidth = rightSampleIdx - leftSampleIdx - 1;

            var region = regions.OfType<BurstGapRegion>().FirstOrDefault(r => r.FirstSample >= leftSampleIdx && r.LastSample <= rightSampleIdx);
            if (region != null)
                samplesWidth = samplesWidth - region.GapSamples + region.BurstDelaySamples;

            var timeStr = (samplesWidth * TimeStepNs / 1000000000d).ToSmallTime();
            var formattedText = new FormattedText($"{timeStr} ({samplesWidth} samples)", Typeface.Default, 12, TextAlignment.Center, TextWrapping.NoWrap, Size.Infinity);
            context.DrawText(Foreground, new((lineEnd - lineStart) / 2 + lineStart - 20, pointerLocation.Y - 16), formattedText);
        }

        static UInt128 getChannelValue(UInt128 sample, int channelNumber) => sample & ((UInt128)1 << channelNumber);

        protected override void OnPointerMoved(PointerEventArgs e)
        {
            base.OnPointerMoved(e);

            var point = e.GetCurrentPoint(this);

            _lastPointerLocation = IsPointerOver ? point.Position : null;
            InvalidateVisual();
        }

        protected override void OnPointerLeave(PointerEventArgs e)
        {
            base.OnPointerLeave(e);

            _lastPointerLocation = null;
            InvalidateVisual();
        }
    }
}
