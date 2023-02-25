using Avalonia.Media;
using System;
using System.Collections.Generic;
using System.Linq;
using System.Text;
using System.Threading.Tasks;

namespace LogicAnalyzer.Classes
{
    public static class AnalyzerColors
    {
        public static Color[] BgChannelColors => new Color[]    
        {
            Color.FromRgb(36,36,36),
            Color.FromRgb(28,28,28),
        };

        public static Color[] FgChannelColors => new Color[]
        {
            Color.FromRgb(254, 0, 0),
            Color.FromRgb(128, 255, 0),
            Color.FromRgb(1, 255, 255),
            Color.FromRgb(127, 0, 255),

            Color.FromRgb(255, 64, 1),
            Color.FromRgb(64, 255, 1),
            Color.FromRgb(0, 192, 255),
            Color.FromRgb(191, 0, 254),

            Color.FromRgb(255, 127, 0),
            Color.FromRgb(0, 255, 1),
            Color.FromRgb(0, 128, 255),
            Color.FromRgb(255, 0, 254),

            Color.FromRgb(255, 192, 0),
            Color.FromRgb(0, 255, 65),
            Color.FromRgb(0, 65, 255),
            Color.FromRgb(255, 0, 192),

            Color.FromRgb(255, 255, 1),
            Color.FromRgb(0, 254, 129),
            Color.FromRgb(0, 0, 254),
            Color.FromRgb(255, 0, 128),

            Color.FromRgb(192, 255, 0),
            Color.FromRgb(1, 255, 193),
            Color.FromRgb(63, 0, 255),
            Color.FromRgb(255, 1, 65),
        };

        public static Color ErrorColor => Colors.Red;

        public static Color TxtColor => Colors.White;
    }
}
