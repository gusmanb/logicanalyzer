using LogicAnalyzer.Extensions;
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
    public partial class BorderGroupBox : GroupBox
    {
        private Color _borderColor = Color.Black;
        private int _borderWidth = 2;
        private int _borderRadius = 5;
        private int _textIndent = 10;
        StringFormat textFormatCenter = new StringFormat { LineAlignment = StringAlignment.Center, Alignment = StringAlignment.Center };
        public BorderGroupBox() : base()
        {
            InitializeComponent();
            SetStyle(
               ControlStyles.UserPaint | ControlStyles.ResizeRedraw |
               ControlStyles.SupportsTransparentBackColor |
               ControlStyles.AllPaintingInWmPaint | ControlStyles.OptimizedDoubleBuffer,
               true);
        }

        public BorderGroupBox(int width, int radius, Color color) : base()
        {
            this._borderWidth = Math.Max(1, width);
            this._borderColor = color;
            this._borderRadius = Math.Max(0, radius);
            InitializeComponent();
        }

        public Color BorderColor
        {
            get => this._borderColor;
            set
            {
                this._borderColor = value;
                this.Invalidate();
            }
        }

        public int BorderWidth
        {
            get => this._borderWidth;
            set
            {
                if (value > 0)
                {
                    this._borderWidth = Math.Min(value, 10);
                    this.Invalidate();
                }
            }
        }

        public int BorderRadius
        {
            get => this._borderRadius;
            set
            {   // Setting a radius of 0 produces square corners...
                if (value >= 0)
                {
                    this._borderRadius = value;
                    this.Invalidate();
                }
            }
        }

        public int LabelIndent
        {
            get => this._textIndent;
            set
            {
                this._textIndent = value;
                this.Invalidate();
            }
        }

        protected override void OnPaint(PaintEventArgs e)
        {
            DrawGroupBox(e.Graphics);
        }
        private void DrawGroupBox(Graphics g)
        {
            Brush textBrush = new SolidBrush(this.ForeColor);
            SizeF strSize = g.MeasureString(this.Text, this.Font);

            Brush borderBrush = new SolidBrush(this.BorderColor);
            Pen borderPen = new Pen(borderBrush, (float)this._borderWidth);


            Rectangle rect = new Rectangle(0,
                                            (int)(strSize.Height / 2),
                                            this.Width - 1,
                                            this.Height - (int)(strSize.Height / 2) - 1);
            

            Brush labelBrush = new SolidBrush(this.BackColor);

            // Clear text and border
            g.Clear(this.BackColor);
            g.DrawRoundedRectangle(borderPen, rect.X, rect.Y, rect.Width - 1, rect.Height - 1, (float)this._borderRadius);
            /*
            // Drawing Border (added "Fix" from Jim Fell, Oct 6, '18)
            int rectX = rect.X + this._borderWidth;
            int rectHeight = (0 == this._borderWidth % 2) ? rect.Height - this._borderWidth / 2 : rect.Height - 1 - this._borderWidth / 2;
            int rectWidth = rect.Width - this._borderWidth;
            // NOTE DIFFERENCE: rectX vs rect.X and rectHeight vs rect.Height
            g.DrawRoundedRectangle(borderPen, rectX, rect.Y, rectWidth, rectHeight, (float)this._borderRadius);
            */

            // Draw text
            if (this.Text.Length > 0)
            {
                // Do some work to ensure we don't put the label outside
                // of the box, regardless of what value is assigned to the Indent:
                int width = (int)rect.Width, posX;
                posX = (this._textIndent < 0) ? Math.Max(0 - width, this._textIndent) : Math.Min(width, this._textIndent);

                posX = (posX < 0) ? rect.Width + posX - (int)strSize.Width : posX;

                RectangleF rectTxt = new RectangleF(posX, 0, strSize.Width, strSize.Height);

                g.FillRectangle(labelBrush, posX, 0, strSize.Width, strSize.Height);
                g.DrawString(this.Text, this.Font, textBrush, rectTxt, textFormatCenter);
            }
        }
    }
}
