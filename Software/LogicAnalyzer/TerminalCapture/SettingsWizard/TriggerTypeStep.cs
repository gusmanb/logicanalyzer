using System;
using System.Collections.Generic;
using System.Linq;
using System.Text;
using System.Threading.Tasks;
using Terminal.Gui;

namespace TerminalCapture.SettingsWizard
{
    public class TriggerTypeStep : WizardStep, IStepValidate
    {
        int _selectedTrigger;
        public TriggerType SelectedTrigger { get { return (TriggerType)_selectedTrigger; } set { _selectedTrigger = (int)value; _rgTrigger.SelectedItem = (int)value; } }

        RadioGroup _rgTrigger;

        public TriggerTypeStep()
        {
            Title = "Trigger Type";
            HelpText = "Select the trigger type you want to use. Edge trigger will start capturing data when the specified channel takes the specified value, pattern trigger will start capturing data when the specified pattern is found.";

            _rgTrigger = new RadioGroup()
            { X = 1, Y = 1, Orientation = Orientation.Vertical, RadioLabels = new string[] { "Edge trigger", "Pattern trigger" } };

            Add(_rgTrigger);
        }

        public void OnValidate(StepValidateArgs Args)
        {

            if (_rgTrigger.SelectedItem == -1)
            {
                MessageBox.ErrorQuery("Error", "Please select a trigger type", "Ok");
                return;
            }

            _selectedTrigger = _rgTrigger.SelectedItem;

            var nextSteps = Args.Sequence;

            if (nextSteps != null)
            {
                if (_selectedTrigger == 0)
                {
                    nextSteps.First(v => v is EdgeTriggerStep).Enabled = true;
                    nextSteps.First(v => v is PatternTriggerStep).Enabled = false;
                }
                else
                {
                    nextSteps.First(v => v is EdgeTriggerStep).Enabled = false;
                    nextSteps.First(v => v is PatternTriggerStep).Enabled = true;
                }
            }

            Args.IsValid = true;
        }

        public enum TriggerType
        {
            Edge = 0,
            Pattern = 1
        }
    }
}
