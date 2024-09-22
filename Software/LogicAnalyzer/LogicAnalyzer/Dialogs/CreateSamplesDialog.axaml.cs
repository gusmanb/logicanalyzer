using Avalonia.Controls;
using LogicAnalyzer.Classes;
using LogicAnalyzer.Controls;
using LogicAnalyzer.Extensions;
using System;
using System.Collections.Generic;
using System.ComponentModel;

namespace LogicAnalyzer.Dialogs
{
    public partial class CreateSamplesDialog : PersistableWindowBase
    {
        List<ChannelSampleMaker> channels = new List<ChannelSampleMaker>();
        
        public int MaxSamples 
        { 
            get { return (int)nudSamples.Maximum; } 
            set 
            { 
                nudSamples.Maximum = value; 
                if(nudSamples.Value > nudSamples.Maximum)
                    nudSamples.Value = nudSamples.Maximum;
                    
            } 
        }

        bool insertMode;
        public bool InsertMode
        {
            get { return insertMode; }
            set 
            { 
                insertMode = value;

                if (insertMode)
                {
                    pnlSamples.IsVisible = true;
                    grdMain.RowDefinitions[0].Height = new GridLength(1, GridUnitType.Star);
                }
                else
                {
                    pnlSamples.IsVisible = false;
                    grdMain.RowDefinitions[0].Height = new GridLength(0, GridUnitType.Pixel);
                }
            }
        }

        public CreateSamplesDialog()
        {
            InitializeComponent();
            nudSamples.ValueChanged += NudSamples_ValueChanged;
            btnAccept.Click += BtnAccept_Click;
            btnCancel.Click += BtnCancel_Click;
        }

        private void BtnCancel_Click(object? sender, Avalonia.Interactivity.RoutedEventArgs e)
        {
            this.Close(null);
        }

        private async void BtnAccept_Click(object? sender, Avalonia.Interactivity.RoutedEventArgs e)
        {
            byte[][] samples = new byte[(int)nudSamples.Value][];

            for(int cNum = 0; cNum < channels.Count; cNum++)
            {
                samples[cNum] = new byte[samples.Length];

                var channel = channels[cNum];
                var channelSamples = channel.Samples;

                if (channelSamples == null)
                {
                    await this.ShowError("Invalid samples", $"Channel {channel.Channel + 1} is not correctly configured to generate samples. Cannot continue.");
                    return;
                }
                else
                {
                    if (channelSamples.Length != samples.Length)
                    {
                        await this.ShowError("Internal error", $"Channel {channel.Channel + 1} is generating an incorrect number of samples. Cannot continue.");
                        return;
                    }

                    for(int buc = 0; buc < channelSamples.Length; buc++) 
                    {
                        if (channelSamples[buc])
                            samples[cNum][buc] = 1;
                    }
                }
            }

            this.Close(samples);
        }

        private void NudSamples_ValueChanged(object? sender, NumericUpDownValueChangedEventArgs e)
        {
            foreach (var channel in channels)
                channel.TotalSamples = (int)nudSamples.Value;
        }

        public void Initialize(int[] channelNumbers, string[] channelNames, int maxSamples, int initialSamples)
        {
            nudSamples.Maximum = maxSamples;
            nudSamples.Value = initialSamples;

            if (nudSamples.Value > maxSamples)
                nudSamples.Value = maxSamples;

            for(int buc = 0; buc < channelNumbers.Length; buc++) 
            {
                ChannelSampleMaker channel = new ChannelSampleMaker();
                channel.Channel = channelNumbers[buc];
                channel.ChannelName = channelNames[buc];
                channel.TotalSamples = initialSamples;
                channels.Add(channel);
                pnlControls.Children.Add(channel);
            }
        }
    }
}
