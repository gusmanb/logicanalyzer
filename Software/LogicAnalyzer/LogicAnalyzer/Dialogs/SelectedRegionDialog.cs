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
    public partial class SelectedRegionDialog : Form
    {
        public SelectedSampleRegion SelectedRegion { get; set; } = new SelectedSampleRegion();
        public SelectedRegionDialog()
        {
            InitializeComponent();
        }

        private void btnAccept_Click(object sender, EventArgs e)
        {
            if (SelectedRegion == null)
            {
                MessageBox.Show("No region selected, internal error.");
                return;
            }

            SelectedRegion.RegionColor?.Dispose();
            SelectedRegion.RegionColor = new SolidBrush(Color.FromArgb(byte.Parse(txtAlpha.Text), cwRegionColor.Color));
            SelectedRegion.RegionName = txtName.Text;
            this.DialogResult = DialogResult.OK;
            this.Close();
        }

        private void btnCancel_Click(object sender, EventArgs e)
        {
            this.DialogResult = DialogResult.Cancel;
            this.Close();
        }

        private void tkAlpha_ValueChanged(object sender, EventArgs e)
        {
            txtAlpha.Text = tkAlpha.Value.ToString();
        }
    }
}
