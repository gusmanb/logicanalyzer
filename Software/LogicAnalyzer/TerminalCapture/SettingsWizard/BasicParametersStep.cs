using SharedDriver;
using Terminal.Gui;

namespace TerminalCapture.SettingsWizard
{
    public class BasicParametersStep : WizardStep, IStepValidate
    {
        TextField _sampleRate;
        TextField _preSamples;
        TextField _postSamples;

        List<CheckBox> _channelCheckBoxes = new List<CheckBox>();

        int _sampleRateValue;
        public int SampleRate
        {
            get { return _sampleRateValue; }
            set { _sampleRateValue = value; _sampleRate.Text = value.ToString(); }
        }

        int _preSamplesValue;
        public int PreSamples
        {
            get { return _preSamplesValue; }
            set { _preSamplesValue = value; _preSamples.Text = value.ToString(); }
        }

        int _postSamplesValue;
        public int PostSamples
        {
            get { return _postSamplesValue; }
            set { _postSamplesValue = value; _postSamples.Text = value.ToString(); }
        }

        int[] _selectedChannels = new int[0];

        public bool BlastOnly { get; private set; }

        AnalyzerDeviceInfo? _info;

        public int[] SelectedChannels
        {
            get { return _selectedChannels; }
            set
            {
                _selectedChannels = value;
                foreach (var cb in _channelCheckBoxes)
                {
                    cb.CheckedState = value.Contains(int.Parse(cb.Id.Substring(5))) ? CheckState.Checked : CheckState.UnChecked;
                }
            }
        }

        public BasicParametersStep(AnalyzerDeviceInfo? Info)
        {
            _info = Info;

            Title = "Basic Parameters";
            //Text = "Please enter the basic parameters for the capture";
            HelpText = "The sample rate is the number of samples per second. The pre-samples is the number of samples to capture before the trigger and the post-samples is the number of samples to capture after the trigger. Select also the channels you want to capture";

            Label lblRate = new Label { Text = "Sample rate: ", X = 1, Y = 1 };
            _sampleRate = new TextField { X = Pos.Right(lblRate) + 1, Y = Pos.Y(lblRate), Width = 14, Text = "100000000", ColorScheme = Colors.ColorSchemes["EditableControl"] };

            Label lblPre = new Label { Text = "Pre-samples: ", X = 1, Y = Pos.Bottom(lblRate) + 1 };
            _preSamples = new TextField { X = Pos.X(_sampleRate), Y = Pos.Bottom(_sampleRate) + 1, Width = 14, Text = "512", ColorScheme = Colors.ColorSchemes["EditableControl"] };

            Label lblPost = new Label { Text = "Post-samples: ", X = 1, Y = Pos.Bottom(lblPre) + 1 };
            _postSamples = new TextField { X = Pos.X(_preSamples), Y = Pos.Bottom(_preSamples) + 1, Width = 14, Text = "1024", ColorScheme = Colors.ColorSchemes["EditableControl"] };

            Add(lblRate);
            Add(_sampleRate);
            Add(lblPre);
            Add(_preSamples);
            Add(lblPost);
            Add(_postSamples);

            for (int buc = 0; buc < 6; buc++)
            {
                var cb = new CheckBox { Text = $"Channel {buc * 4 + 1}", Id = $"CHAN_{buc * 4}", X = 1, Y = buc * 2 + 7 };
                Add(cb);
                _channelCheckBoxes.Add(cb);
                cb = new CheckBox { Text = $"Channel {buc * 4 + 2}", Id = $"CHAN_{buc * 4 + 1}", X = 14, Y = buc * 2 + 7 };
                Add(cb);
                _channelCheckBoxes.Add(cb);
                cb = new CheckBox { Text = $"Channel {buc * 4 + 3}", Id = $"CHAN_{buc * 4 + 2}", X = 27, Y = buc * 2 + 7 };
                Add(cb);
                _channelCheckBoxes.Add(cb);
                cb = new CheckBox { Text = $"Channel {buc * 4 + 4}", Id = $"CHAN_{buc * 4 + 3}", X = 40, Y = buc * 2 + 7 };
                Add(cb);
                _channelCheckBoxes.Add(cb);
            }
        }

        public void OnValidate(StepValidateArgs Args)
        {

            BlastOnly = false;

            if (!int.TryParse(_sampleRate.Text.ToString(), out _sampleRateValue))
            {
                MessageBox.ErrorQuery("Error", "Invalid sample rate", "Ok");
                return;
            }

            if(_sampleRateValue < 1)
            {
                MessageBox.ErrorQuery("Error", "Sample rate must be greater than 0", "Ok");
                return;
            }

            if (_info != null)
            {
                if (_sampleRateValue > _info.BlastFrequency)
                {
                    MessageBox.ErrorQuery("Error", "Sample rate is higher than the maximum frequency.", "Ok");
                    return;
                }

                if (_sampleRateValue > _info.MaxFrequency)
                {
                    var result = MessageBox.Query("Blast mode", "Requested speed can only be achieved in blast mode, are you sure you want to use it?", "Ok", "Cancel");

                    if (result != 0)
                    {
                        return;
                    }

                    BlastOnly = true;
                }
            }

            if (!int.TryParse(_preSamples.Text.ToString(), out _preSamplesValue))
            {
                MessageBox.ErrorQuery("Error", "Invalid pre-samples", "Ok");
                return;
            }

            if (!int.TryParse(_postSamples.Text.ToString(), out _postSamplesValue))
            {
                MessageBox.ErrorQuery("Error", "Invalid post-samples", "Ok");
                return;
            }

            _selectedChannels = _channelCheckBoxes.Where(cb => cb.CheckedState == CheckState.Checked).Select(cb => int.Parse(cb.Id.Substring(5))).ToArray();

            if (_selectedChannels.Length == 0)
            {
                MessageBox.ErrorQuery("Error", "Select at least one channel", "Ok");
                return;
            }

            if (_info != null)
            {
                CaptureLimits? limits = null;

                switch (_selectedChannels.Max())
                {
                    case < 8:
                        limits = _info.ModeLimits[0];
                        break;
                    case < 16:
                        limits = _info.ModeLimits[1];
                        break;
                    default:
                        limits = _info.ModeLimits[2];
                        break;
                }

                if (limits != null)
                {
                    if (_preSamplesValue < limits.MinPreSamples || _preSamplesValue > limits.MaxPreSamples)
                    {
                        MessageBox.ErrorQuery("Error", $"Pre-samples must be between {limits.MinPreSamples} and {limits.MaxPreSamples}", "Ok");
                        return;
                    }

                    if (_postSamplesValue < limits.MinPostSamples || _postSamplesValue > limits.MaxPostSamples)
                    {
                        MessageBox.ErrorQuery("Error", $"Post-samples must be between {limits.MinPostSamples} and {limits.MaxPostSamples}", "Ok");
                        return;
                    }

                    if (_preSamplesValue + _postSamplesValue > limits.MaxTotalSamples)
                    {
                        MessageBox.ErrorQuery("Error", $"Total samples must be less than {limits.MaxTotalSamples}", "Ok");
                        return;
                    }
                }
            }

            var nextSteps = Args.Sequence;

            if (BlastOnly && nextSteps != null)
            {
                var step = (TriggerTypeStep)nextSteps.First(v => v is TriggerTypeStep);
                step.Enabled = false;
                step.SelectedTrigger = 0;
                var edge = (EdgeTriggerStep)nextSteps.First(v => v is EdgeTriggerStep);
                edge.Enabled = true;
                edge.BlastOnly = true;
                nextSteps.First(v => v is PatternTriggerStep).Enabled = false;
            }

            Args.IsValid = true;
        }
    }
}