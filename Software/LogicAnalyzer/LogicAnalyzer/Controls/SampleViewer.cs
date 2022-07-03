using LogicAnalyzer.Protocols;
using System;
using System.Collections.Generic;
using System.ComponentModel;
using System.Data;
using System.Drawing;
using System.Linq;
using System.Text;
using System.Threading.Tasks;
using System.Windows.Forms;

namespace LogicAnalyzer
{
    public partial class SampleViewer : UserControl
    {
        public int PreSamples { get; set; }
        public uint[] Samples { get; set; }
        public int ChannelCount { get; set; }
        public int SamplesInScreen { get; set; }
        public int FirstSample { get; set; }

        bool updating = false;

        Pen samplePen;
        Pen triggerPen = new Pen(Color.White, 2);
        List<SelectedSampleRegion> regions = new List<SelectedSampleRegion>();

        public SelectedSampleRegion[] SelectedRegions { get { return regions.ToArray(); } }

        List<ProtocolAnalyzedChannel> analysisData = new List<ProtocolAnalyzedChannel>();

        public SampleViewer()
        {
            InitializeComponent();

            samplePen = new Pen(Color.DarkGray);
            samplePen.DashPattern = new float[] { 1, 4 };

            SetStyle(ControlStyles.AllPaintingInWmPaint | ControlStyles.OptimizedDoubleBuffer, true);
            SetStyle(ControlStyles.ResizeRedraw, true);
            SetStyle(ControlStyles.Opaque, true);
        }

        public void BeginUpdate() 
        {
            updating = true;
        }

        public void EndUpdate()
        {
            updating = false;
            this.Invalidate();
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

        protected override void OnPaint(PaintEventArgs e)
        {
            base.OnPaint(e);
            e.Graphics.SetClip(new Rectangle(Point.Empty, this.Size));
            e.Graphics.Clear(Color.Black);

            if (PreSamples == 0 || Samples == null || ChannelCount == 0 || SamplesInScreen == 0 || updating)
                return;

            float channelHeight = this.Height / (float)ChannelCount;
            float sampleWidth = this.Width / (float)SamplesInScreen;
            float margin = channelHeight / 5;

            int lastSample = Math.Min(SamplesInScreen + FirstSample, Samples.Length);

            for (int chan = 1; chan < ChannelCount; chan += 2)
            {
                e.Graphics.FillRectangle(ChannelColors.ChannlBgBrush, new RectangleF(0, chan * channelHeight, this.Width, channelHeight));
            }

            for (int buc = FirstSample; buc < lastSample; buc++)
            {

                uint sample = Samples[buc];
                uint prevSample = buc == 0 ? 0 : Samples[buc - 1];
                float lineX = (buc - FirstSample) * sampleWidth;

                e.Graphics.DrawLine(samplePen, lineX + sampleWidth / 2, 0, lineX + sampleWidth / 2, this.Height);

                if (buc == PreSamples)
                    e.Graphics.DrawLine(triggerPen, lineX, 0, lineX, this.Height);

                for (int chan = 0; chan < ChannelCount; chan++)
                {
                    float lineY;

                    uint curVal = (uint)(sample & (1 << chan));
                    uint prevVal = (uint)(prevSample & (1 << chan));
                    if (curVal != 0)
                        lineY = chan * channelHeight + margin;
                    else
                        lineY = (chan + 1) * channelHeight - margin;

                    e.Graphics.DrawLine(ChannelColors.ChannelPens[chan], lineX, lineY, lineX + sampleWidth, lineY);

                    if (curVal != prevVal)
                    {
                        lineY = chan * channelHeight + margin;
                        e.Graphics.DrawLine(ChannelColors.ChannelPens[chan], lineX, lineY, lineX, lineY + channelHeight - margin * 2);
                    }
                }

            }

            e.Graphics.CompositingMode = System.Drawing.Drawing2D.CompositingMode.SourceOver;

            if (regions.Count > 0)
            {
                foreach (var region in regions)
                {
                    float start = (region.FirstSample - FirstSample) * sampleWidth;
                    float end = sampleWidth * region.SampleCount;
                    e.Graphics.FillRectangle(region.RegionColor, new RectangleF(start, 0, end, this.Height));
                }
            }

            if (analysisData != null && analysisData.Count > 0)
            {
                foreach (var channel in analysisData)
                {
                    var overlappingSegments = channel.Segments.Where(s => s.FirstSample <= s.LastSample && s.LastSample >= FirstSample);

                    if (overlappingSegments.Any())
                    {
                        float yStart = channel.ChannelIndex * channelHeight + channelHeight * 0.25f;
                        float yEnd = channelHeight * 0.5f;

                        foreach (var segment in overlappingSegments)
                        {

                            float xStart = (segment.FirstSample - FirstSample) * sampleWidth;
                            float xEnd = sampleWidth * (segment.LastSample - segment.FirstSample + 1);

                            RectangleF area = new RectangleF(xStart, yStart, xEnd, yEnd);

                            channel.Render(segment, e.Graphics, area);
                        }
                    }
                }
            }

            e.Graphics.CompositingMode = System.Drawing.Drawing2D.CompositingMode.SourceCopy;
        }
    }
}
