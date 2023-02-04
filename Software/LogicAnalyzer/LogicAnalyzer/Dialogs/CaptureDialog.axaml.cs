using Avalonia;
using Avalonia.Controls;
using Avalonia.Interactivity;
using Avalonia.Markup.Xaml;
using LogicAnalyzer.Extensions;
using MessageBox.Avalonia;
using Newtonsoft.Json;
using SharedDriver;
using System;
using System.Collections.Generic;
using System.IO;
using System.Linq;
using System.Reflection;
using System.Threading.Tasks;

namespace LogicAnalyzer.Dialogs
{
    public partial class CaptureDialog : Window
    {
        CheckBox[] captureChannels;
        RadioButton[] triggerChannels;
        byte mode = 0;
        public CaptureSettings SelectedSettings { get; private set; }

        public bool DisableFast 
        {
            get { return ckFastTrigger.IsEnabled; }
            set
            {
                ckFastTrigger.IsEnabled =! value;
                if(value)
                    ckFastTrigger.IsChecked = false;
            }
        }

        public CaptureDialog()
        {
            InitializeComponent();
            btnAccept.Click += btnAccept_Click;
            btnCancel.Click += btnCancel_Click;
            ddMode.SelectionChanged += DdMode_SelectionChanged;
            InitializeControlArrays();
            LoadSettings();
        }

        private void DdMode_SelectionChanged(object? sender, SelectionChangedEventArgs e)
        {
            mode = (byte)ddMode.SelectedIndex;

            switch (mode)
            {
                case 0:

                    for(int buc = 0; buc < 8; buc++)
                        captureChannels[buc].IsEnabled= true;

                    for (int buc = 8; buc < 24; buc++)
                    {
                        captureChannels[buc].IsEnabled = false;
                        captureChannels[buc].IsChecked = false;
                    }

                    nudPreSamples.Minimum = 2;
                    nudPreSamples.Maximum = 98303;
                    nudPostSamples.Minimum = 512;
                    nudPostSamples.Maximum = 131069;
                    break;

                case 1:

                    for (int buc = 0; buc < 16; buc++)
                        captureChannels[buc].IsEnabled = true;

                    for (int buc = 16; buc < 24; buc++)
                    {
                        captureChannels[buc].IsEnabled = false;
                        captureChannels[buc].IsChecked = false;
                    }

                    nudPreSamples.Minimum = 2;
                    nudPreSamples.Maximum = 49151;
                    nudPostSamples.Minimum = 512;
                    nudPostSamples.Maximum = 65533;
                    break;

                case 2:

                    for (int buc = 0; buc < 24; buc++)
                        captureChannels[buc].IsEnabled = true;

                    nudPreSamples.Minimum = 2;
                    nudPreSamples.Maximum = 24576;
                    nudPostSamples.Minimum = 512;
                    nudPostSamples.Maximum = 32765;
                    break;
            }

            if(nudPreSamples.Value > nudPreSamples.Maximum)
                nudPreSamples.Value = nudPreSamples.Maximum;

            if (nudPostSamples.Value > nudPostSamples.Maximum)
                nudPostSamples.Value = nudPostSamples.Maximum;
        }

        protected override void OnOpened(EventArgs e)
        {
            base.OnOpened(e);
            this.FixStartupPosition();
        }

        private void InitializeControlArrays()
        {
            List<CheckBox> channels = new List<CheckBox>();
            List<RadioButton> triggers = new List<RadioButton>();

            for (int buc = 1; buc < 25; buc++)
            {
                channels.Add(this.FindControl<CheckBox>($"ckCapture{buc}"));
                triggers.Add(this.FindControl<RadioButton>($"rbTrigger{buc}"));
            }

            captureChannels = channels.ToArray();
            triggerChannels = triggers.ToArray();
        }

        private void LoadSettings()
        {
            if (File.Exists("captureSettings.json"))
            {
                string data = File.ReadAllText("captureSettings.json");
                var settings = JsonConvert.DeserializeObject<CaptureSettings>(data);

                if (settings == null)
                    return;

                nudFrequency.Value = settings.Frequency;
                nudPreSamples.Value = settings.PreTriggerSamples;
                nudPostSamples.Value = settings.PostTriggerSamples;

                foreach (var channel in settings.CaptureChannels)
                    captureChannels[channel].IsChecked = true;

                switch (settings.TriggerType)
                {
                    case 0:
                        rbTriggerTypePattern.IsChecked = false;
                        rbTriggerTypeEdge.IsChecked = true;

                        triggerChannels[settings.TriggerChannel].IsChecked = true;
                        ckNegativeTrigger.IsChecked = settings.TriggerInverted;

                        rbTriggerTypePattern.IsChecked = false;
                        rbTriggerTypeEdge.IsChecked = true;

                        ckFastTrigger.IsChecked = false;

                        break;

                    case 1:
                        {
                            rbTriggerTypePattern.IsChecked = true;
                            rbTriggerTypeEdge.IsChecked = false;

                            nudTriggerBase.Value = settings.TriggerChannel + 1;
                            string pattern = "";

                            for (int buc = 0; buc < settings.TriggerBitCount; buc++)
                                pattern += (settings.TriggerPattern & (1 << buc)) == 0 ? "0" : "1";

                            txtPattern.Text = pattern;

                            ckFastTrigger.IsChecked = false;
                        }
                        break;

                    case 2:
                        {
                            rbTriggerTypePattern.IsChecked = true;
                            rbTriggerTypeEdge.IsChecked = false;

                            nudTriggerBase.Value = settings.TriggerChannel + 1;
                            string pattern = "";

                            for (int buc = 0; buc < settings.TriggerBitCount; buc++)
                                pattern += (settings.TriggerPattern & (1 << buc)) == 0 ? "0" : "1";

                            txtPattern.Text = pattern;

                            ckFastTrigger.IsChecked = true;
                        }
                        break;
                }

                ddMode.SelectedIndex = settings.CaptureMode;
            }
        }

        private async void btnAccept_Click(object? sender, RoutedEventArgs e)
        {
            int max = mode == 0 ? 131071 : (mode == 1 ? 65535 : 32767);

            if (nudPreSamples.Value + nudPostSamples.Value > max)
            {
                await ShowError("Error", $"Total samples cannot exceed {max}.");
                return;
            }

            List<int> channelsToCapture = new List<int>();

            for (int buc = 0; buc < captureChannels.Length; buc++)
            {
                if (captureChannels[buc].IsChecked == true)
                    channelsToCapture.Add(buc);
            }

            if (channelsToCapture.Count == 0)
            {
                await ShowError("Error", "Select at least one channel to be captured.");
                return;
            }

            int trigger = -1;
            int triggerBits = 0;

            UInt16 triggerPattern = 0;

            if (rbTriggerTypeEdge.IsChecked == true)
            {
                for (int buc = 0; buc < triggerChannels.Length; buc++)
                {
                    if (triggerChannels[buc].IsChecked == true)
                    {
                        if (trigger == -1)
                            trigger = buc;
                        else
                        {
                            await ShowError("Error", "Only one trigger channel supported.");
                            return;
                        }
                    }
                }
            }
            else
            {
                trigger = (int)nudTriggerBase.Value - 1;

                char[] patternChars = txtPattern.Text.ToArray();

                if (patternChars.Length == 0)
                {
                    await ShowError("Error", "Trigger pattern must be at least one bit long.");
                    return;
                }

                if (patternChars.Any(c => c != '0' && c != '1'))
                {
                    await ShowError("Error", "Trigger patterns must be composed only by 0's and 1's.");
                    return;
                }

                if ((trigger - 1) + patternChars.Length > 16)
                {
                    await ShowError("Error", "Only first 16 channels can be used in a pattern trigger.");
                    return;
                }

                if (ckFastTrigger.IsChecked == true && patternChars.Length > 5)
                {
                    await ShowError("Error", "Fast pattern matching is restricted to 5 channels.");
                    return;
                }

                for (int buc = 0; buc < patternChars.Length; buc++)
                {
                    if (patternChars[buc] == '1')
                        triggerPattern |= (UInt16)(1 << buc);
                }

                triggerBits = patternChars.Length;
            }

            if (trigger == -1)
            {
                await ShowError("Error", "You must select a trigger channel. How the heck did you managed to deselect all? ¬¬");
                return;
            }

            CaptureSettings settings = new CaptureSettings();

            settings.Frequency = (int)nudFrequency.Value;
            settings.PreTriggerSamples = (int)nudPreSamples.Value;
            settings.PostTriggerSamples = (int)nudPostSamples.Value;

            settings.TriggerType = rbTriggerTypePattern.IsChecked == true ? (ckFastTrigger.IsChecked == true ? 2 : 1) : 0;
            settings.TriggerPattern = triggerPattern;
            settings.TriggerBitCount = triggerBits;
            settings.TriggerChannel = trigger;
            settings.TriggerInverted = ckNegativeTrigger.IsChecked == true;

            settings.CaptureChannels = channelsToCapture.ToArray();
            settings.CaptureMode = mode;

            File.WriteAllText("captureSettings.json", JsonConvert.SerializeObject(settings));
            SelectedSettings = settings;
            this.Close(true);
        }

        private void btnCancel_Click(object? sender, EventArgs e)
        {
            this.Close(false);
        }

        private void rbTriggerTypeEdge_CheckedChanged(object sender, EventArgs e)
        {
            if (rbTriggerTypeEdge.IsChecked == true)
            {
                pnlEdge.IsEnabled = true;
                pnlComplex.IsEnabled = false;
            }
            else
            {
                pnlEdge.IsEnabled = false;
                pnlComplex.IsEnabled = true;
            }
        }

        private void ckFastTrigger_CheckedChanged(object sender, EventArgs e)
        {
            if (ckFastTrigger.IsChecked == true)
                txtPattern.MaxLength = 5;
            else
                txtPattern.MaxLength = 16;
        }

        private async Task ShowError(string Title, string Text)
        {
            var box = MessageBoxManager.GetMessageBoxStandardWindow(Title, Text, icon: MessageBox.Avalonia.Enums.Icon.Error);

            var prop = box.GetType().GetField("_window", BindingFlags.Instance | BindingFlags.NonPublic);
            var win = prop.GetValue(box) as Window;

            win.Icon = this.Icon;
            await box.ShowDialog(this);
        }
    }
}
