using Avalonia.Media;
using System;
using System.Collections.Generic;
using System.Linq;
using System.Text;
using System.Threading.Tasks;

namespace LogicAnalyzer.Classes
{
    public static class ColorExtensions
    {
        public static Color FindContrast(this Color theColor)
        {
            int r = theColor.R;
            int g = theColor.G;
            int b = theColor.B;

            int yiq = ((r * 299) + (g * 587) + (b * 114)) / 1000;

            return yiq >= 128 ? Colors.Black : Colors.White;
        }
    }
}
