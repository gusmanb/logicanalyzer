using Avalonia;
using Avalonia.Controls;
using Avalonia.Interactivity;
using Avalonia.Markup.Xaml;
using Avalonia.Media;
using Avalonia.Threading;
using LogicAnalyzer.Classes;
using LogicAnalyzer.Controls;
using LogicAnalyzer.Extensions;
using Newtonsoft.Json;
using SharedDriver;
using System;
using System.Collections.Generic;
using System.IO;
using System.Linq;
using System.Reflection;
using System.Threading.Tasks;
using static System.Collections.Specialized.BitVector32;

namespace LogicAnalyzer.Dialogs
{
    public partial class CaptureDialog : Window
    {
        ChannelSelector[] captureChannels;
        RadioButton[] triggerChannels;
        CaptureLimits limits;
        AnalyzerDriverBase driver;

        Color lowJitter = new Color(255, 27, 128, 5);
        Color mediumJitter = new Color(255, 163, 81, 10);
        Color highJitter = new Color(255, 184, 0, 0);
        public CaptureSession SelectedSettings { get; private set; }

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
            btnReset.Click += btnReset_Click;
            rbTriggerTypeEdge.IsCheckedChanged += rbTriggerTypeEdge_CheckedChanged;
            nudFrequency.ValueChanged += NudFrequency_ValueChanged;
            ckBlast.IsCheckedChanged += ckBlast_CheckedChanged;
        }

        private void NudFrequency_ValueChanged(object? sender, NumericUpDownValueChangedEventArgs e)
        {
            ComputeJitter();
        }

        private void ComputeJitter()
        {
            double selFreq = (double)(nudFrequency.Value ?? 0);

            if(selFreq == 0)
                return;

            double div = (int)(driver.MaxFrequency / (double)(nudFrequency.Value ?? 0));
            double intFreq = driver.MaxFrequency / div;
            double diff = intFreq - selFreq;
            
            double pct = (diff * 100.0) / selFreq;

            string text = $"Jitter: {pct:F3}%";
            lblJitter.Text = text;
            
            if(pct < 1)
                brdJitter.Background = GraphicObjectsCache.GetBrush(lowJitter);
            else if (pct < 10)
                brdJitter.Background = GraphicObjectsCache.GetBrush(mediumJitter);
            else
                brdJitter.Background = GraphicObjectsCache.GetBrush(highJitter);

        }

        public void Initialize(AnalyzerDriverBase Driver)
        {
            driver = Driver;
            SetDriverMode(driver.DriverType);
            InitializeControlArrays(driver.ChannelCount);
            InitializeParameters();
            LoadSettings(driver.DriverType);
            CheckMode();
        }

        private void InitializeParameters()
        {
            nudFrequency.Minimum = driver.MinFrequency;
            nudFrequency.Maximum = driver.MaxFrequency;

            nudFrequency.Value = Math.Min(Math.Max(nudFrequency.Minimum, nudFrequency.Value ?? 0), nudFrequency.Maximum);
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
                channel.ChangeColor += Channel_ChangeColor;
                channels.Add(channel);
                triggers.Add(this.FindControl<RadioButton>($"rbTrigger{buc + 1}"));
                pannelChannel++;
            }

            captureChannels = channels.ToArray();
            triggerChannels = triggers.ToArray();
        }

        private void Channel_ChangeColor(object? sender, EventArgs e)
        {
            _ = Task.Run(async () => 
            {
                await Task.Delay(150);

                await Dispatcher.UIThread.InvokeAsync(async () =>
                {
                    var chan = sender as ChannelSelector;

                    if (chan == null)
                        return;

                    var picker = new ColorPickerDialog(); //ColorPickerWindow();

                    if (chan.ChannelColor != null)
                        picker.PickerColor = Color.FromUInt32(chan.ChannelColor.Value);
                    else
                        picker.PickerColor = AnalyzerColors.GetColor(chan.ChannelNumber);

                    var color = await picker.ShowDialog<Color?>(this);

                    if (color == null)
                        return;

                    chan.ChannelColor = color.Value.ToUInt32();
                });
            });
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

            if (!ckBlast.IsChecked ?? false)
            {
                nudPreSamples.Minimum = limits.MinPreSamples;
                nudPreSamples.Maximum = limits.MaxPreSamples;

                if (nudPreSamples.Value > limits.MaxPreSamples)
                    nudPreSamples.Value = limits.MaxPreSamples;
            }

            nudPostSamples.Minimum = limits.MinPostSamples;
            nudPostSamples.Maximum = limits.MaxPostSamples;

            if (nudPostSamples.Value > limits.MaxPostSamples)
                nudPostSamples.Value = limits.MaxPostSamples;
            
        }

        private void LoadSettings(AnalyzerDriverType DriverType)
        {
            settingsFile = $"cpSettings{DriverType}.json";
            CaptureSession? settings = AppSettingsManager.GetSettings<CaptureSession>(settingsFile);

            if (settings != null)
            {
                foreach (var channel in settings.CaptureChannels)
                {
                    if (channel.ChannelNumber >= captureChannels.Length)
                        continue;

                    captureChannels[channel.ChannelNumber].Enabled = true;
                    captureChannels[channel.ChannelNumber].ChannelName = channel.ChannelName;
                    captureChannels[channel.ChannelNumber].ChannelColor = channel.ChannelColor;
                }

                if (settings.TriggerType == TriggerType.Blast)
                {
                    SetBlastMode(true);
                    ckBlast.IsChecked = true;
                }
                else
                {
                    nudFrequency.Value = settings.Frequency;
                    nudPreSamples.Value = settings.PreTriggerSamples;
                    nudPostSamples.Value = settings.PostTriggerSamples;
                    ckBlast.IsChecked = false;
                }

                if (DriverType != AnalyzerDriverType.Emulated)
                {
                    switch (settings.TriggerType)
                    {
                        case TriggerType.Edge:
                        case TriggerType.Blast:

                            rbTriggerTypePattern.IsChecked = false;
                            rbTriggerTypeEdge.IsChecked = true;
                            triggerChannels[settings.TriggerChannel].IsChecked = true;
                            ckNegativeTrigger.IsChecked = settings.TriggerInverted;
                            ckBurst.IsChecked = settings.LoopCount > 0;
                            nudBurstCount.Value = settings.LoopCount > 0 ? settings.LoopCount + 1 : 2;
                            ckMeasure.IsChecked = settings.LoopCount > 0 ? settings.MeasureBursts : false;
                            rbTriggerTypePattern.IsChecked = false;
                            rbTriggerTypeEdge.IsChecked = true;
                            pnlEdge.IsEnabled = true;
                            pnlPatternTrigger.IsEnabled = false;
                            ckFastTrigger.IsChecked = false;

                            break;

                        case TriggerType.Complex:
                            {
                                rbTriggerTypePattern.IsChecked = true;
                                rbTriggerTypeEdge.IsChecked = false;

                                nudTriggerBase.Value = settings.TriggerChannel + 1;
                                string pattern = "";

                                for (int buc = 0; buc < settings.TriggerBitCount; buc++)
                                    pattern += (settings.TriggerPattern & (1 << buc)) == 0 ? "0" : "1";

                                txtPattern.Text = pattern;

                                ckFastTrigger.IsChecked = false;
                                pnlEdge.IsEnabled = false;
                                pnlPatternTrigger.IsEnabled = true;
                            }
                            break;

                        case TriggerType.Fast:
                            {
                                rbTriggerTypePattern.IsChecked = true;
                                rbTriggerTypeEdge.IsChecked = false;

                                nudTriggerBase.Value = settings.TriggerChannel + 1;
                                string pattern = "";

                                for (int buc = 0; buc < settings.TriggerBitCount; buc++)
                                    pattern += (settings.TriggerPattern & (1 << buc)) == 0 ? "0" : "1";

                                txtPattern.Text = pattern;

                                ckFastTrigger.IsChecked = true;
                                pnlEdge.IsEnabled = false;
                                pnlPatternTrigger.IsEnabled = true;
                            }
                            break;
                    }
                }
            }
        }

        private async void btnAccept_Click(object? sender, RoutedEventArgs e)
        {
            List<AnalyzerChannel> channelsToCapture = new List<AnalyzerChannel>();

            for (int buc = 0; buc < captureChannels.Length; buc++)
            {
                if (captureChannels[buc].Enabled == true)
                    channelsToCapture.Add(new AnalyzerChannel { ChannelName = captureChannels[buc].ChannelName, ChannelNumber = buc, ChannelColor = captureChannels[buc].ChannelColor });
            }

            if (channelsToCapture.Count == 0)
            {
                await this.ShowError("Error", "Select at least one channel to be captured.");
                return;
            }

            int max = driver.GetLimits(channelsToCapture.Select(c => c.ChannelNumber).ToArray()).MaxTotalSamples;

            int loops = (int)((ckBurst.IsChecked ?? false) ? nudBurstCount.Value - 1 : 0);
            bool measure = (ckBurst.IsChecked ?? false) && (ckMeasure.IsChecked ?? false);

            if (nudPreSamples.Value + (nudPostSamples.Value * (loops + 1)) > max)
            {
                await this.ShowError("Error", $"Total samples cannot exceed {max}.");
                return;
            }

            CaptureSession settings = new CaptureSession();

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
                    settings.TriggerType = TriggerType.Edge;
                    break;
                case AnalyzerDriverType.Multi:
                    settings.TriggerType = ckFastTrigger.IsChecked == true ? TriggerType.Fast : TriggerType.Complex;
                    break;
                default:
                    settings.TriggerType = rbTriggerTypePattern.IsChecked == true ? (ckFastTrigger.IsChecked == true ? TriggerType.Fast : TriggerType.Complex) : (ckBlast.IsChecked == true ? TriggerType.Blast : TriggerType.Edge);
                    break;
            }
            

            settings.Frequency = (int)nudFrequency.Value;
            settings.PreTriggerSamples = (int)nudPreSamples.Value;
            settings.PostTriggerSamples = (int)nudPostSamples.Value;
            settings.LoopCount = loops;
            settings.MeasureBursts = measure;
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

        private void btnReset_Click(object? sender, EventArgs e)
        {
            SetBlastMode(false);
            nudFrequency.Value = driver.MaxFrequency;
            nudPreSamples.Value = 512;
            nudPostSamples.Value = 1024;
            ckBurst.IsChecked = false;
            rbTrigger1.IsChecked = true;
            ckNegativeTrigger.IsChecked = false;
            ckMeasure.IsChecked = false;
            txtPattern.Text = "";
            ckFastTrigger.IsChecked = false;
            rbTriggerTypeEdge.IsChecked = true;

            foreach (var channel in captureChannels)
            {
                channel.Enabled = false;
                channel.ChannelName = "";
                channel.ChannelColor = null;
            }
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
                ckBlast.IsChecked = false;
                SetBlastMode(false);
            }
        }

        private void ckFastTrigger_CheckedChanged(object sender, EventArgs e)
        {
            if (ckFastTrigger.IsChecked == true)
                txtPattern.MaxLength = 5;
            else
                txtPattern.MaxLength = 16;
        }

        private void ckBlast_CheckedChanged(object sender, EventArgs e)
        {
            SetBlastMode(ckBlast.IsChecked ?? false);
        }

        private void SetBlastMode(bool Enabled)
        {
            if (Enabled)
            {
                nudFrequency.Minimum = driver.BlastFrequency;
                nudFrequency.Maximum = driver.BlastFrequency;
                nudFrequency.Value = driver.BlastFrequency;
                nudFrequency.IsEnabled = false;

                nudPreSamples.Minimum = 0;
                nudPreSamples.Maximum = 0;
                nudPreSamples.Value = 0;
                nudPreSamples.IsEnabled = false;

                var enabledChannels = captureChannels.Where(c => c.Enabled).Select(c => (int)c.ChannelNumber).ToArray();
                var limits = driver.GetLimits(enabledChannels);

                nudPostSamples.Minimum = limits.MinPostSamples;
                nudPostSamples.Maximum = limits.MaxPostSamples;

                if (nudPostSamples.Value > limits.MaxPostSamples)
                    nudPostSamples.Value = limits.MaxPostSamples;

                ckBurst.IsChecked = false;
                ckBurst.IsEnabled = false;
                ckMeasure.IsChecked = false;
                ckMeasure.IsEnabled = false;
                nudBurstCount.IsEnabled = false;

                lblJitter.Text = "Jitter: 0.000%";
                brdJitter.Background = GraphicObjectsCache.GetBrush(lowJitter);
            }
            else
            {
                nudFrequency.Minimum = driver.MinFrequency;
                nudFrequency.Maximum = driver.MaxFrequency;

                if(nudFrequency.Value > driver.MaxFrequency)
                    nudFrequency.Value = driver.MaxFrequency;

                nudFrequency.IsEnabled = true;

                nudPreSamples.Minimum = limits.MinPreSamples;
                nudPreSamples.Maximum = limits.MaxPreSamples;
                
                if (nudPreSamples.Value > limits.MaxPreSamples)
                    nudPreSamples.Value = limits.MaxPreSamples;

                if (nudPreSamples.Value < limits.MinPreSamples)
                    nudPreSamples.Value = limits.MinPreSamples;

                nudPreSamples.IsEnabled = true;

                nudPostSamples.Minimum = limits.MinPostSamples;
                nudPostSamples.Maximum = limits.MaxPostSamples;

                if (nudPostSamples.Value > limits.MaxPostSamples)
                    nudPostSamples.Value = limits.MaxPostSamples;

                nudPostSamples.IsEnabled = true;

                ckBurst.IsEnabled = true;
            }
        }
    }
}
