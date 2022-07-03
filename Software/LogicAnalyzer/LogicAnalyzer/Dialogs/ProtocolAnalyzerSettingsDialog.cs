using LogicAnalyzer.Protocols;
using System;
using System.Collections.Generic;
using System.ComponentModel;
using System.Data;
using System.Drawing;
using System.Linq;
using System.Text;
using System.Threading.Tasks;
using System.Windows.Forms;

namespace LogicAnalyzer
{
    public partial class ProtocolAnalyzerSettingsDialog : Form
    {
        public ProtocolAnalyzerSettingValue[]? SelectedSettings { get; private set; }
        public ProtocolAnalyzerSelectedChannel[]? SelectedChannels { get; private set; }

        ProtocolAnalyzerBase analyzer;
        public ProtocolAnalyzerBase Analyzer { get { return analyzer; } set { analyzer = value; LoadControls(); } }

        int[] channels;
        public int[] Channels { get { return channels; } set { channels = value; LoadControls(); } }


        public ProtocolAnalyzerSettingsDialog()
        {
            InitializeComponent();
        }
        void LoadControls()
        {
            flSettings.Controls.Clear();

            if (analyzer == null)
                return;

            this.Text = $"{analyzer.ProtocolName} analyzer settings";

            var signals = analyzer?.Signals;

            if (signals != null && signals.Length > 0 && channels != null && channels.Length > 0)
            {

                List<string> channelsSource = new List<string>();

                channelsSource.Add("< None >");

                channelsSource.AddRange(channels.Select(c => $"Channel {c + 1}"));

                for (int buc = 0; buc < signals.Length; buc++)
                {
                    var signal = signals[buc];

                    flSettings.Controls.Add(new Label { Visible = true, Name = $"Label_Signal{buc}", Text = $"Channel for signal { signal.SignalName }:", AutoSize = true });

                    var list = new ComboBox { Visible = true, Name = $"List_Signal{buc}", DropDownStyle = ComboBoxStyle.DropDownList, DataSource = channelsSource.ToArray(), Width = flSettings.Width - 32 };

                    flSettings.Controls.Add(list);

                    list.SelectedIndexChanged += SignalChannel_SelectedIndexChanged;

                    flSettings.Controls.Add(new DividerLabel { Visible = true, Name = $"Divider_Signal{buc}", LineStyle = Border3DStyle.Bump, Width = flSettings.Width - 32 });
                }
            }

            var settings = analyzer?.Settings;

            if (settings != null && settings.Length > 0)
            {
                for (int buc = 0; buc < settings.Length; buc++)
                {
                    var set = settings[buc];

                    flSettings.Controls.Add(new Label { Visible = true, Name = $"Label_Index{buc}", Text = set.Caption + ":", AutoSize = true });

                    switch (set.SettingType)
                    {
                        case ProtocolAnalyzerSetting.ProtocolAnalyzerSettingType.Boolean:

                            var ck = new CheckBox { Visible = true, Name = $"Check_Index{buc}", Text = set.CheckCaption };
                            flSettings.Controls.Add(ck);
                            ck.CheckedChanged += BooleanSetting_CheckedChanged;
                            break;

                        case ProtocolAnalyzerSetting.ProtocolAnalyzerSettingType.Integer:

                            var nud = new NumericUpDown { Visible = true, Name = $"Numeric_Index{buc}", Minimum = set.IntegerMinimumValue, Maximum = set.IntegerMaximumValue, Width = flSettings.Width - 32 };
                            flSettings.Controls.Add(nud);
                            nud.ValueChanged += IntegerSetting_ValueChanged;
                            break;

                        case ProtocolAnalyzerSetting.ProtocolAnalyzerSettingType.List:

                            var list = new ComboBox { Visible = true, Name = $"List_Index{buc}", DropDownStyle = ComboBoxStyle.DropDownList, DataSource = set.ListValues, Width = flSettings.Width - 32 };
                            flSettings.Controls.Add(list);
                            list.SelectedIndexChanged += ListSetting_SelectedIndexChanged;
                            break;


                    }

                    flSettings.Controls.Add(new DividerLabel { Visible = true, Name = $"Divider_Index{buc}", LineStyle = Border3DStyle.Bump, Width = flSettings.Width - 32 });
                }
            }
        }

        private void ListSetting_SelectedIndexChanged(object? sender, EventArgs e)
        {
            ValidateSettings();
        }

        private void IntegerSetting_ValueChanged(object? sender, EventArgs e)
        {
            ValidateSettings();
        }

        private void BooleanSetting_CheckedChanged(object? sender, EventArgs e)
        {
            ValidateSettings();
        }

        private void SignalChannel_SelectedIndexChanged(object? sender, EventArgs e)
        {
            ValidateSettings();
        }

        void ValidateSettings()
        {
            var st = ComposeSettings();
            var ch = ComposeChannels();

            if (st == null || ch == null)
            {
                btnAccept.Enabled = false;
                return;
            }

            if (analyzer.ValidateSettings(st, ch))
            {
                btnAccept.Enabled = true;
            }
            else
            {
                btnAccept.Enabled = false;
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

                        var ck = flSettings.Controls.Find($"Check_Index{buc}", false).FirstOrDefault() as CheckBox;

                        if (ck == null)
                            return null;

                        value = ck.Checked;

                        break;

                    case ProtocolAnalyzerSetting.ProtocolAnalyzerSettingType.Integer:

                        var  nud = flSettings.Controls.Find($"Numeric_Index{buc}", false).FirstOrDefault() as NumericUpDown;

                        if (nud == null)
                            return null;

                        value = (int)nud.Value;

                        break;

                    case ProtocolAnalyzerSetting.ProtocolAnalyzerSettingType.List:

                        var list = flSettings.Controls.Find($"List_Index{buc}", false).FirstOrDefault() as ComboBox;

                        if (list == null)
                            return null;

                        value = (string)list.SelectedItem;

                        break;

                }

                settingsValues.Add( new ProtocolAnalyzerSettingValue
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
                var list = flSettings.Controls.Find($"List_Signal{buc}", false).FirstOrDefault() as ComboBox;

                if (list == null)
                    return null;

                selectedChannels.Add(new ProtocolAnalyzerSelectedChannel
                {
                    ChannelIndex = list.SelectedIndex - 1,
                    SignalName = signal.SignalName
                });
            }

            return selectedChannels.ToArray();
        }

        private void btnCancel_Click(object sender, EventArgs e)
        {
            this.DialogResult = DialogResult.Cancel;
            this.Close();
        }

        private void btnAccept_Click(object sender, EventArgs e)
        {
            SelectedSettings = ComposeSettings();
            SelectedChannels = ComposeChannels();
            this.DialogResult = DialogResult.OK;
            this.Close();
        }
    }
}
