using Avalonia.Controls;
using LogicAnalyzer.Classes;
using LogicAnalyzer.Controls;
using LogicAnalyzer.Extensions;
using System.Collections;
using System.Collections.Generic;
using System.Drawing;
using System.Linq;

namespace LogicAnalyzer.Dialogs
{
    public partial class MeasureDialog : PersistableWindowBase
    {
        public MeasureDialog()
        {
            InitializeComponent();
            btnAccept.Click += BtnAccept_Click;
        }

        private void BtnAccept_Click(object? sender, Avalonia.Interactivity.RoutedEventArgs e)
        {
            this.Close();
        }

        public void SetData(string[] ChannelNames, IEnumerable<byte[]> Samples, int SamplingFrequency)
        {
            int samples = Samples.First().Length;
            lblSamples.Text = samples.ToString();
            double period = (1.0 / (double)SamplingFrequency) * samples;
            lblPeriod.Text = period.ToSmallTime();

            period = 1.0 / (double)SamplingFrequency;
            lblSamplePeriod.Text = period.ToSmallTime();

            for (int buc = 0; buc < ChannelNames.Length; buc++)
            {
                ChannelMeasures cm = new ChannelMeasures();
                cm.SetData(ChannelNames[buc], Samples.Skip(buc).First(), SamplingFrequency);
                pnlControls.Children.Add(cm);
            }
        }
    }
}
