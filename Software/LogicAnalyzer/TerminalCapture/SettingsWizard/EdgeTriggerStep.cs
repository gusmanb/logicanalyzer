using System;
using System.Collections.Generic;
using System.Collections.ObjectModel;
using System.Linq;
using System.Text;
using System.Threading.Tasks;
using Terminal.Gui;

namespace TerminalCapture.SettingsWizard
{
    public class EdgeTriggerStep : WizardStep, IStepValidate
    {
        NumericUpDown _nudChannel;
        NumericUpDown _nudBursts;
        CheckBox _cbEdge;
        CheckBox _cbBlast;
        CheckBox _cbBurst;
        CheckBox _cbMeasure;

        int _channel;
        public int Channel { get { return _channel; } set { _channel = value; _nudChannel.Value = value + 1; } }

        bool _edge;
        public bool NegativeEdge { get { return _edge; } set { _edge = value; _cbEdge.CheckedState = value ? CheckState.Checked : CheckState.UnChecked; } }

        bool _blast;
        public bool Blast { get { return _blast; } set { _blast = value; _cbBlast.CheckedState = value ? CheckState.Checked : CheckState.UnChecked; } }

        bool _burst;
        public bool Burst { get { return _burst; } set { _burst = value; _cbBurst.CheckedState = value ? CheckState.Checked : CheckState.UnChecked; } }

        int _bursts;
        public int Bursts { get { return _bursts; } set { _bursts = value; _nudBursts.Value = value; } }

        bool _measure;
        public bool Measure { get { return _measure; } set { _measure = value; _cbMeasure.CheckedState = value ? CheckState.Checked : CheckState.UnChecked; } }

        bool _blastOnly;
        public bool BlastOnly { get { return _blastOnly; } set{ _blastOnly = value; UpdateBlastOnly(); } }

        public EdgeTriggerStep()
        {

            int secondCol = 21;

            Title = "Edge Trigger";
            HelpText = "Select the channel and the value that will trigger the capture. Also you can enable the burst mode and blast mode for this type of trigger. Remember that if you capture in CSV mode all the information regarding burst triggers and delays will be lost.";

            Label lblChan = new Label { Text = "Trigger channel: ", X = 1, Y = 1 };
            _nudChannel = new NumericUpDown { X = secondCol, Y = lblChan.Y, Value = 1, ColorScheme = Colors.ColorSchemes["EditableControl"] };
            _nudChannel.ValueChanging += (s, e) => { if (e.NewValue < 1 || e.NewValue > 24) e.Cancel = true; };


            _cbEdge = new CheckBox() { X = 1, Y = Pos.Bottom(lblChan) + 1, Text = "Negative edge" };
            _cbBlast = new CheckBox() { X = 1, Y = Pos.Bottom(_cbEdge) + 1, Text = "Enable blast mode" };
            _cbBurst = new CheckBox() { X = 1, Y = Pos.Bottom(_cbBlast) + 1, Text = "Enable burst mode" };

            Label lblBursts = new Label { Text = "Bursts: ", X = 1, Y = Pos.Bottom(_cbBurst) + 1 };
            _nudBursts = new NumericUpDown { X = secondCol, Y = lblBursts.Y, Value = 1, ColorScheme = Colors.ColorSchemes["EditableControl"] };
            _nudBursts.ValueChanging += (s, e) => { if (e.NewValue < 1 || e.NewValue > 254) e.Cancel = true; };

            _cbMeasure = new CheckBox() { X = 1, Y = Pos.Bottom(lblBursts) + 1, Text = "Measure delay" };


            _cbBlast.CheckedStateChanged += (s, e) => { _cbBurst.Enabled = _cbBlast.CheckedState == CheckState.UnChecked; };
            _cbBurst.CheckedStateChanged += (s, e) => { _nudBursts.Enabled = _cbBurst.CheckedState == CheckState.Checked; };

            Add(lblChan, _nudChannel, _cbEdge, _cbBlast, _cbBurst, lblBursts, _nudBursts, _cbMeasure);

        }

        void UpdateBlastOnly()
        {
            if (_blastOnly)
            {
                _cbBlast.CheckedState = CheckState.Checked;
                _cbBlast.Enabled = false;
                _cbBurst.Enabled = false;
                _nudBursts.Enabled = false;
            }
            else
            {
                _cbBlast.Enabled = true;
                _cbBurst.Enabled = _cbBlast.CheckedState == CheckState.UnChecked;
                _nudBursts.Enabled = _cbBurst.CheckedState == CheckState.Checked;
            }
        }

        public void OnValidate(StepValidateArgs Args)
        {
            _channel = (int)_nudChannel.Value - 1;
            _edge = _cbEdge.CheckedState == CheckState.Checked;
            _blast = _cbBlast.CheckedState == CheckState.Checked;
            _burst = _cbBurst.CheckedState == CheckState.Checked;
            _bursts = (int)_nudBursts.Value;
            _measure = _cbMeasure.CheckedState == CheckState.Checked;

            Args.IsValid = true;
        }
    }
}
