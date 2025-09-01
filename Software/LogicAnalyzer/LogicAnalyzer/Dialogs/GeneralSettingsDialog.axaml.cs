using Avalonia.Controls;
using LogicAnalyzer.Extensions;
using System;

namespace LogicAnalyzer.Dialogs
{
    public partial class GeneralSettingsDialog : Window
    {
        public int MinSamples { get; set; }
        public int MaxSamples { get; set; }

        public int MinSamplesLimit { get; set; }
        public int MaxSamplesLimit { get; set; }

        public GeneralSettingsDialog()
        {
            InitializeComponent();
            btnAccept.Click += BtnAccept_Click;
            btnCancel.Click += BtnCancel_Click;
        }

        protected override void OnOpened(EventArgs e)
        {
            base.OnOpened(e);
            this.FixStartupPosition();
            nudMin.Minimum = MinSamplesLimit;
            nudMin.Maximum = MaxSamplesLimit;
            nudMax.Minimum = MinSamplesLimit;
            nudMax.Maximum = MaxSamplesLimit;

            nudMin.Value = Math.Clamp(MinSamples, MinSamplesLimit, MaxSamplesLimit);
            nudMax.Value = Math.Clamp(MaxSamples, MinSamplesLimit, MaxSamplesLimit);

            var tooltip = $"Min: {MinSamplesLimit:#,##0}\r\nMax: {MaxSamplesLimit:#,##0}";
            ToolTip.SetTip(nudMin, tooltip);
            ToolTip.SetTip(nudMax, tooltip);
        }

        private void BtnCancel_Click(object? sender, Avalonia.Interactivity.RoutedEventArgs e)
        {
            Close(false);
        }

        private async void BtnAccept_Click(object? sender, Avalonia.Interactivity.RoutedEventArgs e)
        {
            if (nudMax.Value < nudMin.Value)
            {
                await this.ShowError("Invalid settings", "Max samples must be greater than Min samples.");
                return;
            }
            MinSamples = (int)nudMin.Value;
            MaxSamples = (int)nudMax.Value;
            Close(true);
        }
    }
}
