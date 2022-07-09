using LogicAnalyzer.Protocols;
using Newtonsoft.Json;
using System.IO.Ports;

namespace LogicAnalyzer
{
    public partial class MainForm : Form
    {
        LogicAnalyzerDriver driver;
        CaptureSettings settings;

        ProtocolAnalyzerLoader pLoader;

        protected override CreateParams CreateParams
        {
            get
            {
                CreateParams cp = base.CreateParams;
                cp.ExStyle |= 0x02000000;  // Turn on WS_EX_COMPOSITED
                return cp;
            }
        }

        public MainForm()
        {
            var splashForm = new Splash();
            splashForm.Show();

            InitializeComponent();
            menuStrip1.Renderer = new ToolStripProfessionalRenderer(new MenuColors.MyColorTable());
        }

        private void Driver_CaptureCompleted(object? sender, CaptureEventArgs e)
        {
            this.BeginInvoke(new Action(() => 
            {
                sampleViewer.BeginUpdate();
                sampleViewer.Samples = e.Samples;
                sampleViewer.PreSamples = e.PreSamples;
                sampleViewer.ChannelCount = e.ChannelCount;
                sampleViewer.SamplesInScreen = Math.Min(100, e.Samples.Length / 10);
                sampleViewer.FirstSample = Math.Max(e.PreSamples - 10, 0);
                sampleViewer.ClearRegions();
                sampleViewer.ClearAnalyzedChannels();
                sampleViewer.EndUpdate();

                scrSamplePos.Maximum = e.Samples.Length - 1;
                scrSamplePos.Value = sampleViewer.FirstSample;
                tkInScreen.Value = sampleViewer.SamplesInScreen;

                channelViewer.Channels = settings.CaptureChannels;

                sampleMarker.VisibleSamples = sampleViewer.SamplesInScreen;
                sampleMarker.FirstSample = sampleViewer.FirstSample;
                sampleMarker.ClearRegions();

                btnCapture.Enabled = true;
                btnRepeat.Enabled = true;
                btnOpenClose.Enabled = true;
                availableAnalyzersToolStripMenuItem.Enabled = true;
                saveCaptureToolStripMenuItem.Enabled = true;
                LoadInfo();

            }));
        }

        private void Form1_Load(object sender, EventArgs e)
        {
            LoadAnalyzers();
            RefreshPorts();
        }

        void LoadAnalyzers()
        {
            pLoader = new ProtocolAnalyzerLoader(Path.Combine(Application.StartupPath, "analyzers"));

            var protocols = pLoader.ProtocolNames;
            availableAnalyzersToolStripMenuItem.DropDownItems.Clear();

            if (protocols.Length == 0)
                availableAnalyzersToolStripMenuItem.DropDownItems.Add("< None >");
            else
            {

                foreach (var protocol in pLoader.ProtocolNames)
                {
                    var menu = availableAnalyzersToolStripMenuItem.DropDownItems.Add(protocol, null, ProtocolAnalyzer_Click);
                    menu.Tag = protocol;
                }
            }
        }

        private void ProtocolAnalyzer_Click(object? sender, EventArgs e)
        {
            var item = (sender as ToolStripMenuItem).Tag.ToString();
            var analyzer = pLoader.GetAnalyzer(item);

            using (var dlg = new ProtocolAnalyzerSettingsDialog())
            {
                dlg.Analyzer = analyzer;
                dlg.Channels = channelViewer.Channels;

                if (dlg.ShowDialog() != DialogResult.OK)
                    return;

                var channels = dlg.SelectedChannels;
                var samples = sampleViewer.Samples;

                foreach (var channel in channels)
                    ExtractSamples(channel, samples);

                var analysisResult = analyzer.Analyze(settings.Frequency, settings.PreTriggerSamples - 1, dlg.SelectedSettings, channels);

                if (analysisResult != null)
                {
                    sampleViewer.BeginUpdate();
                    sampleViewer.AddAnalyzedChannels(analysisResult);
                    sampleViewer.EndUpdate();
                }
            }
        }

        private void ExtractSamples(ProtocolAnalyzerSelectedChannel channel, uint[]? samples)
        {
            if (channel == null || samples == null)
                return;

            int idx = channel.ChannelIndex;
            int mask = 1 << idx;
            channel.Samples = samples.Select(s => (s & mask) != 0 ? (byte)1 : (byte)0).ToArray();
        }

        private void btnOpenClose_Click(object sender, EventArgs e)
        {
            if (driver == null)
            {
                if (ddSerialPorts.SelectedIndex == -1)
                {
                    MessageBox.Show("Select a serial port to connect.");
                    return;
                }

                try
                {
                    driver = new LogicAnalyzerDriver(ddSerialPorts.SelectedItem.ToString(), 115200);
                    driver.CaptureCompleted += Driver_CaptureCompleted;
                }
                catch
                {
                    MessageBox.Show("Cannot connect to device.");
                    return;
                }

                lblConnectedDevice.Text = driver.DeviceVersion;
                ddSerialPorts.Enabled = false;
                btnRefresh.Enabled = false;
                btnOpenClose.Text = "Close device";
                btnCapture.Enabled = true;
                btnRepeat.Enabled = true;
            }
            else
            {
                driver.Dispose();
                driver = null;
                lblConnectedDevice.Text = "< None >";
                ddSerialPorts.Enabled = true;
                btnRefresh.Enabled = true;
                btnOpenClose.Text = "Open device";
                RefreshPorts();
                btnCapture.Enabled = false;
                btnRepeat.Enabled = false;
            }
        }

        private void button2_Click(object sender, EventArgs e)
        {
            RefreshPorts();
        }

        void RefreshPorts()
        {
            ddSerialPorts.DataSource = null;
            ddSerialPorts.Refresh();
            ddSerialPorts.DataSource = SerialPort.GetPortNames();
        }

        private void btnRepeat_Click(object sender, EventArgs e)
        {
            if (settings == null)
            {
                MessageBox.Show("No capture to repeat");
                return;
            }

            BeginCapture();
        }

        private void btnCapture_Click(object sender, EventArgs e)
        {
            using (var dialog = new CaptureDialog())
            {
                if (dialog.ShowDialog() != DialogResult.OK)
                    return;

                settings = dialog.SelectedSettings;
                BeginCapture();
            }
        }

        private void BeginCapture()
        {

            if (settings.TriggerType != 0)
            {
                if (!driver.StartPatternCapture(settings.Frequency, settings.PreTriggerSamples, settings.PostTriggerSamples, settings.CaptureChannels, settings.TriggerChannel, settings.TriggerBitCount, settings.TriggerPattern, settings.TriggerType == 2 ? true : false))
                {
                    MessageBox.Show("Device reported error starting capture. Restart the device and try again.");
                    return;
                }
            }
            else
            {
                if (!driver.StartCapture(settings.Frequency, settings.PreTriggerSamples, settings.PostTriggerSamples, settings.CaptureChannels, settings.TriggerChannel, settings.TriggerInverted))
                {
                    MessageBox.Show("Device reported error starting capture. Restart the device and try again.");
                    return;
                }
            }
            btnCapture.Enabled = false;
            btnRepeat.Enabled = false;
            btnOpenClose.Enabled = false;
        }

        private void scrSamplePos_ValueChanged(object sender, EventArgs e)
        {
            if (sampleViewer.Samples != null)
            {
                sampleViewer.BeginUpdate();
                sampleViewer.FirstSample = scrSamplePos.Value;
                sampleViewer.EndUpdate();
                sampleMarker.FirstSample = sampleViewer.FirstSample;
            }
        }

        private void tkInScreen_ValueChanged(object sender, EventArgs e)
        {
            if (sampleViewer.Samples != null)
            {
                sampleViewer.BeginUpdate();
                sampleViewer.SamplesInScreen = tkInScreen.Value;
                sampleViewer.EndUpdate();
                sampleMarker.VisibleSamples = sampleViewer.SamplesInScreen;
            }
        }

        private void btnJmpTrigger_Click(object sender, EventArgs e)
        {
            if (sampleViewer.Samples != null && settings != null)
            {
                sampleViewer.BeginUpdate();
                sampleViewer.FirstSample = Math.Max(settings.PreTriggerSamples - (tkInScreen.Value / 10), 0);
                sampleViewer.EndUpdate();
                scrSamplePos.Value = sampleViewer.FirstSample;
                sampleMarker.FirstSample = sampleViewer.FirstSample;
            }
        }

        private void saveCaptureToolStripMenuItem_Click(object sender, EventArgs e)
        {
            using (var sf = new SaveFileDialog())
            {
                sf.Filter = "Logic analyzer captures|*.lac";

                if (sf.ShowDialog() != DialogResult.OK)
                    return;

                ExportedCapture ex = new ExportedCapture { Settings = settings, Samples = sampleViewer.Samples, ChannelTexts = channelViewer.ChannelsText, SelectedRegions = sampleViewer.SelectedRegions };

                File.WriteAllText(sf.FileName,JsonConvert.SerializeObject(ex, new JsonConverter[] { new SelectedSampleRegion.SelectedSampleRegionConverter() }));
            }
        }

        private void openCaptureToolStripMenuItem_Click(object sender, EventArgs e)
        {
            using (var sf = new OpenFileDialog())
            {
                sf.Filter = "Logic analyzer captures|*.lac";

                if (sf.ShowDialog() != DialogResult.OK)
                    return;

                ExportedCapture ex = JsonConvert.DeserializeObject<ExportedCapture>(File.ReadAllText(sf.FileName), new JsonConverter[] { new SelectedSampleRegion.SelectedSampleRegionConverter() });

                if (ex == null)
                    return;

                settings = ex.Settings;

                sampleViewer.BeginUpdate();
                sampleViewer.Samples = ex.Samples;
                sampleViewer.PreSamples = ex.Settings.PreTriggerSamples;
                sampleViewer.ChannelCount = ex.Settings.CaptureChannels.Length;
                sampleViewer.SamplesInScreen = Math.Min(100, ex.Samples.Length / 10);
                sampleViewer.FirstSample = Math.Max(ex.Settings.PreTriggerSamples - 10, 0);
                sampleViewer.ClearRegions();
                sampleViewer.ClearAnalyzedChannels();

                if (ex.SelectedRegions != null)
                    sampleViewer.AddRegions(ex.SelectedRegions);

                sampleViewer.EndUpdate();

                sampleMarker.VisibleSamples = sampleViewer.SamplesInScreen;
                sampleMarker.FirstSample = sampleViewer.FirstSample;
                sampleMarker.ClearRegions();
                
                if (ex.SelectedRegions != null)
                    sampleMarker.AddRegions(ex.SelectedRegions);

                scrSamplePos.Maximum = ex.Samples.Length - 1;
                scrSamplePos.Value = sampleViewer.FirstSample;
                tkInScreen.Value = sampleViewer.SamplesInScreen;

                channelViewer.Channels = ex.Settings.CaptureChannels;
                channelViewer.ChannelsText = ex.ChannelTexts;

                saveCaptureToolStripMenuItem.Enabled = true;
                availableAnalyzersToolStripMenuItem.Enabled = true;

                LoadInfo();
            }
        }

        void LoadInfo()
        {
            lblFreq.Text = String.Format("{0:n}", settings.Frequency) + " Hz";
            lblPreSamples.Text = String.Format("{0:n}", settings.PreTriggerSamples);
            lblPostSamples.Text = String.Format("{0:n}", settings.PostTriggerSamples);
            lblSamples.Text = String.Format("{0:n}", settings.PostTriggerSamples + settings.PreTriggerSamples);
            lblChannels.Text = settings.CaptureChannels.Length.ToString();
            lblTrigger.Text = $"Channel {settings.TriggerChannel + 1}";
            lblEdge.Text = settings.TriggerInverted ? "Negative" : "Positive";
        }

        private void sampleMarker_RegionCreated(object sender, RegionEventArgs e)
        {
            sampleViewer.BeginUpdate();
            sampleViewer.AddRegion(e.Region);
            sampleViewer.EndUpdate();
        }

        private void sampleMarker_RegionDeleted(object sender, RegionEventArgs e)
        {
            sampleViewer.BeginUpdate();
            sampleViewer.RemoveRegion(e.Region);
            sampleViewer.EndUpdate();
        }
    }
}