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
            this.cwRegionColor.Location = new System.Drawing.Point(12, 66);
            this.cwRegionColor.Name = "cwRegionColor";
            this.cwRegionColor.ShowAngleArrow = true;
            this.cwRegionColor.ShowCenterLines = true;
            this.cwRegionColor.ShowSaturationRing = true;
            this.cwRegionColor.Size = new System.Drawing.Size(251, 261);
            this.cwRegionColor.TabIndex = 0;
            // 
            // label1
            // 
            this.label1.AutoSize = true;
            this.label1.Location = new System.Drawing.Point(12, 15);
            this.label1.Name = "label1";
            this.label1.Size = new System.Drawing.Size(80, 15);
            this.label1.TabIndex = 1;
            this.label1.Text = "Region name:";
            // 
            // txtName
            // 
            this.txtName.BackColor = System.Drawing.Color.DimGray;
            this.txtName.ForeColor = System.Drawing.Color.LightGray;
            this.txtName.Location = new System.Drawing.Point(98, 12);
            this.txtName.Name = "txtName";
            this.txtName.Size = new System.Drawing.Size(211, 23);
            this.txtName.TabIndex = 2;
            // 
            // label2
            // 
            this.label2.AutoSize = true;
            this.label2.Location = new System.Drawing.Point(12, 48);
            this.label2.Name = "label2";
            this.label2.Size = new System.Drawing.Size(74, 15);
            this.label2.TabIndex = 3;
            this.label2.Text = "Region color";
            // 
            // btnCancel
            // 
            this.btnCancel.BackColor = System.Drawing.Color.DimGray;
            this.btnCancel.FlatAppearance.BorderSize = 0;
            this.btnCancel.FlatStyle = System.Windows.Forms.FlatStyle.Flat;
            this.btnCancel.Location = new System.Drawing.Point(239, 333);
            this.btnCancel.Name = "btnCancel";
            this.btnCancel.Size = new System.Drawing.Size(75, 23);
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
            this.btnAccept.Location = new System.Drawing.Point(158, 333);
            this.btnAccept.Name = "btnAccept";
            this.btnAccept.Size = new System.Drawing.Size(75, 23);
            this.btnAccept.TabIndex = 5;
            this.btnAccept.Text = "Accept";
            this.btnAccept.UseVisualStyleBackColor = false;
            this.btnAccept.Click += new System.EventHandler(this.btnAccept_Click);
            // 
            // tkAlpha
            // 
            this.tkAlpha.Location = new System.Drawing.Point(269, 69);
            this.tkAlpha.Maximum = 255;
            this.tkAlpha.Name = "tkAlpha";
            this.tkAlpha.Orientation = System.Windows.Forms.Orientation.Vertical;
            this.tkAlpha.Size = new System.Drawing.Size(45, 229);
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
            this.txtAlpha.Location = new System.Drawing.Point(269, 304);
            this.txtAlpha.Name = "txtAlpha";
            this.txtAlpha.ReadOnly = true;
            this.txtAlpha.Size = new System.Drawing.Size(45, 23);
            this.txtAlpha.TabIndex = 7;
            this.txtAlpha.Text = "128";
            this.txtAlpha.TextAlign = System.Windows.Forms.HorizontalAlignment.Center;
            // 
            // label3
            // 
            this.label3.AutoSize = true;
            this.label3.Location = new System.Drawing.Point(272, 51);
            this.label3.Name = "label3";
            this.label3.Size = new System.Drawing.Size(38, 15);
            this.label3.TabIndex = 8;
            this.label3.Text = "Alpha";
            // 
            // SelectedRegionDialog
            // 
            this.AcceptButton = this.btnAccept;
            this.AutoScaleDimensions = new System.Drawing.SizeF(7F, 15F);
            this.AutoScaleMode = System.Windows.Forms.AutoScaleMode.Font;
            this.BackColor = System.Drawing.Color.FromArgb(((int)(((byte)(32)))), ((int)(((byte)(32)))), ((int)(((byte)(32)))));
            this.CancelButton = this.btnCancel;
            this.ClientSize = new System.Drawing.Size(321, 365);
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
            this.FormBorderStyle = System.Windows.Forms.FormBorderStyle.FixedSingle;
            this.MaximizeBox = false;
            this.MinimizeBox = false;
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