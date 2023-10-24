using Avalonia;
using Avalonia.Controls;
using Avalonia.Interactivity;
using Avalonia.Markup.Xaml;
using LogicAnalyzer.Classes;
using LogicAnalyzer.Controls;
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
        ChannelSelector[] captureChannels;
        RadioButton[] triggerChannels;
        CaptureLimits limits;
        IAnalizerDriver driver;
        public CaptureSettings SelectedSettings { get; private set; }

        string settingsFile;

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
        }

        public void Initialize(IAnalizerDriver Driver)
        {
            driver = Driver;
            SetDriverMode(driver.DriverType);
            InitializeControlArrays(driver.Channels);
            LoadSettings(driver.DriverType);
        }

        private void SetDriverMode(AnalyzerDriverType DriverType)
        {
            if (DriverType == AnalyzerDriverType.Multi)
            {
                pnlAllTriggers.Children.Remove(pnlPatternTrigger);
                pnlSingleTrigger.Children.Add(pnlPatternTrigger);
                pnlAllTriggers.IsVisible = false;
                pnlSingleTrigger.IsVisible = true;
                grdMainContainer.RowDefinitions = new RowDefinitions("4*,*");
            }
            else if (DriverType == AnalyzerDriverType.Emulated)
            {
                pnlAllTriggers.IsVisible = false;
                grdMainContainer.RowDefinitions = new RowDefinitions("1*");
                MaxHeight = MinHeight = Height = 410;
                grdBase.RowDefinitions = new RowDefinitions("1*,7*,1*");
            }
        }

        protected override void OnOpened(EventArgs e)
        {
            base.OnOpened(e);
            this.FixStartupPosition();
        }

        private void InitializeControlArrays(int ChannelCount)
        {
            List<ChannelSelector> channels = new List<ChannelSelector>();
            List<RadioButton> triggers = new List<RadioButton>();

            StackPanel currentPanel = new StackPanel();
            currentPanel.Orientation = Avalonia.Layout.Orientation.Horizontal;
            currentPanel.HorizontalAlignment = Avalonia.Layout.HorizontalAlignment.Center;
            int pannelChannel = 0;
            pnlChannels.Children.Add(currentPanel);
            for (int buc = 0; buc < ChannelCount; buc++)
            {
                if (pannelChannel == 8)
                {
                    pannelChannel = 0;
                    currentPanel = new StackPanel();
                    currentPanel.Orientation = Avalonia.Layout.Orientation.Horizontal;
                    currentPanel.HorizontalAlignment = Avalonia.Layout.HorizontalAlignment.Center;
                    pnlChannels.Children.Add(currentPanel);
                }

                var channel = new ChannelSelector { ChannelNumber = (byte)buc };
                currentPanel.Children.Add(channel);
                channel.Selected += Channel_Selected;
                channel.Deselected += Channel_Deselected;
                channels.Add(channel);
                triggers.Add(this.FindControl<RadioButton>($"rbTrigger{buc + 1}"));
                pannelChannel++;
            }

            captureChannels = channels.ToArray();
            triggerChannels = triggers.ToArray();
        }

        private void Channel_Deselected(object? sender, EventArgs e)
        {
            CheckMode();
        }

        private void Channel_Selected(object? sender, EventArgs e)
        {
            CheckMode();
        }

        private void CheckMode()
        {
            var enabledChannels = captureChannels.Where(c => c.Enabled).Select(c => (int)c.ChannelNumber).ToArray();
            limits = driver.GetLimits(enabledChannels);

            nudPreSamples.Minimum = limits.MinPreSamples;
            nudPreSamples.Maximum = limits.MaxPreSamples;
            nudPostSamples.Minimum = limits.MinPostSamples;
            nudPostSamples.Maximum = limits.MaxPostSamples;

            if (nudPreSamples.Value > limits.MaxPreSamples)
                nudPreSamples.Value = limits.MaxPreSamples;

            if (nudPostSamples.Value > limits.MaxPostSamples)
                nudPostSamples.Value = limits.MaxPostSamples;

        }

        private void LoadSettings(AnalyzerDriverType DriverType)
        {
            settingsFile = $"cpSettings{DriverType}.json";
            CaptureSettings? settings = AppSettingsManager.GetSettings<CaptureSettings>(settingsFile);

            if (settings != null)
            {
                nudFrequency.Value = settings.Frequency;
                nudPreSamples.Value = settings.PreTriggerSamples;
                nudPostSamples.Value = settings.PostTriggerSamples;

                foreach (var channel in settings.CaptureChannels)
                {
                    if (channel.ChannelNumber >= captureChannels.Length)
                        continue;

                    captureChannels[channel.ChannelNumber].Enabled = true;
                    captureChannels[channel.ChannelNumber].ChannelName = channel.ChannelName;
                }

                if (DriverType != AnalyzerDriverType.Emulated)
                {
                    switch (settings.TriggerType)
                    {
                        case 0:
                            rbTriggerTypePattern.IsChecked = false;
                            rbTriggerTypeEdge.IsChecked = true;

                            triggerChannels[settings.TriggerChannel].IsChecked = true;
                            ckNegativeTrigger.IsChecked = settings.TriggerInverted;
                            ckBurst.IsChecked = settings.LoopCount > 0;
                            nudBurstCount.Value = settings.LoopCount > 0 ? settings.LoopCount + 1 : 2;

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
                }
            }
        }

        private async void btnAccept_Click(object? sender, RoutedEventArgs e)
        {
            List<CaptureChannel> channelsToCapture = new List<CaptureChannel>();

            for (int buc = 0; buc < captureChannels.Length; buc++)
            {
                if (captureChannels[buc].Enabled == true)
                    channelsToCapture.Add(new CaptureChannel { ChannelName = captureChannels[buc].ChannelName, ChannelNumber = buc });
            }

            if (channelsToCapture.Count == 0)
            {
                await this.ShowError("Error", "Select at least one channel to be captured.");
                return;
            }

            int max = driver.GetLimits(channelsToCapture.Select(c => c.ChannelNumber).ToArray()).MaxTotalSamples;

            int loops = (int)((ckBurst.IsChecked ?? false) ? nudBurstCount.Value - 1 : 0);

            if (nudPreSamples.Value + (nudPostSamples.Value * (loops + 1)) > max)
            {
                await this.ShowError("Error", $"Total samples cannot exceed {max}.");
                return;
            }

            CaptureSettings settings = new CaptureSettings();

            if (driver.DriverType != AnalyzerDriverType.Emulated)
            {

                int trigger = -1;
                int triggerBits = 0;

                UInt16 triggerPattern = 0;

                if (driver.DriverType != AnalyzerDriverType.Multi && rbTriggerTypeEdge.IsChecked == true)
                {
                    for (int buc = 0; buc < triggerChannels.Length; buc++)
                    {
                        if (triggerChannels[buc].IsChecked == true)
                        {
                            if (trigger == -1)
                                trigger = buc;
                            else
                            {
                                await this.ShowError("Error", "Only one trigger channel supported.");
                                return;
                            }
                        }
                    }
                }
                else
                {
                    trigger = (int)nudTriggerBase.Value - 1;

                    if (string.IsNullOrWhiteSpace(txtPattern.Text))
                    {
                        await this.ShowError("Error", "Trigger pattern must be at least one bit long.");
                        return;
                    }

                    char[] patternChars = txtPattern.Text.Trim().ToArray();

                    if (patternChars.Length == 0)
                    {
                        await this.ShowError("Error", "Trigger pattern must be at least one bit long.");
                        return;
                    }

                    if (patternChars.Any(c => c != '0' && c != '1'))
                    {
                        await this.ShowError("Error", "Trigger patterns must be composed only by 0's and 1's.");
                        return;
                    }

                    if ((trigger - 1) + patternChars.Length > 16)
                    {
                        await this.ShowError("Error", "Only first 16 channels can be used in a pattern trigger.");
                        return;
                    }

                    if (ckFastTrigger.IsChecked == true && patternChars.Length > 5)
                    {
                        await this.ShowError("Error", "Fast pattern matching is restricted to 5 channels.");
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
                    await this.ShowError("Error", "You must select a trigger channel. How the heck did you managed to deselect all? ¬¬");
                    return;
                }

                settings.TriggerPattern = triggerPattern;
                settings.TriggerBitCount = triggerBits;
                settings.TriggerChannel = trigger;
            }

            switch (driver.DriverType)
            {
                case AnalyzerDriverType.Emulated:
                    settings.TriggerType = 0;
                    break;
                case AnalyzerDriverType.Multi:
                    settings.TriggerType = ckFastTrigger.IsChecked == true ? 2 : 1;
                    break;
                default:
                    settings.TriggerType = rbTriggerTypePattern.IsChecked == true ? (ckFastTrigger.IsChecked == true ? 2 : 1) : 0;
                    break;
            }
            

            settings.Frequency = (int)nudFrequency.Value;
            settings.PreTriggerSamples = (int)nudPreSamples.Value;
            settings.PostTriggerSamples = (int)nudPostSamples.Value;
            settings.LoopCount = loops;
            settings.TriggerInverted = ckNegativeTrigger.IsChecked == true;
            settings.CaptureChannels = channelsToCapture.ToArray();
            
            File.WriteAllText(settingsFile, JsonConvert.SerializeObject(settings));
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
                pnlPatternTrigger.IsEnabled = false;
            }
            else
            {
                pnlEdge.IsEnabled = false;
                pnlPatternTrigger.IsEnabled = true;
            }
        }

        private void ckFastTrigger_CheckedChanged(object sender, EventArgs e)
        {
            if (ckFastTrigger.IsChecked == true)
                txtPattern.MaxLength = 5;
            else
                txtPattern.MaxLength = 16;
        }
    }
}
