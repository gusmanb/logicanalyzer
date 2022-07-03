using System;
using System.Collections.Generic;
using System.Linq;
using System.Text;
using System.Threading.Tasks;

namespace LogicAnalyzer
{
    public static class ChannelColors
    {
        public static Pen[] ChannelPens = new Pen[24];
        public static Brush[] ChannelBrushes = new Brush[24];
        public static Brush ChannlBgBrush = new SolidBrush(Color.FromArgb(64, 64, 64));
        static ChannelColors()
        {
            ChannelPens[0] = new Pen(Color.FromArgb(254, 0, 0));
            ChannelPens[1] = new Pen(Color.FromArgb(128, 255, 0));
            ChannelPens[2] = new Pen(Color.FromArgb(1, 255, 255));
            ChannelPens[3] = new Pen(Color.FromArgb(127, 0, 255));

            ChannelPens[4] = new Pen(Color.FromArgb(255, 64, 1));
            ChannelPens[5] = new Pen(Color.FromArgb(64, 255, 1));
            ChannelPens[6] = new Pen(Color.FromArgb(0, 192, 255));
            ChannelPens[7] = new Pen(Color.FromArgb(191, 0, 254));

            ChannelPens[8] = new Pen(Color.FromArgb(255, 127, 0));
            ChannelPens[9] = new Pen(Color.FromArgb(0, 255, 1));
            ChannelPens[10] = new Pen(Color.FromArgb(0, 128, 255));
            ChannelPens[11] = new Pen(Color.FromArgb(255, 0, 254));

            ChannelPens[12] = new Pen(Color.FromArgb(255, 192, 0));
            ChannelPens[13] = new Pen(Color.FromArgb(0, 255, 65));
            ChannelPens[14] = new Pen(Color.FromArgb(0, 65, 255));
            ChannelPens[15] = new Pen(Color.FromArgb(255, 0, 192));

            ChannelPens[16] = new Pen(Color.FromArgb(255, 255, 1));
            ChannelPens[17] = new Pen(Color.FromArgb(0, 254, 129));
            ChannelPens[18] = new Pen(Color.FromArgb(0, 0, 254));
            ChannelPens[19] = new Pen(Color.FromArgb(255, 0, 128));

            ChannelPens[20] = new Pen(Color.FromArgb(192, 255, 0));
            ChannelPens[21] = new Pen(Color.FromArgb(1, 255, 193));
            ChannelPens[22] = new Pen(Color.FromArgb(63, 0, 255));
            ChannelPens[23] = new Pen(Color.FromArgb(255, 1, 65));

            ChannelBrushes[0] = new SolidBrush(Color.FromArgb(254, 0, 0));
            ChannelBrushes[1] = new SolidBrush(Color.FromArgb(128, 255, 0));
            ChannelBrushes[2] = new SolidBrush(Color.FromArgb(1, 255, 255));
            ChannelBrushes[3] = new SolidBrush(Color.FromArgb(127, 0, 255));

            ChannelBrushes[4] = new SolidBrush(Color.FromArgb(255, 64, 1));
            ChannelBrushes[5] = new SolidBrush(Color.FromArgb(64, 255, 1));
            ChannelBrushes[6] = new SolidBrush(Color.FromArgb(0, 192, 255));
            ChannelBrushes[7] = new SolidBrush(Color.FromArgb(191, 0, 254));

            ChannelBrushes[8] = new SolidBrush(Color.FromArgb(255, 127, 0));
            ChannelBrushes[9] = new SolidBrush(Color.FromArgb(0, 255, 1));
            ChannelBrushes[10] = new SolidBrush(Color.FromArgb(0, 128, 255));
            ChannelBrushes[11] = new SolidBrush(Color.FromArgb(255, 0, 254));

            ChannelBrushes[12] = new SolidBrush(Color.FromArgb(255, 192, 0));
            ChannelBrushes[13] = new SolidBrush(Color.FromArgb(0, 255, 65));
            ChannelBrushes[14] = new SolidBrush(Color.FromArgb(0, 65, 255));
            ChannelBrushes[15] = new SolidBrush(Color.FromArgb(255, 0, 192));

            ChannelBrushes[16] = new SolidBrush(Color.FromArgb(255, 255, 1));
            ChannelBrushes[17] = new SolidBrush(Color.FromArgb(0, 254, 129));
            ChannelBrushes[18] = new SolidBrush(Color.FromArgb(0, 0, 254));
            ChannelBrushes[19] = new SolidBrush(Color.FromArgb(255, 0, 128));

            ChannelBrushes[20] = new SolidBrush(Color.FromArgb(192, 255, 0));
            ChannelBrushes[21] = new SolidBrush(Color.FromArgb(1, 255, 193));
            ChannelBrushes[22] = new SolidBrush(Color.FromArgb(63, 0, 255));
            ChannelBrushes[23] = new SolidBrush(Color.FromArgb(255, 1, 65));
        }
    }
}
