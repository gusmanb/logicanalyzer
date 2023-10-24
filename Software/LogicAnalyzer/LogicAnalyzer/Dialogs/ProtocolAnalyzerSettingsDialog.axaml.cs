using Avalonia;
using Avalonia.Controls;
using Avalonia.Interactivity;
using Avalonia.Markup.Xaml;
using Avalonia.Media;
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

                    pnlControls.Children.Add(new TextBlock{ IsVisible = true, Name = $"Label_Signal{buc}", Text = $"Channel for signal { signal.SignalName }:" });

                    var list = new ComboBox { IsVisible = true, Name = $"List_Signal{buc}", Items = channelsSource.ToArray(), HorizontalAlignment=Avalonia.Layout.HorizontalAlignment.Stretch, Margin= new Thickness(0,10,20,0) };

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
                            pnlControls.Children.Add(ck);
                            ck.Checked += BooleanSetting_CheckedChanged;
                            break;

                        case ProtocolAnalyzerSetting.ProtocolAnalyzerSettingType.Integer:

                            var nud = new NumericUpDown { IsVisible = true, Name = $"Numeric_Index{buc}", Minimum = set.IntegerMinimumValue, Maximum = set.IntegerMaximumValue, HorizontalAlignment = Avalonia.Layout.HorizontalAlignment.Stretch, Margin = new Thickness(0, 10, 20, 0) };
                            pnlControls.Children.Add(nud);
                            nud.ValueChanged += IntegerSetting_ValueChanged;
                            break;

                        case ProtocolAnalyzerSetting.ProtocolAnalyzerSettingType.List:

                            var list = new ComboBox { IsVisible = true, Name = $"List_Index{buc}", Items = set.ListValues, HorizontalAlignment = Avalonia.Layout.HorizontalAlignment.Stretch, Margin = new Thickness(0, 10, 20, 0) };
                            pnlControls.Children.Add(list);
                            list.SelectionChanged += ListSetting_SelectedIndexChanged;
                            break;


                    }

                    pnlControls.Children.Add(new Panel { HorizontalAlignment=Avalonia.Layout.HorizontalAlignment.Stretch, Background = Brushes.White, Height=1, Margin=new Thickness(10) });
                }
            }

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
            var ch = ComposeChannels();

            if (st == null || ch == null)
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

        ProtocolAnalyzerSelectedChannel[]? ComposeChannels()
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

                selectedChannels.Add(new ProtocolAnalyzerSelectedChannel
                {
                    ChannelIndex = list.SelectedIndex - 1,
                    SignalName = signal.SignalName
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
            SelectedSettings = ComposeSettings();
            SelectedChannels = ComposeChannels();
            this.Close(true);
        }

        public class Channel
        {
            public required int ChannelIndex { get; set; }
            public required string ChannelName { get; set; }
        }
    }
}
