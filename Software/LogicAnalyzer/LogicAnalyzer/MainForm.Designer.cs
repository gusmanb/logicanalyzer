namespace LogicAnalyzer
{
    partial class MainForm
    {
        /// <summary>
        ///  Required designer variable.
        /// </summary>
        private System.ComponentModel.IContainer components = null;

        /// <summary>
        ///  Clean up any resources being used.
        /// </summary>
        /// <param name="disposing">true if managed resources should be disposed; otherwise, false.</param>
        protected override void Dispose(bool disposing)
        {
            if (disposing && (components != null))
            {
                components.Dispose();
            }
            base.Dispose(disposing);
        }

        #region Windows Form Designer generated code

        /// <summary>
        ///  Required method for Designer support - do not modify
        ///  the contents of this method with the code editor.
        /// </summary>
        private void InitializeComponent()
        {
            this.btnOpenClose = new System.Windows.Forms.Button();
            this.btnRefresh = new System.Windows.Forms.Button();
            this.sampleViewer = new LogicAnalyzer.SampleViewer();
            this.ddSerialPorts = new System.Windows.Forms.ComboBox();
            this.label1 = new System.Windows.Forms.Label();
            this.lblConnectedDevice = new System.Windows.Forms.Label();
            this.btnCapture = new System.Windows.Forms.Button();
            this.btnRepeat = new System.Windows.Forms.Button();
            this.scrSamplePos = new System.Windows.Forms.HScrollBar();
            this.groupBox1 = new LogicAnalyzer.BorderGroupBox();
            this.btnJmpTrigger = new System.Windows.Forms.Button();
            this.label4 = new System.Windows.Forms.Label();
            this.label3 = new System.Windows.Forms.Label();
            this.tkInScreen = new System.Windows.Forms.TrackBar();
            this.label2 = new System.Windows.Forms.Label();
            this.channelViewer = new LogicAnalyzer.ChannelViewer();
            this.menuStrip1 = new System.Windows.Forms.MenuStrip();
            this.fileToolStripMenuItem = new System.Windows.Forms.ToolStripMenuItem();
            this.openCaptureToolStripMenuItem = new System.Windows.Forms.ToolStripMenuItem();
            this.saveCaptureToolStripMenuItem = new System.Windows.Forms.ToolStripMenuItem();
            this.protocolAnalyzersToolStripMenuItem = new System.Windows.Forms.ToolStripMenuItem();
            this.availableAnalyzersToolStripMenuItem = new System.Windows.Forms.ToolStripMenuItem();
            this.noneToolStripMenuItem = new System.Windows.Forms.ToolStripMenuItem();
            this.groupBox2 = new LogicAnalyzer.BorderGroupBox();
            this.lblEdge = new System.Windows.Forms.Label();
            this.label18 = new System.Windows.Forms.Label();
            this.lblTrigger = new System.Windows.Forms.Label();
            this.label16 = new System.Windows.Forms.Label();
            this.lblChannels = new System.Windows.Forms.Label();
            this.label14 = new System.Windows.Forms.Label();
            this.lblPostSamples = new System.Windows.Forms.Label();
            this.label12 = new System.Windows.Forms.Label();
            this.lblPreSamples = new System.Windows.Forms.Label();
            this.label10 = new System.Windows.Forms.Label();
            this.lblSamples = new System.Windows.Forms.Label();
            this.label8 = new System.Windows.Forms.Label();
            this.lblFreq = new System.Windows.Forms.Label();
            this.label5 = new System.Windows.Forms.Label();
            this.sampleMarker = new LogicAnalyzer.SampleMarker();
            this.label6 = new System.Windows.Forms.Label();
            this.groupBox1.SuspendLayout();
            ((System.ComponentModel.ISupportInitialize)(this.tkInScreen)).BeginInit();
            this.menuStrip1.SuspendLayout();
            this.groupBox2.SuspendLayout();
            this.SuspendLayout();
            // 
            // btnOpenClose
            // 
            this.btnOpenClose.BackColor = System.Drawing.Color.DimGray;
            this.btnOpenClose.FlatAppearance.BorderSize = 0;
            this.btnOpenClose.FlatStyle = System.Windows.Forms.FlatStyle.Flat;
            this.btnOpenClose.ForeColor = System.Drawing.Color.LightGray;
            this.btnOpenClose.Location = new System.Drawing.Point(189, 27);
            this.btnOpenClose.Name = "btnOpenClose";
            this.btnOpenClose.Size = new System.Drawing.Size(126, 23);
            this.btnOpenClose.TabIndex = 0;
            this.btnOpenClose.Text = "Open device";
            this.btnOpenClose.UseVisualStyleBackColor = false;
            this.btnOpenClose.Click += new System.EventHandler(this.btnOpenClose_Click);
            // 
            // btnRefresh
            // 
            this.btnRefresh.BackColor = System.Drawing.Color.DimGray;
            this.btnRefresh.FlatAppearance.BorderSize = 0;
            this.btnRefresh.FlatStyle = System.Windows.Forms.FlatStyle.Flat;
            this.btnRefresh.ForeColor = System.Drawing.Color.LightGray;
            this.btnRefresh.Location = new System.Drawing.Point(12, 27);
            this.btnRefresh.Name = "btnRefresh";
            this.btnRefresh.Size = new System.Drawing.Size(75, 23);
            this.btnRefresh.TabIndex = 1;
            this.btnRefresh.Text = "Refresh";
            this.btnRefresh.UseVisualStyleBackColor = false;
            this.btnRefresh.Click += new System.EventHandler(this.button2_Click);
            // 
            // sampleViewer
            // 
            this.sampleViewer.Anchor = ((System.Windows.Forms.AnchorStyles)((((System.Windows.Forms.AnchorStyles.Top | System.Windows.Forms.AnchorStyles.Bottom) 
            | System.Windows.Forms.AnchorStyles.Left) 
            | System.Windows.Forms.AnchorStyles.Right)));
            this.sampleViewer.ChannelCount = 0;
            this.sampleViewer.FirstSample = 0;
            this.sampleViewer.Location = new System.Drawing.Point(150, 83);
            this.sampleViewer.MinimumSize = new System.Drawing.Size(16, 16);
            this.sampleViewer.Name = "sampleViewer";
            this.sampleViewer.PreSamples = 0;
            this.sampleViewer.Samples = null;
            this.sampleViewer.SamplesInScreen = 0;
            this.sampleViewer.Size = new System.Drawing.Size(1000, 649);
            this.sampleViewer.TabIndex = 2;
            // 
            // ddSerialPorts
            // 
            this.ddSerialPorts.BackColor = System.Drawing.Color.LightGray;
            this.ddSerialPorts.DropDownStyle = System.Windows.Forms.ComboBoxStyle.DropDownList;
            this.ddSerialPorts.FormattingEnabled = true;
            this.ddSerialPorts.Location = new System.Drawing.Point(93, 27);
            this.ddSerialPorts.Name = "ddSerialPorts";
            this.ddSerialPorts.Size = new System.Drawing.Size(90, 23);
            this.ddSerialPorts.TabIndex = 3;
            // 
            // label1
            // 
            this.label1.AutoSize = true;
            this.label1.ForeColor = System.Drawing.Color.LightGray;
            this.label1.Location = new System.Drawing.Point(321, 31);
            this.label1.Name = "label1";
            this.label1.Size = new System.Drawing.Size(105, 15);
            this.label1.TabIndex = 4;
            this.label1.Text = "Connected device:";
            // 
            // lblConnectedDevice
            // 
            this.lblConnectedDevice.AutoSize = true;
            this.lblConnectedDevice.ForeColor = System.Drawing.Color.LightGray;
            this.lblConnectedDevice.Location = new System.Drawing.Point(432, 31);
            this.lblConnectedDevice.Name = "lblConnectedDevice";
            this.lblConnectedDevice.Size = new System.Drawing.Size(58, 15);
            this.lblConnectedDevice.TabIndex = 5;
            this.lblConnectedDevice.Text = "< None >";
            // 
            // btnCapture
            // 
            this.btnCapture.Anchor = ((System.Windows.Forms.AnchorStyles)((System.Windows.Forms.AnchorStyles.Top | System.Windows.Forms.AnchorStyles.Right)));
            this.btnCapture.BackColor = System.Drawing.Color.DimGray;
            this.btnCapture.Enabled = false;
            this.btnCapture.FlatAppearance.BorderSize = 0;
            this.btnCapture.FlatStyle = System.Windows.Forms.FlatStyle.Flat;
            this.btnCapture.ForeColor = System.Drawing.Color.LightGray;
            this.btnCapture.Location = new System.Drawing.Point(1281, 27);
            this.btnCapture.Name = "btnCapture";
            this.btnCapture.Size = new System.Drawing.Size(75, 23);
            this.btnCapture.TabIndex = 6;
            this.btnCapture.Text = "Capture";
            this.btnCapture.UseVisualStyleBackColor = false;
            this.btnCapture.Click += new System.EventHandler(this.btnCapture_Click);
            // 
            // btnRepeat
            // 
            this.btnRepeat.Anchor = ((System.Windows.Forms.AnchorStyles)((System.Windows.Forms.AnchorStyles.Top | System.Windows.Forms.AnchorStyles.Right)));
            this.btnRepeat.BackColor = System.Drawing.Color.DimGray;
            this.btnRepeat.Enabled = false;
            this.btnRepeat.FlatAppearance.BorderSize = 0;
            this.btnRepeat.FlatStyle = System.Windows.Forms.FlatStyle.Flat;
            this.btnRepeat.ForeColor = System.Drawing.Color.LightGray;
            this.btnRepeat.Location = new System.Drawing.Point(1156, 27);
            this.btnRepeat.Name = "btnRepeat";
            this.btnRepeat.Size = new System.Drawing.Size(119, 23);
            this.btnRepeat.TabIndex = 7;
            this.btnRepeat.Text = "Repeat last capture";
            this.btnRepeat.UseVisualStyleBackColor = false;
            this.btnRepeat.Click += new System.EventHandler(this.btnRepeat_Click);
            // 
            // scrSamplePos
            // 
            this.scrSamplePos.Anchor = ((System.Windows.Forms.AnchorStyles)(((System.Windows.Forms.AnchorStyles.Bottom | System.Windows.Forms.AnchorStyles.Left) 
            | System.Windows.Forms.AnchorStyles.Right)));
            this.scrSamplePos.Location = new System.Drawing.Point(12, 735);
            this.scrSamplePos.Maximum = 32;
            this.scrSamplePos.Name = "scrSamplePos";
            this.scrSamplePos.Size = new System.Drawing.Size(1344, 17);
            this.scrSamplePos.TabIndex = 8;
            this.scrSamplePos.Value = 16;
            this.scrSamplePos.ValueChanged += new System.EventHandler(this.scrSamplePos_ValueChanged);
            // 
            // groupBox1
            // 
            this.groupBox1.Anchor = ((System.Windows.Forms.AnchorStyles)((System.Windows.Forms.AnchorStyles.Top | System.Windows.Forms.AnchorStyles.Right)));
            this.groupBox1.BackColor = System.Drawing.Color.FromArgb(((int)(((byte)(64)))), ((int)(((byte)(64)))), ((int)(((byte)(64)))));
            this.groupBox1.BorderColor = System.Drawing.Color.FromArgb(((int)(((byte)(64)))), ((int)(((byte)(64)))), ((int)(((byte)(64)))));
            this.groupBox1.BorderRadius = 0;
            this.groupBox1.BorderWidth = 1;
            this.groupBox1.Controls.Add(this.btnJmpTrigger);
            this.groupBox1.Controls.Add(this.label4);
            this.groupBox1.Controls.Add(this.label3);
            this.groupBox1.Controls.Add(this.tkInScreen);
            this.groupBox1.Controls.Add(this.label2);
            this.groupBox1.ForeColor = System.Drawing.Color.LightGray;
            this.groupBox1.LabelIndent = 10;
            this.groupBox1.Location = new System.Drawing.Point(1156, 56);
            this.groupBox1.Name = "groupBox1";
            this.groupBox1.Size = new System.Drawing.Size(200, 135);
            this.groupBox1.TabIndex = 9;
            this.groupBox1.TabStop = false;
            this.groupBox1.Text = "Adjustments";
            // 
            // btnJmpTrigger
            // 
            this.btnJmpTrigger.Anchor = ((System.Windows.Forms.AnchorStyles)(((System.Windows.Forms.AnchorStyles.Top | System.Windows.Forms.AnchorStyles.Left) 
            | System.Windows.Forms.AnchorStyles.Right)));
            this.btnJmpTrigger.BackColor = System.Drawing.Color.DimGray;
            this.btnJmpTrigger.FlatAppearance.BorderSize = 0;
            this.btnJmpTrigger.FlatStyle = System.Windows.Forms.FlatStyle.Flat;
            this.btnJmpTrigger.Location = new System.Drawing.Point(6, 106);
            this.btnJmpTrigger.Name = "btnJmpTrigger";
            this.btnJmpTrigger.Size = new System.Drawing.Size(188, 23);
            this.btnJmpTrigger.TabIndex = 4;
            this.btnJmpTrigger.Text = "Jump to trigger";
            this.btnJmpTrigger.UseVisualStyleBackColor = false;
            this.btnJmpTrigger.Click += new System.EventHandler(this.btnJmpTrigger_Click);
            // 
            // label4
            // 
            this.label4.AutoSize = true;
            this.label4.Location = new System.Drawing.Point(163, 27);
            this.label4.Name = "label4";
            this.label4.Size = new System.Drawing.Size(25, 15);
            this.label4.TabIndex = 3;
            this.label4.Text = "100";
            // 
            // label3
            // 
            this.label3.AutoSize = true;
            this.label3.Location = new System.Drawing.Point(6, 27);
            this.label3.Name = "label3";
            this.label3.Size = new System.Drawing.Size(19, 15);
            this.label3.TabIndex = 2;
            this.label3.Text = "10";
            // 
            // tkInScreen
            // 
            this.tkInScreen.LargeChange = 10;
            this.tkInScreen.Location = new System.Drawing.Point(6, 45);
            this.tkInScreen.Maximum = 200;
            this.tkInScreen.Minimum = 10;
            this.tkInScreen.Name = "tkInScreen";
            this.tkInScreen.Size = new System.Drawing.Size(182, 45);
            this.tkInScreen.TabIndex = 1;
            this.tkInScreen.TickFrequency = 10;
            this.tkInScreen.Value = 10;
            this.tkInScreen.ValueChanged += new System.EventHandler(this.tkInScreen_ValueChanged);
            // 
            // label2
            // 
            this.label2.AutoSize = true;
            this.label2.Location = new System.Drawing.Point(44, 27);
            this.label2.Name = "label2";
            this.label2.Size = new System.Drawing.Size(101, 15);
            this.label2.TabIndex = 0;
            this.label2.Text = "Samples in screen";
            // 
            // channelViewer
            // 
            this.channelViewer.Anchor = ((System.Windows.Forms.AnchorStyles)(((System.Windows.Forms.AnchorStyles.Top | System.Windows.Forms.AnchorStyles.Bottom) 
            | System.Windows.Forms.AnchorStyles.Left)));
            this.channelViewer.Channels = null;
            this.channelViewer.ChannelsText = new string[0];
            this.channelViewer.Location = new System.Drawing.Point(12, 83);
            this.channelViewer.Name = "channelViewer";
            this.channelViewer.Size = new System.Drawing.Size(137, 649);
            this.channelViewer.TabIndex = 10;
            // 
            // menuStrip1
            // 
            this.menuStrip1.BackColor = System.Drawing.Color.Silver;
            this.menuStrip1.GripStyle = System.Windows.Forms.ToolStripGripStyle.Visible;
            this.menuStrip1.Items.AddRange(new System.Windows.Forms.ToolStripItem[] {
            this.fileToolStripMenuItem,
            this.protocolAnalyzersToolStripMenuItem});
            this.menuStrip1.LayoutStyle = System.Windows.Forms.ToolStripLayoutStyle.Flow;
            this.menuStrip1.Location = new System.Drawing.Point(0, 0);
            this.menuStrip1.Name = "menuStrip1";
            this.menuStrip1.RenderMode = System.Windows.Forms.ToolStripRenderMode.Professional;
            this.menuStrip1.Size = new System.Drawing.Size(1365, 23);
            this.menuStrip1.TabIndex = 11;
            this.menuStrip1.Text = "menuStrip1";
            // 
            // fileToolStripMenuItem
            // 
            this.fileToolStripMenuItem.DropDownItems.AddRange(new System.Windows.Forms.ToolStripItem[] {
            this.openCaptureToolStripMenuItem,
            this.saveCaptureToolStripMenuItem});
            this.fileToolStripMenuItem.Name = "fileToolStripMenuItem";
            this.fileToolStripMenuItem.Size = new System.Drawing.Size(37, 19);
            this.fileToolStripMenuItem.Text = "File";
            // 
            // openCaptureToolStripMenuItem
            // 
            this.openCaptureToolStripMenuItem.Name = "openCaptureToolStripMenuItem";
            this.openCaptureToolStripMenuItem.Size = new System.Drawing.Size(146, 22);
            this.openCaptureToolStripMenuItem.Text = "Open capture";
            this.openCaptureToolStripMenuItem.Click += new System.EventHandler(this.openCaptureToolStripMenuItem_Click);
            // 
            // saveCaptureToolStripMenuItem
            // 
            this.saveCaptureToolStripMenuItem.Enabled = false;
            this.saveCaptureToolStripMenuItem.Name = "saveCaptureToolStripMenuItem";
            this.saveCaptureToolStripMenuItem.Size = new System.Drawing.Size(146, 22);
            this.saveCaptureToolStripMenuItem.Text = "Save capture";
            this.saveCaptureToolStripMenuItem.Click += new System.EventHandler(this.saveCaptureToolStripMenuItem_Click);
            // 
            // protocolAnalyzersToolStripMenuItem
            // 
            this.protocolAnalyzersToolStripMenuItem.DropDownItems.AddRange(new System.Windows.Forms.ToolStripItem[] {
            this.availableAnalyzersToolStripMenuItem});
            this.protocolAnalyzersToolStripMenuItem.Name = "protocolAnalyzersToolStripMenuItem";
            this.protocolAnalyzersToolStripMenuItem.Size = new System.Drawing.Size(115, 19);
            this.protocolAnalyzersToolStripMenuItem.Text = "Protocol analyzers";
            // 
            // availableAnalyzersToolStripMenuItem
            // 
            this.availableAnalyzersToolStripMenuItem.DropDownItems.AddRange(new System.Windows.Forms.ToolStripItem[] {
            this.noneToolStripMenuItem});
            this.availableAnalyzersToolStripMenuItem.Enabled = false;
            this.availableAnalyzersToolStripMenuItem.Name = "availableAnalyzersToolStripMenuItem";
            this.availableAnalyzersToolStripMenuItem.Size = new System.Drawing.Size(173, 22);
            this.availableAnalyzersToolStripMenuItem.Text = "Available analyzers";
            // 
            // noneToolStripMenuItem
            // 
            this.noneToolStripMenuItem.Name = "noneToolStripMenuItem";
            this.noneToolStripMenuItem.Size = new System.Drawing.Size(125, 22);
            this.noneToolStripMenuItem.Text = "< None >";
            // 
            // groupBox2
            // 
            this.groupBox2.Anchor = ((System.Windows.Forms.AnchorStyles)((System.Windows.Forms.AnchorStyles.Bottom | System.Windows.Forms.AnchorStyles.Right)));
            this.groupBox2.BackColor = System.Drawing.Color.FromArgb(((int)(((byte)(64)))), ((int)(((byte)(64)))), ((int)(((byte)(64)))));
            this.groupBox2.BorderColor = System.Drawing.Color.FromArgb(((int)(((byte)(64)))), ((int)(((byte)(64)))), ((int)(((byte)(64)))));
            this.groupBox2.BorderRadius = 0;
            this.groupBox2.BorderWidth = 1;
            this.groupBox2.Controls.Add(this.lblEdge);
            this.groupBox2.Controls.Add(this.label18);
            this.groupBox2.Controls.Add(this.lblTrigger);
            this.groupBox2.Controls.Add(this.label16);
            this.groupBox2.Controls.Add(this.lblChannels);
            this.groupBox2.Controls.Add(this.label14);
            this.groupBox2.Controls.Add(this.lblPostSamples);
            this.groupBox2.Controls.Add(this.label12);
            this.groupBox2.Controls.Add(this.lblPreSamples);
            this.groupBox2.Controls.Add(this.label10);
            this.groupBox2.Controls.Add(this.lblSamples);
            this.groupBox2.Controls.Add(this.label8);
            this.groupBox2.Controls.Add(this.lblFreq);
            this.groupBox2.Controls.Add(this.label5);
            this.groupBox2.ForeColor = System.Drawing.Color.LightGray;
            this.groupBox2.LabelIndent = 10;
            this.groupBox2.Location = new System.Drawing.Point(1156, 603);
            this.groupBox2.Name = "groupBox2";
            this.groupBox2.Size = new System.Drawing.Size(200, 129);
            this.groupBox2.TabIndex = 12;
            this.groupBox2.TabStop = false;
            this.groupBox2.Text = "Information";
            // 
            // lblEdge
            // 
            this.lblEdge.Location = new System.Drawing.Point(93, 109);
            this.lblEdge.Name = "lblEdge";
            this.lblEdge.Size = new System.Drawing.Size(101, 15);
            this.lblEdge.TabIndex = 13;
            this.lblEdge.TextAlign = System.Drawing.ContentAlignment.TopRight;
            // 
            // label18
            // 
            this.label18.AutoSize = true;
            this.label18.Location = new System.Drawing.Point(6, 109);
            this.label18.Name = "label18";
            this.label18.Size = new System.Drawing.Size(36, 15);
            this.label18.TabIndex = 12;
            this.label18.Text = "Edge:";
            // 
            // lblTrigger
            // 
            this.lblTrigger.Location = new System.Drawing.Point(93, 94);
            this.lblTrigger.Name = "lblTrigger";
            this.lblTrigger.Size = new System.Drawing.Size(101, 15);
            this.lblTrigger.TabIndex = 11;
            this.lblTrigger.TextAlign = System.Drawing.ContentAlignment.TopRight;
            // 
            // label16
            // 
            this.label16.AutoSize = true;
            this.label16.Location = new System.Drawing.Point(6, 94);
            this.label16.Name = "label16";
            this.label16.Size = new System.Drawing.Size(46, 15);
            this.label16.TabIndex = 10;
            this.label16.Text = "Trigger:";
            // 
            // lblChannels
            // 
            this.lblChannels.Location = new System.Drawing.Point(93, 79);
            this.lblChannels.Name = "lblChannels";
            this.lblChannels.Size = new System.Drawing.Size(101, 15);
            this.lblChannels.TabIndex = 9;
            this.lblChannels.TextAlign = System.Drawing.ContentAlignment.TopRight;
            // 
            // label14
            // 
            this.label14.AutoSize = true;
            this.label14.Location = new System.Drawing.Point(6, 79);
            this.label14.Name = "label14";
            this.label14.Size = new System.Drawing.Size(59, 15);
            this.label14.TabIndex = 8;
            this.label14.Text = "Channels:";
            // 
            // lblPostSamples
            // 
            this.lblPostSamples.Location = new System.Drawing.Point(93, 64);
            this.lblPostSamples.Name = "lblPostSamples";
            this.lblPostSamples.Size = new System.Drawing.Size(101, 15);
            this.lblPostSamples.TabIndex = 7;
            this.lblPostSamples.TextAlign = System.Drawing.ContentAlignment.TopRight;
            // 
            // label12
            // 
            this.label12.AutoSize = true;
            this.label12.Location = new System.Drawing.Point(6, 64);
            this.label12.Name = "label12";
            this.label12.Size = new System.Drawing.Size(79, 15);
            this.label12.TabIndex = 6;
            this.label12.Text = "Post samples:";
            // 
            // lblPreSamples
            // 
            this.lblPreSamples.Location = new System.Drawing.Point(93, 49);
            this.lblPreSamples.Name = "lblPreSamples";
            this.lblPreSamples.Size = new System.Drawing.Size(101, 15);
            this.lblPreSamples.TabIndex = 5;
            this.lblPreSamples.TextAlign = System.Drawing.ContentAlignment.TopRight;
            // 
            // label10
            // 
            this.label10.AutoSize = true;
            this.label10.Location = new System.Drawing.Point(6, 49);
            this.label10.Name = "label10";
            this.label10.Size = new System.Drawing.Size(73, 15);
            this.label10.TabIndex = 4;
            this.label10.Text = "Pre samples:";
            // 
            // lblSamples
            // 
            this.lblSamples.Location = new System.Drawing.Point(93, 34);
            this.lblSamples.Name = "lblSamples";
            this.lblSamples.Size = new System.Drawing.Size(101, 15);
            this.lblSamples.TabIndex = 3;
            this.lblSamples.TextAlign = System.Drawing.ContentAlignment.TopRight;
            // 
            // label8
            // 
            this.label8.AutoSize = true;
            this.label8.Location = new System.Drawing.Point(6, 34);
            this.label8.Name = "label8";
            this.label8.Size = new System.Drawing.Size(81, 15);
            this.label8.TabIndex = 2;
            this.label8.Text = "Total samples:";
            // 
            // lblFreq
            // 
            this.lblFreq.Location = new System.Drawing.Point(93, 19);
            this.lblFreq.Name = "lblFreq";
            this.lblFreq.Size = new System.Drawing.Size(101, 15);
            this.lblFreq.TabIndex = 1;
            this.lblFreq.TextAlign = System.Drawing.ContentAlignment.TopRight;
            // 
            // label5
            // 
            this.label5.AutoSize = true;
            this.label5.Location = new System.Drawing.Point(6, 19);
            this.label5.Name = "label5";
            this.label5.Size = new System.Drawing.Size(65, 15);
            this.label5.TabIndex = 0;
            this.label5.Text = "Frequency:";
            // 
            // sampleMarker
            // 
            this.sampleMarker.Anchor = ((System.Windows.Forms.AnchorStyles)(((System.Windows.Forms.AnchorStyles.Top | System.Windows.Forms.AnchorStyles.Left) 
            | System.Windows.Forms.AnchorStyles.Right)));
            this.sampleMarker.BackColor = System.Drawing.Color.DimGray;
            this.sampleMarker.FirstSample = 0;
            this.sampleMarker.ForeColor = System.Drawing.Color.LightGray;
            this.sampleMarker.Location = new System.Drawing.Point(150, 56);
            this.sampleMarker.Name = "sampleMarker";
            this.sampleMarker.Size = new System.Drawing.Size(1000, 21);
            this.sampleMarker.TabIndex = 13;
            this.sampleMarker.VisibleSamples = 0;
            this.sampleMarker.RegionCreated += new System.EventHandler<LogicAnalyzer.RegionEventArgs>(this.sampleMarker_RegionCreated);
            this.sampleMarker.RegionDeleted += new System.EventHandler<LogicAnalyzer.RegionEventArgs>(this.sampleMarker_RegionDeleted);
            // 
            // label6
            // 
            this.label6.BackColor = System.Drawing.Color.DimGray;
            this.label6.ForeColor = System.Drawing.Color.LightGray;
            this.label6.Location = new System.Drawing.Point(12, 56);
            this.label6.Name = "label6";
            this.label6.Size = new System.Drawing.Size(137, 21);
            this.label6.TabIndex = 14;
            this.label6.Text = "Channels";
            this.label6.TextAlign = System.Drawing.ContentAlignment.MiddleCenter;
            // 
            // MainForm
            // 
            this.AutoScaleDimensions = new System.Drawing.SizeF(7F, 15F);
            this.AutoScaleMode = System.Windows.Forms.AutoScaleMode.Font;
            this.BackColor = System.Drawing.Color.FromArgb(((int)(((byte)(32)))), ((int)(((byte)(32)))), ((int)(((byte)(32)))));
            this.ClientSize = new System.Drawing.Size(1365, 761);
            this.Controls.Add(this.label6);
            this.Controls.Add(this.sampleMarker);
            this.Controls.Add(this.groupBox2);
            this.Controls.Add(this.channelViewer);
            this.Controls.Add(this.groupBox1);
            this.Controls.Add(this.scrSamplePos);
            this.Controls.Add(this.btnRepeat);
            this.Controls.Add(this.btnCapture);
            this.Controls.Add(this.lblConnectedDevice);
            this.Controls.Add(this.label1);
            this.Controls.Add(this.ddSerialPorts);
            this.Controls.Add(this.sampleViewer);
            this.Controls.Add(this.btnRefresh);
            this.Controls.Add(this.btnOpenClose);
            this.Controls.Add(this.menuStrip1);
            this.DoubleBuffered = true;
            this.ForeColor = System.Drawing.Color.LightGray;
            this.MinimumSize = new System.Drawing.Size(1024, 800);
            this.Name = "MainForm";
            this.StartPosition = System.Windows.Forms.FormStartPosition.CenterScreen;
            this.Text = "LogicAnalyzer V1.0 by El Dr. Gusman";
            this.Load += new System.EventHandler(this.Form1_Load);
            this.groupBox1.ResumeLayout(false);
            this.groupBox1.PerformLayout();
            ((System.ComponentModel.ISupportInitialize)(this.tkInScreen)).EndInit();
            this.menuStrip1.ResumeLayout(false);
            this.menuStrip1.PerformLayout();
            this.groupBox2.ResumeLayout(false);
            this.groupBox2.PerformLayout();
            this.ResumeLayout(false);
            this.PerformLayout();

        }

        #endregion

        private Button btnOpenClose;
        private Button btnRefresh;
        private SampleViewer sampleViewer;
        private ComboBox ddSerialPorts;
        private Label label1;
        private Label lblConnectedDevice;
        private Button btnCapture;
        private Button btnRepeat;
        private HScrollBar scrSamplePos;
        private BorderGroupBox groupBox1;
        private Label label4;
        private Label label3;
        private TrackBar tkInScreen;
        private Label label2;
        private Button btnJmpTrigger;
        private ChannelViewer channelViewer;
        private MenuStrip menuStrip1;
        private ToolStripMenuItem fileToolStripMenuItem;
        private ToolStripMenuItem openCaptureToolStripMenuItem;
        private ToolStripMenuItem saveCaptureToolStripMenuItem;
        private BorderGroupBox groupBox2;
        private Label lblEdge;
        private Label label18;
        private Label lblTrigger;
        private Label label16;
        private Label lblChannels;
        private Label label14;
        private Label lblPostSamples;
        private Label label12;
        private Label lblPreSamples;
        private Label label10;
        private Label lblSamples;
        private Label label8;
        private Label lblFreq;
        private Label label5;
        private SampleMarker sampleMarker;
        private Label label6;
        private ToolStripMenuItem protocolAnalyzersToolStripMenuItem;
        private ToolStripMenuItem availableAnalyzersToolStripMenuItem;
        private ToolStripMenuItem noneToolStripMenuItem;
    }
}