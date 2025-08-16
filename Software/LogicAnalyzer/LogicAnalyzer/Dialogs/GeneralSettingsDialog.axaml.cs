using Avalonia.Controls;
using LogicAnalyzer.Extensions;
using System;

namespace LogicAnalyzer.Dialogs
{
    public partial class GeneralSettingsDialog : Window
    {
        public int MinSamples { get; set; }
        public int MaxSamples { get; set; }

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
            nudMin.Value = MinSamples;
            nudMax.Value = MaxSamples;
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
