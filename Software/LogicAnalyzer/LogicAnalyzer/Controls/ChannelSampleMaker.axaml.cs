using Avalonia;
using Avalonia.Controls;
using Avalonia.Media;
using Avalonia.Media.Imaging;
using LogicAnalyzer.Classes;
using LogicAnalyzer.Dialogs;
using System;
using System.Collections.Generic;
using System.Linq;
using System.Text.RegularExpressions;
using static SignalDescriptionLanguage.SDLParser;

namespace LogicAnalyzer.Controls
{
    public partial class ChannelSampleMaker : UserControl
    {
        TokenizedSDL? sdl;
        public TokenizedSDL? SDL { get { return sdl; } set { sdl = value; GenerateImage(); } }

        int totalSamples = 0;
        public int TotalSamples { get { return totalSamples; } set { totalSamples = value; GenerateImage(); }  }

        RenderTargetBitmap? renderTarget;

        int channel;
        public int Channel 
        { 
            get { return channel; } 
            set { channel = value; lblChannelNo.Text = $"Channel {channel + 1}"; GenerateImage(); } 
        }

        string? channelName;
        public string? ChannelName 
        {
            get { return channelName; }
            set { channelName = value; lblChannelName.Text = channelName; }
        }

        public bool[]? Samples { get { return GenerateSamples(); } }

        public ChannelSampleMaker()
        {
            InitializeComponent();
            brdImage.PointerReleased += ImgSignal_PointerReleased;
        }

        private async void ImgSignal_PointerReleased(object? sender, Avalonia.Input.PointerReleasedEventArgs e)
        {
            if(e.InitialPressMouseButton == Avalonia.Input.MouseButton.Left)
            {
                var dlg = new SignalComposerDialog();
                dlg.SDL = sdl;
                await dlg.ShowDialog(this.Parent.Parent.Parent.Parent as Window);
                SDL = dlg.SDL;
            }
        }

        private bool[]? GenerateSamples()
        {
            bool[]? samples = sdl?.ToSamples();

            if (samples == null || samples.Length == 0)
                return null;

            if (samples.Length < totalSamples)
            {
                List<bool> buf = new List<bool>();
                buf.AddRange(samples);
                bool[] extra = new bool[totalSamples - samples.Length];
                Array.Fill(extra, samples.Last());
                buf.AddRange(extra);
                samples = buf.ToArray();

            }
            else if (samples.Length > totalSamples)
                samples = samples.Take(totalSamples).ToArray();

            return samples;
        }

        private void GenerateImage()
        {
            bool[]? samples = GenerateSamples();

            if (renderTarget != null)
            {
                imgSignal.Source = null;
                renderTarget.Dispose();
                renderTarget = null;
            }

            renderTarget = new RenderTargetBitmap(new PixelSize(630, 46));

            if (samples == null || samples.Length == 0)
                return;


            double sampleWidth = 630.0 / samples.Length;
            bool currentValue = samples[0];
            double currentX = 0;
            int high = 6;
            int low = 40;

            using (var context = renderTarget.CreateDrawingContext(null))
            {
                var pen = GraphicObjectsCache.GetPen(AnalyzerColors.FgChannelColors[channel], 1);
                for (int buc = 0; buc < samples.Length; buc++)
                {
                    if (samples[buc] != currentValue)
                        context.DrawLine(pen, new Point(currentX, high), new Point(currentX, low));

                    currentValue = samples[buc];

                    if (currentValue == true)
                        context.DrawLine(pen, new Point(currentX, high), new Point(currentX + sampleWidth, high));
                    else
                        context.DrawLine(pen, new Point(currentX, low), new Point(currentX + sampleWidth, low));

                    currentX += sampleWidth;
                }
            }


            imgSignal.Source = renderTarget;
        }
       
    }
}
