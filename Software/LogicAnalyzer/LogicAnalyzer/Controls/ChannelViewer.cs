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
    public partial class ChannelViewer : UserControl
    {
        int[] channels;
        List<TextBox> boxes = new List<TextBox>();
        Font boxFont = new Font("Segoe UI", 7, FontStyle.Regular);
        public int[] Channels 
        { 
            get { return channels; }
            set { channels = value; CreateBoxes(); this.Invalidate(); } 
        }

        public string[] ChannelsText 
        { 
            get { return boxes.Select(b => b.Text).ToArray(); }
            set 
            {
                if (value == null || channels == null || value.Length != channels.Length)
                    return;
                else
                {
                    for (int buc = 0; buc < value.Length; buc++)
                        boxes[buc].Text = value[buc];
                }
            }
        }

        StringFormat textFormat = new StringFormat { LineAlignment = StringAlignment.Center, Alignment = StringAlignment.Center };

        public ChannelViewer()
        {
            InitializeComponent();
            SetStyle(ControlStyles.AllPaintingInWmPaint | ControlStyles.OptimizedDoubleBuffer, true);
            SetStyle(ControlStyles.ResizeRedraw, true);
            SetStyle(ControlStyles.Opaque, true);
        }

        void CreateBoxes()
        {
            
            foreach (var control in boxes)
            {
                this.Controls.Remove(control);
                control.Dispose();
            }

            boxes.Clear();

            if (channels == null)
                return;

            float channelHeight = this.Height / (float)channels.Length;
            float quarterHeight = channelHeight / 4;

            for (int i = 0; i < channels.Length; i++)
            {
                var box = new TextBox();
                box.Visible = true;
                box.Width = this.Width - 10;
                box.Top = (int)(((i + 1) * channelHeight) - (quarterHeight + 7));
                box.Left = 5;
                box.Height = 12;
                box.Anchor = AnchorStyles.Top;
                box.BorderStyle = BorderStyle.None;
                box.Font = boxFont;
                box.AutoSize = false;
                box.TextAlign = HorizontalAlignment.Center;
                box.BackColor = Color.DimGray;
                box.ForeColor = Color.LightGray;

                this.Controls.Add(box);
                boxes.Add(box);
            }
            
        }

        protected override void OnPaint(PaintEventArgs e)
        {
            base.OnPaint(e);
            e.Graphics.SetClip(new Rectangle(Point.Empty, this.Size));
            e.Graphics.Clear(Color.Black);


            if (channels == null)
                return;

            float channelHeight = this.Height / (float)channels.Length;
            float halfHeight = channelHeight / 2;

            for (int chan = 0; chan < channels.Length; chan++)
            {

                if ((chan % 2) == 1)
                {
                    e.Graphics.FillRectangle(ChannelColors.ChannlBgBrush, new RectangleF(0, chan * channelHeight, this.Width, channelHeight));
                }

                var rect = new RectangleF(0, channelHeight * chan, this.Width, halfHeight);
                e.Graphics.DrawString($"Channel {channels[chan] + 1}", this.Font, ChannelColors.ChannelBrushes[chan], rect, textFormat);
            }
        }

        protected override void OnResize(EventArgs e)
        {
            if (channels != null && boxes.Count > 0)
            {
                float channelHeight = this.Height / (float)channels.Length;
                float quarterHeight = channelHeight / 4;

                for (int i = 0; i < boxes.Count; i++)
                {
                    var box = boxes[i];
                    box.Width = this.Width - 10;
                    box.Top = (int)(((i + 1) * channelHeight) - (quarterHeight + 7));
                    box.Left = 5;
                }
            }
            base.OnResize(e);
        }
    }
}
