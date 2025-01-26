using System;
using System.Collections.Generic;
using System.Linq;
using System.Text;
using System.Threading.Tasks;
using Terminal.Gui;

namespace TerminalCapture.SettingsWizard
{
    public class PatternTriggerStep : WizardStep, IStepValidate
    {
        NumericUpDown _nudChannel;
        TextField _txtPattern;
        CheckBox _cbFast;

        int _channel;
        public int Channel { get { return _channel; } set { _channel = value; _nudChannel.Value = value + 1; } }

        string _pattern;
        public string Pattern { get { return _pattern; } set { _pattern = value; _txtPattern.Text = value; } }

        bool _fast;
        public bool Fast { get { return _fast; } set { _fast = value; _cbFast.CheckedState = value ? CheckState.Checked : CheckState.UnChecked; } }

        public PatternTriggerStep()
        {
            Title = "Pattern Trigger";
            HelpText = "Select the pattern that will trigger the capture.";

            Label lblChan = new Label { Text = "First channel: ", X = 1, Y = 1 };
            _nudChannel = new NumericUpDown { X = 21, Y = lblChan.Y, Value = 1, ColorScheme = Colors.ColorSchemes["EditableControl"] };
            _nudChannel.ValueChanging += (s, e) => { if (e.NewValue < 1 || e.NewValue > 16) e.Cancel = true; };
            Label lblPattern = new Label { Text = "Pattern: ", X = 1, Y = Pos.Bottom(lblChan) + 1 };
            _txtPattern = new TextField { X = 21, Y = lblPattern.Y, Width = 17, ColorScheme = Colors.ColorSchemes["EditableControl"] };

            _cbFast = new CheckBox() { X = 1, Y = Pos.Bottom(lblPattern) + 1, Text = "Fast trigger" };

            _txtPattern.TextChanging += (s, e) =>
            {
                if(e.NewValue.Any(c => c != '0' && c != '1'))
                {
                    e.Cancel = true;
                }

                if (e.NewValue.Length > 16)
                {
                    e.Cancel = true;
                }

                if(e.NewValue.Length > 5 && _cbFast.CheckedState == CheckState.Checked)
                {
                    e.Cancel = true;
                }
            };

            _cbFast.CheckedStateChanged += (s, e) =>
            {
                if (_txtPattern.Text.Length > 5 && _cbFast.CheckedState == CheckState.Checked)
                {
                    _txtPattern.Text = _txtPattern.Text.Substring(0, 5);
                }
            };

            Add(lblChan, _nudChannel, lblPattern, _txtPattern, _cbFast);
        }

        public void OnValidate(StepValidateArgs Args)
        {
            if(string.IsNullOrWhiteSpace(_txtPattern.Text))
            {
                MessageBox.ErrorQuery("Error", "Please enter a pattern", "Ok");
                return;
            }

            if(_txtPattern.Text.Length + _nudChannel.Value > 17)
            {
                MessageBox.ErrorQuery("Error", "The pattern trigger can only be used in the first 16 channels", "Ok");
                return;
            }

            if(_cbFast.CheckedState == CheckState.Checked && _txtPattern.Text.Length > 5)
            {
                MessageBox.ErrorQuery("Error", "Fast trigger can only be used with patterns up to 5 bits", "Ok");
                return;
            }

            _pattern = _txtPattern.Text;
            _channel = (int)_nudChannel.Value - 1;
            _fast = _cbFast.CheckedState == CheckState.Checked;

            Args.IsValid = true;
        }
    }
}
