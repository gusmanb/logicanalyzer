using Avalonia;
using Avalonia.Controls;
using Avalonia.Interactivity;
using Avalonia.Markup.Xaml;
using Avalonia.Media;
using LogicAnalyzer.Classes;
using LogicAnalyzer.Extensions;
using LogicAnalyzer.Protocols;
using System;
using System.Collections.Generic;
using System.Linq;

namespace LogicAnalyzer.Dialogs
{
    public partial class ProtocolAnalyzerSettingsDialog : Window
    {
        public ProtocolAnalyzerSettingValue[]? SelectedSettings { get; private set; }
        public ProtocolAnalyzerSelectedChannel[]? SelectedChannels { get; private set; }

        ProtocolAnalyzerBase analyzer;
        public ProtocolAnalyzerBase Analyzer { get { return analyzer; } set { analyzer = value; LoadControls(); } }

        AnalysisSettings? initialSettings;
        public AnalysisSettings? InitialSettings { get { return initialSettings; } set { initialSettings = value; LoadControls(); } }

        Channel[] channels;
        public Channel[] Channels { get { return channels; } set { channels = value; LoadControls(); } }


        public ProtocolAnalyzerSettingsDialog()
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

            if (analyzer == null)
                return;

            this.Title = $"{analyzer.ProtocolName} analyzer settings";

            var signals = analyzer?.Signals;

            if (signals != null && signals.Length > 0 && channels != null && channels.Length > 0)
            {

                List<string> channelsSource = new List<string>();

                channelsSource.Add("< None >");

                channelsSource.AddRange(channels.Select(c => c.ChannelName));

                for (int buc = 0; buc < signals.Length; buc++)
                {
                    var signal = signals[buc];

                    pnlControls.Children.Add(new TextBlock{ IsVisible = true, Name = $"Label_Signal{buc}", Text = signal.IsBus ? $"First channel of bus {signal.SignalName}" : $"Channel for signal { signal.SignalName }:" });

                    var list = new ComboBox { IsVisible = true, Name = $"List_Signal{buc}", Items = channelsSource.ToArray(), HorizontalAlignment=Avalonia.Layout.HorizontalAlignment.Stretch, Margin= new Thickness(0,10,20,0) };

                    if (initialSettings != null)
                    {
                        var chan = initialSettings.Channels?.FirstOrDefault(c => c.SignalName == signal.SignalName && c.BusIndex == 0);

                        if(chan != null)
                            list.SelectedIndex = chan.ChannelIndex + 1;
                    }

                    pnlControls.Children.Add(list);

                    list.SelectionChanged += SignalChannel_SelectedIndexChanged;

                    pnlControls.Children.Add(new Panel { HorizontalAlignment = Avalonia.Layout.HorizontalAlignment.Stretch, Background = Brushes.White, Height = 1, Margin = new Thickness(10) });
                }
            }

            var settings = analyzer?.Settings;

            if (settings != null && settings.Length > 0)
            {
                for (int buc = 0; buc < settings.Length; buc++)
                {
                    var set = settings[buc];

                    pnlControls.Children.Add(new TextBlock { IsVisible = true, Name = $"Label_Index{buc}", Text = set.Caption + ":"});

                    switch (set.SettingType)
                    {
                        case ProtocolAnalyzerSetting.ProtocolAnalyzerSettingType.Boolean:

                            var ck = new CheckBox { IsVisible = true, Name = $"Check_Index{buc}", Content = set.CheckCaption, Margin = new Thickness(0, 10, 20, 0) };
                            
                            if (initialSettings != null)
                            {
                                var setV = initialSettings.Settings?.FirstOrDefault(s => s.SettingIndex == buc);

                                if(setV != null)
                                    ck.IsChecked = (bool)(setV.Value ?? false);
                            }

                            pnlControls.Children.Add(ck);

                            ck.Checked += BooleanSetting_CheckedChanged;
                            break;

                        case ProtocolAnalyzerSetting.ProtocolAnalyzerSettingType.Integer:

                            var nud = new NumericUpDown { IsVisible = true, Name = $"Numeric_Index{buc}", Minimum = set.IntegerMinimumValue, Maximum = set.IntegerMaximumValue, HorizontalAlignment = Avalonia.Layout.HorizontalAlignment.Stretch, Margin = new Thickness(0, 10, 20, 0), Value = set.IntegerMinimumValue };

                            if (initialSettings != null)
                            {
                                var setV = initialSettings.Settings?.FirstOrDefault(s => s.SettingIndex == buc);

                                if (setV != null)
                                    nud.Value = (int)(setV.Value ?? 0);
                            }

                            pnlControls.Children.Add(nud);
                            nud.ValueChanged += IntegerSetting_ValueChanged;
                            break;

                        case ProtocolAnalyzerSetting.ProtocolAnalyzerSettingType.List:

                            var list = new ComboBox { IsVisible = true, Name = $"List_Index{buc}", Items = set.ListValues, HorizontalAlignment = Avalonia.Layout.HorizontalAlignment.Stretch, Margin = new Thickness(0, 10, 20, 0) };

                            if (initialSettings != null)
                            {
                                var setV = initialSettings.Settings?.FirstOrDefault(s => s.SettingIndex == buc);

                                if (setV != null)
                                    list.SelectedIndex = Array.IndexOf(set.ListValues, setV.Value);
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

        private void IntegerSetting_ValueChanged(object? sender, RoutedEventArgs e)
        {
            ValidateSettings();
        }

        private void BooleanSetting_CheckedChanged(object? sender, RoutedEventArgs e)
        {
            ValidateSettings();
        }

        private void SignalChannel_SelectedIndexChanged(object? sender, SelectionChangedEventArgs e)
        {
            ValidateSettings();
        }

        void ValidateSettings()
        {
            var st = ComposeSettings();

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

            if (analyzer.ValidateSettings(st, ch))
            {
                btnAccept.IsEnabled = true;
            }
            else
            {
                btnAccept.IsEnabled = false;
            }


        }

        ProtocolAnalyzerSettingValue[]? ComposeSettings()
        {
            if (analyzer == null)
                return null;

            var settings = analyzer.Settings;

            if (settings == null)
                return new ProtocolAnalyzerSettingValue[0];

            List<ProtocolAnalyzerSettingValue> settingsValues = new List<ProtocolAnalyzerSettingValue>();

            for (int buc = 0; buc < settings.Length; buc++)
            {
                var setting = settings[buc];
                object? value = null;

                switch (setting.SettingType)
                {
                    case ProtocolAnalyzerSetting.ProtocolAnalyzerSettingType.Boolean:

                        var ck = pnlControls.Children.Where(c => c.Name == $"Check_Index{buc}").FirstOrDefault() as CheckBox;

                        if (ck == null)
                            return null;

                        value = ck.IsChecked;

                        break;

                    case ProtocolAnalyzerSetting.ProtocolAnalyzerSettingType.Integer:

                        var nud = pnlControls.Children.Where(c => c.Name == $"Numeric_Index{buc}").FirstOrDefault() as NumericUpDown;

                        if (nud == null)
                            return null;

                        value = (int)nud.Value;

                        break;

                    case ProtocolAnalyzerSetting.ProtocolAnalyzerSettingType.List:

                        var list = pnlControls.Children.Where(c => c.Name == $"List_Index{buc}").FirstOrDefault() as ComboBox;

                        if (list == null)
                            return null;

                        value = (string)list.SelectedItem?.ToString();

                        break;

                }

                settingsValues.Add(new ProtocolAnalyzerSettingValue
                {
                    SettingIndex = buc,
                    Value = value
                });
            }

            return settingsValues.ToArray();
        }

        ProtocolAnalyzerSelectedChannel[]? ComposeChannels(ProtocolAnalyzerSettingValue[] values)
        {
            if (analyzer == null || channels == null)
                return null;

            var signals = analyzer.Signals;
            List<ProtocolAnalyzerSelectedChannel> selectedChannels = new List<ProtocolAnalyzerSelectedChannel>();

            for (int buc = 0; buc < signals.Length; buc++)
            {
                var signal = signals[buc];
                var list = pnlControls.Children.Where(c => c.Name == $"List_Signal{buc}").FirstOrDefault() as ComboBox;

                if (list == null)
                    return null;

                if (list.SelectedIndex == -1)
                    continue;

                var size = signal.IsBus ? analyzer.GetBusWidth(signal, values) : 1;

                if (size == 0)
                    continue;

                int idx = list.SelectedIndex - 1;

                if (idx + size > channels.Length)
                    return null;

                if (size == 1)
                {

                    selectedChannels.Add(new ProtocolAnalyzerSelectedChannel
                    {
                        ChannelIndex = idx,
                        SignalName = signal.SignalName
                    });
                }
                else
                {
                    for (int bucS = 0; bucS < size; bucS++)
                    {
                        selectedChannels.Add(new ProtocolAnalyzerSelectedChannel
                        {
                            ChannelIndex = idx + bucS,
                            SignalName = signal.SignalName,
                            BusIndex = bucS
                        });
                    }
                }
            }

            return selectedChannels.ToArray();
        }

        private void btnCancel_Click(object? sender, RoutedEventArgs e)
        {
            this.Close(false);
        }

        private void btnAccept_Click(object? sender, RoutedEventArgs e)
        {
            SelectedSettings = ComposeSettings();
            SelectedChannels = ComposeChannels(SelectedSettings);
            this.Close(true);
        }

        public class Channel
        {
            public required int ChannelIndex { get; set; }
            public required string ChannelName { get; set; }
        }
    }
}
