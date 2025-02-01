using SharedDriver;
using System;
using System.Collections.Generic;
using System.Drawing;
using System.Linq;
using System.Text;
using System.Threading.Tasks;
using Terminal.Gui;

namespace TerminalCapture.Dialogs
{
    public class DeviceInfoDialog : Dialog
    {
        AnalyzerDeviceInfo _deviceInfo;
        public DeviceInfoDialog(AnalyzerDeviceInfo DeviceInfo)
        {
            _deviceInfo = DeviceInfo;

            Title = "Device Information";
            Width = 65;
            Height = 26;

            var lblType = new Label() { Text = $"Device: {_deviceInfo.Name}", Y = 1, Width = Dim.Percent(100), TextAlignment = Alignment.Center, ColorScheme = Colors.ColorSchemes["TitleLabel"] };

            var lblFreq = new Label() { Text = $"Max std rate: {FrequencyValue(_deviceInfo.MaxFrequency)}", Y = Pos.Bottom(lblType), X = 1 };
            var lblBlast = new Label() { Text = $"Max blast rate: {FrequencyValue(_deviceInfo.BlastFrequency)}", Y = Pos.Bottom(lblType) };
            lblBlast.X = Pos.Percent(100) - lblBlast.Text.Length - 1;

            var lblBuf = new Label() { Text = $"Buffer size: {_deviceInfo.BufferSize:#,##0}", Y = Pos.Bottom(lblFreq), X = 1 };
            var lblChan = new Label() { Text = $"Channels: {_deviceInfo.Channels}", Y = Pos.Bottom(lblFreq) };
            lblChan.X = Pos.Percent(100) - lblChan.Text.Length - 1;

            var lbl8BitMode = new Label() { Text = "8-bit mode", Y = Pos.Bottom(lblBuf) + 1, Width = Dim.Percent(100), TextAlignment = Alignment.Center, ColorScheme = Colors.ColorSchemes["TitleLabel"] };

            var lblMinPreEight = new Label() { Text = $"Min pre samples: {_deviceInfo.ModeLimits[0].MinPreSamples:#,##0}", Y = Pos.Bottom(lbl8BitMode), X = 1 };
            var lblMaxPreEight = new Label() { Text = $"Max pre samples: {_deviceInfo.ModeLimits[0].MaxPreSamples:#,##0}", Y = Pos.Bottom(lbl8BitMode) };
            lblMaxPreEight.X = Pos.Percent(100) - lblMaxPreEight.Text.Length - 1;

            var lblMinPostEight = new Label() { Text = $"Min post samples: {_deviceInfo.ModeLimits[0].MinPostSamples:#,##0}", Y = Pos.Bottom(lblMinPreEight), X = 1 };
            var lblMaxPostEight = new Label() { Text = $"Max post samples: {_deviceInfo.ModeLimits[0].MaxPostSamples:#,##0}", Y = Pos.Bottom(lblMinPreEight) };
            lblMaxPostEight.X = Pos.Percent(100) - lblMaxPostEight.Text.Length - 1;

            var lblMaxTotalEight = new Label() { Text = $"Max total samples: {_deviceInfo.ModeLimits[0].MaxTotalSamples:#,##0}", Y = Pos.Bottom(lblMinPostEight) };
            lblMaxTotalEight.X = Pos.Percent(50) - lblMaxTotalEight.Text.Length / 2;

            var lbl16BitMode = new Label() { Text = "16-bit mode", Y = Pos.Bottom(lblMaxTotalEight) + 1, Width = Dim.Percent(100), TextAlignment = Alignment.Center, ColorScheme = Colors.ColorSchemes["TitleLabel"] };

            var lblMinPreSixteen = new Label() { Text = $"Min pre samples: {_deviceInfo.ModeLimits[1].MinPreSamples:#,##0}", Y = Pos.Bottom(lbl16BitMode), X = 1 };
            var lblMaxPreSixteen = new Label() { Text = $"Max pre samples: {_deviceInfo.ModeLimits[1].MaxPreSamples:#,##0}", Y = Pos.Bottom(lbl16BitMode) };
            lblMaxPreSixteen.X = Pos.Percent(100) - lblMaxPreSixteen.Text.Length - 1;

            var lblMinPostSixteen = new Label() { Text = $"Min post samples: {_deviceInfo.ModeLimits[1].MinPostSamples:#,##0}", Y = Pos.Bottom(lblMinPreSixteen), X = 1 };
            var lblMaxPostSixteen = new Label() { Text = $"Max post samples: {_deviceInfo.ModeLimits[1].MaxPostSamples:#,##0}", Y = Pos.Bottom(lblMinPreSixteen) };
            lblMaxPostSixteen.X = Pos.Percent(100) - lblMaxPostSixteen.Text.Length - 1;

            var lblMaxTotalSixteen = new Label() { Text = $"Max total samples: {_deviceInfo.ModeLimits[1].MaxTotalSamples:#,##0}", Y = Pos.Bottom(lblMinPostSixteen) };
            lblMaxTotalSixteen.X = Pos.Percent(50) - lblMaxTotalSixteen.Text.Length / 2;

            var lbl24BitMode = new Label() { Text = "24-bit mode", Y = Pos.Bottom(lblMaxTotalSixteen) + 1, Width = Dim.Percent(100), TextAlignment = Alignment.Center, ColorScheme = Colors.ColorSchemes["TitleLabel"] };

            var lblMinPreTwentyFour = new Label() { Text = $"Min pre samples 24-bit: {_deviceInfo.ModeLimits[2].MinPreSamples:#,##0}", Y = Pos.Bottom(lbl24BitMode), X = 1 };
            var lblMaxPreTwentyFour = new Label() { Text = $"Max pre samples 24-bit: {_deviceInfo.ModeLimits[2].MaxPreSamples:#,##0}", Y = Pos.Bottom(lbl24BitMode) };
            lblMaxPreTwentyFour.X = Pos.Percent(100) - lblMaxPreTwentyFour.Text.Length - 1;

            var lblMinPostTwentyFour = new Label() { Text = $"Min post samples 24-bit: {_deviceInfo.ModeLimits[2].MinPostSamples:#,##0}", Y = Pos.Bottom(lblMinPreTwentyFour), X = 1 };
            var lblMaxPostTwentyFour = new Label() { Text = $"Max post samples 24-bit: {_deviceInfo.ModeLimits[2].MaxPostSamples:#,##0}", Y = Pos.Bottom(lblMinPreTwentyFour) };
            lblMaxPostTwentyFour.X = Pos.Percent(100) - lblMaxPostTwentyFour.Text.Length - 1;

            var lblMaxTotalTwentyFour = new Label() { Text = $"Max total samples 24-bit: {_deviceInfo.ModeLimits[2].MaxTotalSamples:#,##0}", Y = Pos.Bottom(lblMinPostTwentyFour) };
            lblMaxTotalTwentyFour.X = Pos.Percent(50) - lblMaxTotalTwentyFour.Text.Length / 2;

            var okButton = new Button() { Text = "Ok" };
            okButton.Accepting += (o, e) => { RequestStop(); };
            okButton.X = Pos.Percent(50) - 3;
            okButton.Y = Pos.Percent(100) - 2;

            Add(okButton, lblType, lblFreq, lblBlast, lblBuf, lblChan, lbl8BitMode, lblMinPreEight, lblMaxPreEight, lblMinPostEight, lblMaxPostEight, lblMaxTotalEight, lbl16BitMode, lblMinPreSixteen, lblMaxPreSixteen, lblMinPostSixteen, lblMaxPostSixteen, lblMaxTotalSixteen, lbl24BitMode, lblMinPreTwentyFour, lblMaxPreTwentyFour, lblMinPostTwentyFour, lblMaxPostTwentyFour, lblMaxTotalTwentyFour);
        }

        private string FrequencyValue(int Value)
        {
            if (Value < 1000)
                return Value.ToString("#,##0") + "Hz";
            else if (Value < 1000000)
                return (Value / 1000).ToString("#,##0") + "KHz";
            else
                return (Value / 1000000).ToString("#,##0") + "MHz";
        }
    }
}
