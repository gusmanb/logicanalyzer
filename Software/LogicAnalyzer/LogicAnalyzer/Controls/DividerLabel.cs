using System;
using System.Collections.Generic;
using System.Linq;
using System.Text;
using System.Threading.Tasks;

namespace LogicAnalyzer
{
    public class DividerLabel : Label
    {
        #region Members
        /// <summary>Spacing between the end of the text and the start of the line.</summary>
        private int m_DividerSpacing;
        /// <summary>style of the divider line</summary>
        private Border3DStyle m_BorderStyle = Border3DStyle.Etched;
        /// <summary>whether to auto-size the height based on text height and padding.</summary>
        private bool m_AutoSizeHeight = false;
        #endregion

        #region Accessors
        /// <summary>Border style of the line.</summary>
        [System.ComponentModel.Category("Appearance")]
        public Border3DStyle LineStyle
        {
            get { return m_BorderStyle; }
            set
            {
                if (value != m_BorderStyle)
                {
                    m_BorderStyle = value;
                    Invalidate();
                }
            }
        }
        /// <summary>Whether to auto-size the height based on the text height and padding.</summary>
        [System.ComponentModel.Category("Appearance")]
        public bool AutoSizeHeight
        {
            get { return m_AutoSizeHeight; }
            set
            {
                if (value != m_AutoSizeHeight)
                {
                    m_AutoSizeHeight = value;
                    if (value)
                        ApplyAutoHeight();
                }
            }
        }
        /// <summary>Spacing between the end of the text and the start of the divider line.</summary>
        public int DividerSpacing
        {
            get { return m_DividerSpacing; }
            set
            {
                if (value != m_DividerSpacing)
                {
                    m_DividerSpacing = value;
                    Invalidate();
                }
            }
        }
        #endregion

        #region Methods
        /// <summary>OnPaint override</summary>
        /// <param name="e"></param>
        protected override void OnPaint(PaintEventArgs e)
        {
            Graphics g = e.Graphics;
            Brush brush = new SolidBrush(ForeColor);
            SizeF textSize = g.MeasureString(Text, Font, Width);
            g.DrawString(Text, Font, brush, Padding.Left, Padding.Top);
            int textLeft = Padding.Left + (int)(textSize.Width + DividerSpacing);
            if (textLeft < Width)
            {
                int textTop = Padding.Top + (int)(textSize.Height / 2);
                ControlPaint.DrawBorder3D(
                          g,
                          textLeft,
                          textTop,
                          Width - textLeft,
                          5,
                          m_BorderStyle,
                          Border3DSide.Top);
            }
        }
        /// <summary></summary>
        /// <param name="e"></param>
        protected override void OnTextChanged(EventArgs e)
        {
            base.OnTextChanged(e);
            ApplyAutoHeight();
        }
        /// <summary></summary>
        /// <param name="e"></param>
        protected override void OnFontChanged(EventArgs e)
        {
            base.OnFontChanged(e);
            ApplyAutoHeight();
        }
        /// <summary></summary>
        /// <param name="e"></param>
        protected override void OnResize(EventArgs e)
        {
            base.OnResize(e);
            ApplyAutoHeight();
        }
        /// <summary></summary>
        /// <param name="e"></param>
        protected override void OnPaddingChanged(EventArgs e)
        {
            base.OnPaddingChanged(e);
            ApplyAutoHeight();
        }
        /// <summary>apply auto height, if necessary.</summary>
        private void ApplyAutoHeight()
        {
            if (m_AutoSizeHeight)
                Height = GetPreferredSize(Size.Empty).Height;
        }
        #endregion

        #region Constructor
        /// <summary>default constructor</summary>
        public DividerLabel()
        {
            SetStyle(ControlStyles.DoubleBuffer, true);
            SetStyle(ControlStyles.AllPaintingInWmPaint, true);
            SetStyle(ControlStyles.ResizeRedraw, true);
        }
        #endregion
    }
}
