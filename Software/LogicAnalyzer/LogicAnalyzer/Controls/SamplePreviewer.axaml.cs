using Avalonia;
using Avalonia.Controls;
using Avalonia.Media;
using Avalonia.Media.Imaging;
using LogicAnalyzer.Classes;
using LogicAnalyzer.Interfaces;
using SkiaSharp;
using System;

namespace LogicAnalyzer.Controls
{
    public partial class SamplePreviewer : UserControl, ISampleDisplay
    {
        Bitmap? bmp;
        int sampleCount = 0;

        int viewPosition;
        public int ViewPosition { get { return viewPosition; } set { viewPosition = value; InvalidateVisual(); } }

        public int FirstSample { get; private set; }

        public int VisibleSamples { get; private set; }

        public SamplePreviewer()
        {
            InitializeComponent();
        }

        public void UpdateSamples(CaptureChannel[] Channels, int SampleCount)
        {
            int channelCount = Channels.Length;

            if (channelCount > 24)
                channelCount = 24;

            int width = Math.Max(Math.Min(SampleCount, 4096), 1024);

            float cHeight = 144 / (float)channelCount;
            float sWidth = (float)width / (float)SampleCount;
            float high = cHeight / 6;
            float low = cHeight - high;

            using SKBitmap skb = new SKBitmap(width, 144);

            SKPaint[] colors = new SKPaint[channelCount];

            for (int buc = 0; buc < channelCount; buc++)
            {
                var avColor = Channels[buc].ChannelColor ?? AnalyzerColors.GetColor(Channels[buc].ChannelNumber);

                colors[buc] = new SKPaint
                {
                    Style = SKPaintStyle.Stroke,
                    StrokeWidth = 1,
                    Color = new SKColor(avColor.R, avColor.G, avColor.B)
                };
            }

            using (var canvas = new SKCanvas(skb))
            {
                for (int x = 0; x < SampleCount; x++)
                {
                    int sample = x;
                    int prevSample = x == 0 ? x : x - 1;

                    for (int chan = 0; chan < channelCount; chan++)
                    {
                        byte curVal = Channels[chan].Samples[sample];
                        byte prevVal = Channels[chan].Samples[prevSample];

                        float y = chan * cHeight + (curVal != 0 ? high : low);

                        canvas.DrawLine(x * sWidth, y, (x + 1) * sWidth, y, colors[chan]);

                        if (curVal != prevVal)
                            canvas.DrawLine(x * sWidth, chan * cHeight + high, x * sWidth, chan * cHeight + low, colors[chan]);
                    }
                }
            }

            using var encoded = skb.Encode(SKEncodedImageFormat.Png, 1);
            using var stream = encoded.AsStream();

            if (bmp != null)
                bmp.Dispose();

            bmp = new Bitmap(stream);
            sampleCount = SampleCount;
        }

        public override void Render(DrawingContext context)
        {
            //base.Render(context);
            var bounds = new Avalonia.Rect(0, 0, this.Bounds.Width, this.Bounds.Height);

            context.FillRectangle(GraphicObjectsCache.GetBrush(Color.Parse("#222222")), bounds);

            if (sampleCount == 0 || bmp == null)
                return;

            //Test quality!!!
            (bmp as IImage).Draw(context, new Avalonia.Rect(bmp.Size), bounds);

            float ratio = (float)bounds.Size.Width / (float)sampleCount;
            float pos = viewPosition * ratio;

            Rect rcVisible = new Rect(FirstSample * ratio, 0, VisibleSamples * ratio, bounds.Height);
            context.FillRectangle(GraphicObjectsCache.GetBrush(Color.FromArgb(32, 255, 255, 255)), rcVisible);

            /*
            context.DrawLine(GraphicObjectsCache.GetPen(Colors.White, 1, DashStyle.Dash), new Avalonia.Point(pos, 0), new Avalonia.Point(pos, 143));
            */
        }

        public void UpdateVisibleSamples(int FirstSample, int VisibleSamples)
        {
            this.FirstSample = FirstSample;
            this.VisibleSamples = VisibleSamples;
            InvalidateVisual();
        }
    }
}
