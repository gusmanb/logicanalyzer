namespace LogicAnalyzer
{
    partial class SelectedRegionDialog
    {
        /// <summary>
        /// Required designer variable.
        /// </summary>
        private System.ComponentModel.IContainer components = null;

        /// <summary>
        /// Clean up any resources being used.
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
        /// Required method for Designer support - do not modify
        /// the contents of this method with the code editor.
        /// </summary>
        private void InitializeComponent()
        {
            this.cwRegionColor = new Cyotek.Windows.Forms.ColorWheel();
            this.label1 = new System.Windows.Forms.Label();
            this.txtName = new System.Windows.Forms.TextBox();
            this.label2 = new System.Windows.Forms.Label();
            this.btnCancel = new System.Windows.Forms.Button();
            this.btnAccept = new System.Windows.Forms.Button();
            this.tkAlpha = new System.Windows.Forms.TrackBar();
            this.txtAlpha = new System.Windows.Forms.TextBox();
            this.label3 = new System.Windows.Forms.Label();
            ((System.ComponentModel.ISupportInitialize)(this.tkAlpha)).BeginInit();
            this.SuspendLayout();
            // 
            // cwRegionColor
            // 
            this.cwRegionColor.Alpha = 1D;
            this.cwRegionColor.LineColor = System.Drawing.Color.DarkGray;
            this.cwRegionColor.Location = new System.Drawing.Point(17, 110);
            this.cwRegionColor.Margin = new System.Windows.Forms.Padding(4, 5, 4, 5);
            this.cwRegionColor.Name = "cwRegionColor";
            this.cwRegionColor.ShowAngleArrow = true;
            this.cwRegionColor.ShowCenterLines = true;
            this.cwRegionColor.ShowSaturationRing = true;
            this.cwRegionColor.Size = new System.Drawing.Size(359, 435);
            this.cwRegionColor.TabIndex = 0;
            // 
            // label1
            // 
            this.label1.AutoSize = true;
            this.label1.Location = new System.Drawing.Point(17, 25);
            this.label1.Margin = new System.Windows.Forms.Padding(4, 0, 4, 0);
            this.label1.Name = "label1";
            this.label1.Size = new System.Drawing.Size(120, 25);
            this.label1.TabIndex = 1;
            this.label1.Text = "Region name:";
            // 
            // txtName
            // 
            this.txtName.BackColor = System.Drawing.Color.DimGray;
            this.txtName.ForeColor = System.Drawing.Color.LightGray;
            this.txtName.Location = new System.Drawing.Point(140, 20);
            this.txtName.Margin = new System.Windows.Forms.Padding(4, 5, 4, 5);
            this.txtName.Name = "txtName";
            this.txtName.Size = new System.Drawing.Size(300, 31);
            this.txtName.TabIndex = 2;
            // 
            // label2
            // 
            this.label2.AutoSize = true;
            this.label2.Location = new System.Drawing.Point(17, 80);
            this.label2.Margin = new System.Windows.Forms.Padding(4, 0, 4, 0);
            this.label2.Name = "label2";
            this.label2.Size = new System.Drawing.Size(112, 25);
            this.label2.TabIndex = 3;
            this.label2.Text = "Region color";
            // 
            // btnCancel
            // 
            this.btnCancel.BackColor = System.Drawing.Color.DimGray;
            this.btnCancel.FlatAppearance.BorderSize = 0;
            this.btnCancel.FlatStyle = System.Windows.Forms.FlatStyle.Flat;
            this.btnCancel.Location = new System.Drawing.Point(341, 555);
            this.btnCancel.Margin = new System.Windows.Forms.Padding(4, 5, 4, 5);
            this.btnCancel.Name = "btnCancel";
            this.btnCancel.Size = new System.Drawing.Size(107, 38);
            this.btnCancel.TabIndex = 4;
            this.btnCancel.Text = "Cancel";
            this.btnCancel.UseVisualStyleBackColor = false;
            this.btnCancel.Click += new System.EventHandler(this.btnCancel_Click);
            // 
            // btnAccept
            // 
            this.btnAccept.BackColor = System.Drawing.Color.DimGray;
            this.btnAccept.FlatAppearance.BorderSize = 0;
            this.btnAccept.FlatStyle = System.Windows.Forms.FlatStyle.Flat;
            this.btnAccept.Location = new System.Drawing.Point(226, 555);
            this.btnAccept.Margin = new System.Windows.Forms.Padding(4, 5, 4, 5);
            this.btnAccept.Name = "btnAccept";
            this.btnAccept.Size = new System.Drawing.Size(107, 38);
            this.btnAccept.TabIndex = 5;
            this.btnAccept.Text = "Accept";
            this.btnAccept.UseVisualStyleBackColor = false;
            this.btnAccept.Click += new System.EventHandler(this.btnAccept_Click);
            // 
            // tkAlpha
            // 
            this.tkAlpha.Location = new System.Drawing.Point(384, 115);
            this.tkAlpha.Margin = new System.Windows.Forms.Padding(4, 5, 4, 5);
            this.tkAlpha.Maximum = 255;
            this.tkAlpha.Name = "tkAlpha";
            this.tkAlpha.Orientation = System.Windows.Forms.Orientation.Vertical;
            this.tkAlpha.Size = new System.Drawing.Size(69, 382);
            this.tkAlpha.TabIndex = 6;
            this.tkAlpha.TickFrequency = 10;
            this.tkAlpha.TickStyle = System.Windows.Forms.TickStyle.Both;
            this.tkAlpha.Value = 128;
            this.tkAlpha.ValueChanged += new System.EventHandler(this.tkAlpha_ValueChanged);
            // 
            // txtAlpha
            // 
            this.txtAlpha.BackColor = System.Drawing.Color.DimGray;
            this.txtAlpha.ForeColor = System.Drawing.Color.LightGray;
            this.txtAlpha.Location = new System.Drawing.Point(384, 507);
            this.txtAlpha.Margin = new System.Windows.Forms.Padding(4, 5, 4, 5);
            this.txtAlpha.Name = "txtAlpha";
            this.txtAlpha.ReadOnly = true;
            this.txtAlpha.Size = new System.Drawing.Size(63, 31);
            this.txtAlpha.TabIndex = 7;
            this.txtAlpha.Text = "128";
            this.txtAlpha.TextAlign = System.Windows.Forms.HorizontalAlignment.Center;
            // 
            // label3
            // 
            this.label3.AutoSize = true;
            this.label3.Location = new System.Drawing.Point(389, 85);
            this.label3.Margin = new System.Windows.Forms.Padding(4, 0, 4, 0);
            this.label3.Name = "label3";
            this.label3.Size = new System.Drawing.Size(58, 25);
            this.label3.TabIndex = 8;
            this.label3.Text = "Alpha";
            // 
            // SelectedRegionDialog
            // 
            this.AcceptButton = this.btnAccept;
            this.AutoScaleDimensions = new System.Drawing.SizeF(10F, 25F);
            this.AutoScaleMode = System.Windows.Forms.AutoScaleMode.Font;
            this.BackColor = System.Drawing.Color.FromArgb(((int)(((byte)(32)))), ((int)(((byte)(32)))), ((int)(((byte)(32)))));
            this.CancelButton = this.btnCancel;
            this.ClientSize = new System.Drawing.Size(462, 610);
            this.ControlBox = false;
            this.Controls.Add(this.label3);
            this.Controls.Add(this.txtAlpha);
            this.Controls.Add(this.tkAlpha);
            this.Controls.Add(this.btnAccept);
            this.Controls.Add(this.btnCancel);
            this.Controls.Add(this.label2);
            this.Controls.Add(this.txtName);
            this.Controls.Add(this.label1);
            this.Controls.Add(this.cwRegionColor);
            this.ForeColor = System.Drawing.Color.LightGray;
            this.FormBorderStyle = System.Windows.Forms.FormBorderStyle.SizableToolWindow;
            this.Margin = new System.Windows.Forms.Padding(4, 5, 4, 5);
            this.MaximizeBox = false;
            this.MaximumSize = new System.Drawing.Size(484, 666);
            this.MinimizeBox = false;
            this.MinimumSize = new System.Drawing.Size(484, 666);
            this.Name = "SelectedRegionDialog";
            this.StartPosition = System.Windows.Forms.FormStartPosition.CenterParent;
            this.Text = "Create selected region";
            ((System.ComponentModel.ISupportInitialize)(this.tkAlpha)).EndInit();
            this.ResumeLayout(false);
            this.PerformLayout();

        }

        #endregion

        private Cyotek.Windows.Forms.ColorWheel cwRegionColor;
        private Label label1;
        private TextBox txtName;
        private Label label2;
        private Button btnCancel;
        private Button btnAccept;
        private TrackBar tkAlpha;
        private TextBox txtAlpha;
        private Label label3;
    }
}