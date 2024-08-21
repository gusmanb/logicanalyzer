using Avalonia;
using Avalonia.Controls;
using Avalonia.Interactivity;
using Avalonia.Markup.Xaml;
using Avalonia.Media;
using LogicAnalyzer.Classes;
using LogicAnalyzer.Extensions;
using SigrokDecoderBridge;
using System;
using System.Collections.Generic;
using System.Linq;

namespace LogicAnalyzer.Dialogs
{
    public partial class SigrokOptionsDialog : Window
    {
        public SigrokOptionValue[]? SelectedOptions { get; private set; }
        public SigrokSelectedChannel[]? SelectedChannels { get; private set; }

        SigrokDecoderBase decoder;
        public SigrokDecoderBase Decoder { get { return decoder; } set { decoder = value; LoadControls(); } }

        AnalysisSettings? initialSettings;
        public AnalysisSettings? InitialSettings { get { return initialSettings; } set { initialSettings = value; LoadControls(); } }

        Channel[] channels;
        public Channel[] Channels { get { return channels; } set { channels = value; LoadControls(); } }

        public SigrokOptionsDialog()
        {
            InitializeComponent();
            btnAccept.IsEnabled = false;
            btnAccept.Click += btnAccept_Click;
            btnCancel.Click += btnCancel_Click;
        }
        protected override void OnOpened(EventArgs e)
        {
            base.OnOpened(e);
            this.FixStartupPosition();
        }

        void LoadControls()
        {
            pnlControls.Children.Clear();

            if (decoder == null)
                return;

            this.Title = $"{decoder.DecoderName} decoder settings";

            var signals = decoder?.Channels;

            if (signals != null && signals.Length > 0 && channels != null && channels.Length > 0)
            {

                List<string> channelsSource = new List<string>();

                channelsSource.Add("< None >");

                channelsSource.AddRange(channels.Select(c => c.ChannelName));

                for (int buc = 0; buc < signals.Length; buc++)
                {
                    var signal = signals[buc];

                    pnlControls.Children.Add(new TextBlock{ IsVisible = true, Name = $"Label_Signal{buc}", Text = $"Channel for signal { signal.Name }:" });

                    var list = new ComboBox { IsVisible = true, Name = $"List_Signal{buc}", ItemsSource = channelsSource.ToArray(), HorizontalAlignment=Avalonia.Layout.HorizontalAlignment.Stretch, Margin= new Thickness(0,10,20,0), Tag = "CHANNEL" };

                    if (initialSettings != null)
                    {
                        var chan = initialSettings.Channels?.FirstOrDefault(c => c.ChannelName == signal.Name);

                        if(chan != null)
                            list.SelectedIndex = chan.ChannelIndex + 1;
                    }

                    pnlControls.Children.Add(list);

                    list.SelectionChanged += SignalChannel_SelectedIndexChanged;

                    pnlControls.Children.Add(new Panel { HorizontalAlignment = Avalonia.Layout.HorizontalAlignment.Stretch, Background = Brushes.White, Height = 1, Margin = new Thickness(10) });
                }
            }

            var settings = decoder?.Options;

            if (settings != null && settings.Length > 0)
            {
                for (int buc = 0; buc < settings.Length; buc++)
                {
                    var set = settings[buc];

                    pnlControls.Children.Add(new TextBlock { IsVisible = true, Name = $"Label_Index{buc}", Text = set.Caption + ":"});

                    switch (set.SettingType)
                    {
                        case SigrokOptionType.Boolean:

                            var ck = new CheckBox { IsVisible = true, Name = $"Check_Index{buc}", Content = set.CheckCaption, Margin = new Thickness(0, 10, 20, 0) };
                            
                            if (initialSettings != null)
                            {
                                var setV = initialSettings.Settings?.FirstOrDefault(s => s.OptionIndex == buc);

                                if(setV != null)
                                    ck.IsChecked = (bool)(setV.Value ?? false);
                            }
                            else if(set.DefaultValue != null)
                            {
                                ck.IsChecked = (bool)set.DefaultValue;
                            }

                            pnlControls.Children.Add(ck);

                            ck.Checked += BooleanSetting_CheckedChanged;
                            break;

                        case SigrokOptionType.String:

                            var tb = new TextBox { IsVisible = true, Name = $"Text_Index{buc}", HorizontalAlignment = Avalonia.Layout.HorizontalAlignment.Stretch, Margin = new Thickness(0, 10, 20, 0) };

                            if (initialSettings != null)
                            {
                                var setV = initialSettings.Settings?.FirstOrDefault(s => s.OptionIndex == buc);

                                if (setV != null)
                                    tb.Text = setV.Value?.ToString() ?? "";
                            }
                            else if(set.DefaultValue != null)
                            {
                                tb.Text = set.DefaultValue.ToString();
                            }

                            pnlControls.Children.Add(tb);
                            tb.TextChanged += (s, e) => ValidateSettings();
                            break;

                        case SigrokOptionType.Integer:
                        case SigrokOptionType.Double:

                            var nud = new NumericUpDown { IsVisible = true, Name = $"Numeric_Index{buc}", Minimum = (decimal)set.MinimumValue, Maximum = (decimal)set.MaximumValue, HorizontalAlignment = Avalonia.Layout.HorizontalAlignment.Stretch, Margin = new Thickness(0, 10, 20, 0), Value = Math.Max((decimal)set.MinimumValue, 0) };

                            if(set.SettingType == SigrokOptionType.Double)
                                nud.FormatString = "0.00";

                            if (initialSettings != null)
                            {
                                var setV = initialSettings.Settings?.FirstOrDefault(s => s.OptionIndex == buc);

                                if (setV != null)
                                    nud.Value = Convert.ToDecimal(setV.Value ?? 0);
                            }
                            else if(set.DefaultValue != null)
                            {
                                nud.Value = Convert.ToDecimal(set.DefaultValue);
                            }

                            pnlControls.Children.Add(nud);
                            nud.ValueChanged += NumericSetting_ValueChanged;
                            break;

                        case SigrokOptionType.List:

                            var list = new ComboBox { IsVisible = true, Name = $"List_Index{buc}", ItemsSource = set.ListValues, HorizontalAlignment = Avalonia.Layout.HorizontalAlignment.Stretch, Margin = new Thickness(0, 10, 20, 0) };

                            if (initialSettings != null)
                            {
                                var setV = initialSettings.Settings?.FirstOrDefault(s => s.OptionIndex == buc);

                                if (setV != null)
                                    list.SelectedIndex = Array.IndexOf(set.ListValues, setV.Value);
                            }
                            else if(set.DefaultValue != null)
                            {
                                list.SelectedIndex = Array.IndexOf(set.ListValues, set.DefaultValue);
                            }

                            pnlControls.Children.Add(list);
                            list.SelectionChanged += ListSetting_SelectedIndexChanged;
                            break;


                    }

                    pnlControls.Children.Add(new Panel { HorizontalAlignment=Avalonia.Layout.HorizontalAlignment.Stretch, Background = Brushes.White, Height=1, Margin=new Thickness(10) });
                }
            }

            ValidateSettings();
        }

        private void ListSetting_SelectedIndexChanged(object? sender, RoutedEventArgs e)
        {
            ValidateSettings();
        }

        private void NumericSetting_ValueChanged(object? sender, RoutedEventArgs e)
        {
            ValidateSettings();
        }

        private void BooleanSetting_CheckedChanged(object? sender, RoutedEventArgs e)
        {
            ValidateSettings();
        }

        private void SignalChannel_SelectedIndexChanged(object? sender, SelectionChangedEventArgs e)
        {

            var cb = sender as ComboBox;

            if (cb == null)
                return;

            if (cb.SelectedIndex == 0)
                cb.SelectedIndex = -1;

            ValidateSettings();
        }

        void ValidateSettings()
        {
            var st = ComposeOptions();

            if (st == null)
            {
                btnAccept.IsEnabled = false;
                return;
            }

            var ch = ComposeChannels(st);

            if (ch == null)
            {
                btnAccept.IsEnabled = false;
                return;
            }

            if (decoder.ValidateOptions(st, ch))
            {
                btnAccept.IsEnabled = true;
            }
            else
            {
                btnAccept.IsEnabled = false;
            }


        }

        SigrokOptionValue[]? ComposeOptions()
        {
            if (decoder == null)
                return null;

            var settings = decoder.Options;

            if (settings == null)
                return new SigrokOptionValue[0];

            List<SigrokOptionValue> settingsValues = new List<SigrokOptionValue>();

            for (int buc = 0; buc < settings.Length; buc++)
            {
                var setting = settings[buc];
                object? value = null;

                switch (setting.SettingType)
                {
                    case SigrokOptionType.Boolean:

                        var ck = pnlControls.Children.Where(c => c.Name == $"Check_Index{buc}").FirstOrDefault() as CheckBox;

                        if (ck == null)
                            return null;

                        value = ck.IsChecked;

                        break;

                    case SigrokOptionType.String:

                        var tb = pnlControls.Children.Where(c => c.Name == $"Text_Index{buc}").FirstOrDefault() as TextBox;

                        if (tb == null)
                            return null;

                        value = tb.Text;

                        break;

                    case SigrokOptionType.Integer:

                        var nud = pnlControls.Children.Where(c => c.Name == $"Numeric_Index{buc}").FirstOrDefault() as NumericUpDown;

                        if (nud == null)
                            return null;

                        value = (int)nud.Value;

                        break;

                    case SigrokOptionType.Double:

                        var nudD = pnlControls.Children.Where(c => c.Name == $"Numeric_Index{buc}").FirstOrDefault() as NumericUpDown;

                        if (nudD == null)
                            return null;

                        value = (double)nudD.Value;

                        break;

                    case SigrokOptionType.List:

                        var list = pnlControls.Children.Where(c => c.Name == $"List_Index{buc}").FirstOrDefault() as ComboBox;

                        if (list == null)
                            return null;

                        value = (string)list.SelectedItem?.ToString();

                        break;

                }

                settingsValues.Add(new SigrokOptionValue
                {
                    OptionIndex = buc,
                    Value = value
                });
            }

            return settingsValues.ToArray();
        }

        SigrokSelectedChannel[]? ComposeChannels(SigrokOptionValue[] values)
        {
            if (decoder == null || this.channels == null)
                return null;

            var channels = decoder.Channels;

            List<SigrokSelectedChannel> selectedChannels = new List<SigrokSelectedChannel>();

            for (int buc = 0; buc < channels.Length; buc++)
            {
                var channel = channels[buc];
                var list = pnlControls.Children.Where(c => c.Name == $"List_Signal{buc}").FirstOrDefault() as ComboBox;

                if (list == null)
                    return null;

                if (list.SelectedIndex == -1)
                    continue;

                int idx = list.SelectedIndex - 1;

                selectedChannels.Add(new SigrokSelectedChannel
                {
                    ChannelIndex = idx,
                    ChannelName = channel.Name
                });
            }

            return selectedChannels.ToArray();
        }

        private void btnCancel_Click(object? sender, RoutedEventArgs e)
        {
            this.Close(false);
        }

        private void btnAccept_Click(object? sender, RoutedEventArgs e)
        {
            SelectedOptions = ComposeOptions();
            SelectedChannels = ComposeChannels(SelectedOptions);
            this.Close(true);
        }

        public class Channel
        {
            public required int ChannelIndex { get; set; }
            public required string ChannelName { get; set; }
        }
    }
}
