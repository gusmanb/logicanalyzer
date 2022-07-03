using Newtonsoft.Json;
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
    public partial class CaptureDialog : Form
    {
        CheckBox[] captureChannels;
        RadioButton[] triggerChannels;

        public CaptureSettings SelectedSettings { get; private set; }

        public CaptureDialog()
        {
            InitializeComponent();
            InitializeControlArrays();
            LoadSettings();
        }

        private void InitializeControlArrays()
        {
            List<CheckBox> channels = new List<CheckBox>();
            List<RadioButton> triggers = new List<RadioButton>();

            for (int buc = 1; buc < 25; buc++)
            {
                channels.Add((CheckBox)Controls.Find($"ckCapture{buc}", true).First());
                triggers.Add((RadioButton)Controls.Find($"rbTrigger{buc}", true).First());
            }

            captureChannels = channels.ToArray();
            triggerChannels = triggers.ToArray();
        }

        private void LoadSettings()
        {
            if (File.Exists("captureSettings.json"))
            {
                string data = File.ReadAllText("captureSettings.json");
                var settings = JsonConvert.DeserializeObject<CaptureSettings>(data);

                if (settings == null)
                    return;

                nudFrequency.Value = settings.Frequency;
                nudPreSamples.Value = settings.PreTriggerSamples;
                nudPostSamples.Value = settings.PostTriggerSamples;

                foreach(var channel in settings.CaptureChannels)
                    captureChannels[channel].Checked = true;

                switch (settings.TriggerType)
                {
                    case 0:
                        rbTriggerTypePattern.Checked = false;
                        rbTriggerTypeEdge.Checked = true;

                        triggerChannels[settings.TriggerChannel].Checked = true;
                        ckNegativeTrigger.Checked = settings.TriggerInverted;

                        rbTriggerTypePattern.Checked = false;
                        rbTriggerTypeEdge.Checked = true;

                        ckFastTrigger.Checked = false;

                        break;

                    case 1:
                        {
                            rbTriggerTypePattern.Checked = true;
                            rbTriggerTypeEdge.Checked = false;

                            nudTriggerBase.Value = settings.TriggerChannel + 1;
                            string pattern = "";

                            for (int buc = 0; buc < settings.TriggerBitCount; buc++)
                                pattern += (settings.TriggerPattern & (1 << buc)) == 0 ? "0" : "1";

                            txtPattern.Text = pattern;

                            ckFastTrigger.Checked = false;
                        }
                        break;

                    case 2:
                        {
                            rbTriggerTypePattern.Checked = true;
                            rbTriggerTypeEdge.Checked = false;

                            nudTriggerBase.Value = settings.TriggerChannel + 1;
                            string pattern = "";

                            for (int buc = 0; buc < settings.TriggerBitCount; buc++)
                                pattern += (settings.TriggerPattern & (1 << buc)) == 0 ? "0" : "1";

                            txtPattern.Text = pattern;

                            ckFastTrigger.Checked = true;
                        }
                        break;
                }
            }
        }

        private void btnAccept_Click(object sender, EventArgs e)
        {
            if (nudPreSamples.Value + nudPostSamples.Value > 32767)
            {
                MessageBox.Show("Total samples cannot exceed 32767.");
                return;
            }

            List<int> channelsToCapture = new List<int>();

            for (int buc = 0; buc < captureChannels.Length; buc++)
            {
                if (captureChannels[buc].Checked)
                    channelsToCapture.Add(buc);
            }

            if (channelsToCapture.Count == 0)
            {
                MessageBox.Show("Select at least one channel to be captured.");
                return;
            }

            int trigger = -1;
            int triggerBits = 0;

            UInt16 triggerPattern = 0;

            if (rbTriggerTypeEdge.Checked)
            {
                for (int buc = 0; buc < triggerChannels.Length; buc++)
                {
                    if (triggerChannels[buc].Checked)
                    {
                        if (trigger == -1)
                            trigger = buc;
                        else
                        {
                            MessageBox.Show("Only one trigger channel supported. How the heck did you managed to select two? ¬¬");
                            return;
                        }
                    }
                }
            }
            else
            {
                trigger = (int)nudTriggerBase.Value - 1;

                char[] patternChars = txtPattern.Text.ToArray();

                if (patternChars.Length == 0)
                {
                    MessageBox.Show("Trigger pattern must be at least one bit long.");
                    return;
                }

                if (patternChars.Any(c => c != '0' && c != '1'))
                {
                    MessageBox.Show("Trigger patterns must be composed only by 0's and 1's.");
                    return;
                }

                if ((trigger - 1) + patternChars.Length > 16)
                {
                    MessageBox.Show("Only first 16 channels can be used in a pattern trigger.");
                    return;
                }

                if (ckFastTrigger.Checked && patternChars.Length > 5)
                {
                    MessageBox.Show("Fast pattern matching is restricted to 5 channels.");
                    return;
                }

                for (int buc = 0; buc < patternChars.Length; buc++)
                {
                    if (patternChars[buc] == '1')
                        triggerPattern |= (UInt16)(1 << buc);
                }

                triggerBits = patternChars.Length;
            }

            if (trigger == -1)
            {
                MessageBox.Show("Yo must select a trigger channel. How the heck did you managed to deselect all? ¬¬");
                return;
            }

            CaptureSettings settings = new CaptureSettings();
            
            settings.Frequency = (int)nudFrequency.Value;
            settings.PreTriggerSamples = (int)nudPreSamples.Value;
            settings.PostTriggerSamples = (int)nudPostSamples.Value;

            settings.TriggerType = rbTriggerTypePattern.Checked ? (ckFastTrigger.Checked ? 2 : 1) : 0;
            settings.TriggerPattern = triggerPattern;
            settings.TriggerBitCount = triggerBits;
            settings.TriggerChannel = trigger;
            settings.TriggerInverted = ckNegativeTrigger.Checked;

            settings.CaptureChannels = channelsToCapture.ToArray();
            
            File.WriteAllText("captureSettings.json", JsonConvert.SerializeObject(settings));
            SelectedSettings = settings;
            DialogResult = DialogResult.OK;
            this.Close();
        }

        private void btnCancel_Click(object sender, EventArgs e)
        {
            DialogResult = DialogResult.Cancel;
            this.Close();
        }

        private void rbTriggerTypeEdge_CheckedChanged(object sender, EventArgs e)
        {
            if (rbTriggerTypeEdge.Checked)
            {
                gbEdgeTrigger.Enabled = true;
                gbPatternTrigger.Enabled = false;
            }
            else
            {
                gbEdgeTrigger.Enabled = false;
                gbPatternTrigger.Enabled = true;
            }
        }

        private void ckFastTrigger_CheckedChanged(object sender, EventArgs e)
        {
            if (ckFastTrigger.Checked)
                txtPattern.MaxLength = 5;
            else
                txtPattern.MaxLength = 16;
        }
    }
}
