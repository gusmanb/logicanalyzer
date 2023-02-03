using Avalonia;
using Avalonia.Controls;
using Avalonia.Media;
using LogicAnalyzer.Classes;
using LogicAnalyzer.Extensions;
using System;
using System.Collections.Generic;
using System.Linq;

namespace LogicAnalyzer.Controls
{
    public partial class ChannelMeasures : UserControl
    {
        public static readonly StyledProperty<IBrush> ForegroundProperty = AvaloniaProperty.Register<SampleMarker, IBrush>(nameof(Foreground));

        public static readonly StyledProperty<IBrush> BackgroundProperty = AvaloniaProperty.Register<SampleMarker, IBrush>(nameof(Background));

        public new IBrush Foreground
        {
            get { return GetValue<IBrush>(ForegroundProperty); }
            set { SetValue<IBrush>(ForegroundProperty, value); base.Foreground = value; UpdateTextColors(); InvalidateVisual(); }
        }

        public new IBrush Background
        {
            get { return GetValue<IBrush>(BackgroundProperty); }
            set { SetValue<IBrush>(BackgroundProperty, value); base.Background = value; UpdateTextColors(); InvalidateVisual(); }
        }

        void UpdateTextColors()
        {
            lblFreq.Foreground= Foreground;
            lblFreq.Background= Background;
            lblNegPulses.Foreground= Foreground;
            lblNegPulses.Background= Background;
            lblNegPulsesDuration.Foreground= Foreground;
            lblNegPulsesDuration.Background= Background;
            lblPosPulses.Foreground= Foreground;
            lblPosPulses.Background = Background;
            lblPosPulsesDuration.Foreground = Foreground;
            lblPosPulsesDuration.Background = Background;
        }

        public ChannelMeasures()
        {
            InitializeComponent();
        }

        public void SetData(string channelName, byte[] channelSamples, int frequency)
        {
            int currentPulse = -1;
            int currentCount = 0;

            List<int> posLengths= new List<int>();
            List<int> negLengths = new List<int>();

            for (int buc = 0; buc < channelSamples.Length; buc++)
            {
                if (channelSamples[buc] != currentPulse)
                {
                    if (currentPulse == 1)
                        posLengths.Add(currentCount);
                    else if (currentPulse == 0)
                        negLengths.Add(currentCount);

                    currentPulse = channelSamples[buc];
                    currentCount = 1;
                }
                else
                    currentCount++;
            }

            if (currentPulse == 1)
                posLengths.Add(currentCount);
            else if (currentPulse == 0)
                negLengths.Add(currentCount);

            var posGrouped = posLengths.GroupBy(p => p).OrderBy(g => g.Count()).ToArray();
            var posOrderedByCount = posGrouped.SelectMany(g => g.ToArray()).ToArray();

            int fivePercent = (int)(posOrderedByCount.Length * 0.95);

            var finalPosSamples = posOrderedByCount.Skip(fivePercent).ToArray();

            var negGrouped = negLengths.GroupBy(p => p).OrderBy(g => g.Count()).ToArray();
            var negOrderedByCount = negGrouped.SelectMany(g => g.ToArray()).ToArray();

            fivePercent = (int)(negOrderedByCount.Length * 0.95);

            var finalNegSamples = negOrderedByCount.Skip(fivePercent).ToArray();

            int minPulses = Math.Min(finalPosSamples.Length, finalNegSamples.Length);

            var matchedPos = finalPosSamples.Skip(finalPosSamples.Length - minPulses).ToArray();
            var matchedNeg = finalNegSamples.Skip(finalNegSamples.Length - minPulses).ToArray();

            int totalSamples = matchedPos.Sum() + matchedNeg.Sum();
            double period = totalSamples * (1.0 / frequency);
            
            double predPosPeriod = finalPosSamples.Length == 0 ? 0 : (finalPosSamples.Average() * (1.0 / frequency));
            double predNegPeriod = finalNegSamples.Length == 0 ? 0 : (finalNegSamples.Average() * (1.0 / frequency));

            double predFreq = period == 0 ? 0 : (1.0 / (predPosPeriod + predNegPeriod));

            double avgPosPeriod = posLengths.Count == 0 ? 0 : (posLengths.Average() * (1.0 / frequency));
            double avgNegPeriod = negLengths.Count == 0 ? 0 : (negLengths.Average() * (1.0 / frequency));

            double avgFreq = period == 0 ? 0 : (1.0 / (avgPosPeriod + avgNegPeriod));

            lblPosPulses.Text = posLengths.Count.ToString();
            lblNegPulses.Text = negLengths.Count.ToString();
            lblPosPredPulsesDuration.Text = predPosPeriod.ToSmallTime();
            lblPosPulsesDuration.Text = avgPosPeriod.ToSmallTime();
            lblNegPredPulsesDuration.Text = predNegPeriod.ToSmallTime();
            lblNegPulsesDuration.Text = avgNegPeriod.ToSmallTime();
            lblPredFreq.Text = predFreq.ToLargeFrequency();
            lblFreq.Text = avgFreq.ToLargeFrequency();
            lblName.Text = $"Channel {channelName}";
        }

    }
}
