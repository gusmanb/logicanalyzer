using SharedDriver;
using System;
using System.Collections.Generic;
using System.Linq;
using System.Text;
using System.Threading.Tasks;
using Terminal.Gui;

namespace TerminalCapture.SettingsWizard
{
    public class ConfigurationWizard : Wizard
    {
        BasicParametersStep _basicParameters;
        TriggerTypeStep _triggerType;
        EdgeTriggerStep _edgeTrigger;
        PatternTriggerStep _patternTrigger;

        bool _back = false;
        AnalyzerDeviceInfo? _info;

        public bool Success { get; private set; }

        public CaptureSession? Configuration { get; private set; }

        public ConfigurationWizard(AnalyzerDeviceInfo? Info, CaptureSession? Config)
        {
            Width = 80;
            Height = 24;
            Title = "Configuration Wizard";

            _info = Info; ;

            _basicParameters = new BasicParametersStep(_info);
            _triggerType = new TriggerTypeStep();
            _edgeTrigger = new EdgeTriggerStep();
            _patternTrigger = new PatternTriggerStep();

            if (Config != null)
            {
                _basicParameters.SampleRate = Config.Frequency;
                _basicParameters.PreSamples = Config.PreTriggerSamples;
                _basicParameters.PostSamples = Config.PostTriggerSamples;
                _basicParameters.SelectedChannels = Config.CaptureChannels.Select(x => x.ChannelNumber).ToArray();

                if (Config.TriggerType == TriggerType.Edge || Config.TriggerType == TriggerType.Blast)
                {
                    _triggerType.SelectedTrigger = TriggerTypeStep.TriggerType.Edge;
                    _edgeTrigger.Channel = Config.TriggerChannel;
                    _edgeTrigger.NegativeEdge = Config.TriggerInverted;
                    _edgeTrigger.Blast = Config.TriggerType == TriggerType.Blast;
                }
                else
                {
                    _triggerType.SelectedTrigger = TriggerTypeStep.TriggerType.Pattern;
                    _patternTrigger.Channel = Config.TriggerChannel;
                    _patternTrigger.Pattern = PatternToString(Config.TriggerPattern, Config.TriggerBitCount);
                }
            }

            AddStep(_basicParameters);
            AddStep(_triggerType);
            AddStep(_edgeTrigger);
            AddStep(_patternTrigger);

            MovingNext += ConfigurationWizard_MovingNext;
            MovingBack += ConfigurationWizard_MovingBack;
            Finished += ConfigurationWizard_Finished;
        }

        private void ConfigurationWizard_MovingBack(object? sender, WizardButtonEventArgs e)
        {
            _back = true;
        }

        private void ConfigurationWizard_Finished(object? sender, WizardButtonEventArgs e)
        {
            if (CurrentStep is IStepValidate oldStepValidate)
            {
                var args = new StepValidateArgs() { Sequence = new WizardStep[] { _basicParameters, _triggerType, _edgeTrigger, _patternTrigger } };
                oldStepValidate.OnValidate(args);
                e.Cancel = !args.IsValid;

                if (args.IsValid)
                {
                    Success = true;
                    Configuration = new CaptureSession()
                    {
                        Frequency = _basicParameters.SampleRate,
                        PreTriggerSamples = _basicParameters.PreSamples,
                        PostTriggerSamples = _basicParameters.PostSamples,
                        CaptureChannels = _basicParameters.SelectedChannels.Select(x => new AnalyzerChannel() { ChannelNumber = x }).ToArray()
                    };

                    if (_triggerType.SelectedTrigger == TriggerTypeStep.TriggerType.Edge)
                    {
                        if (_edgeTrigger.Blast)
                            Configuration.TriggerType = TriggerType.Blast;
                        else
                            Configuration.TriggerType = TriggerType.Edge;

                        Configuration.TriggerInverted = _edgeTrigger.NegativeEdge;
                        Configuration.TriggerChannel = _edgeTrigger.Channel;
                    }
                    else
                    {
                        if(_patternTrigger.Fast)
                            Configuration.TriggerType = TriggerType.Fast;
                        else
                            Configuration.TriggerType = TriggerType.Complex;

                        Configuration.TriggerBitCount = _patternTrigger.Pattern.Length;
                        Configuration.TriggerPattern = StringToPattern(_patternTrigger.Pattern);
                        Configuration.TriggerChannel = _patternTrigger.Channel;
                    }
                }
            }
        }

        private void ConfigurationWizard_MovingNext(object? sender, WizardButtonEventArgs e)
        {
            if (_back)
            {
                _back = false;
                e.Cancel = true;
                return;

            }

            if (CurrentStep is IStepValidate oldStepValidate)
            {
                var args = new StepValidateArgs() { Sequence =new WizardStep[] { _basicParameters, _triggerType, _edgeTrigger, _patternTrigger } };
                oldStepValidate.OnValidate(args);
                e.Cancel = !args.IsValid;
            }
        }

        private ushort StringToPattern(string pattern)
        {
            ushort triggerPattern = 0;

            for (int buc = 0; buc < pattern.Length; buc++)
            {
                if (pattern[buc] == '1')
                    triggerPattern |= (UInt16)(1 << buc);
            }

            return triggerPattern;
        }

        private string PatternToString(ushort triggerPattern, int triggerBitCount)
        {
            string pattern = "";

            for (int buc = 0; buc < triggerBitCount; buc++)
                pattern += (triggerPattern & (1 << buc)) == 0 ? "0" : "1";

            return pattern;
        }

    }
}
