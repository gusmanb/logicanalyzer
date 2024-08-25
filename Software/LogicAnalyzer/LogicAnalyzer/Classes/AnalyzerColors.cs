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

        public static Color FromHex(string Hex)
        {
            if (Hex.StartsWith("#"))
                Hex = Hex.Substring(1);

            if (Hex.Length != 6)
                throw new ArgumentException("Hex color must be 6 characters long");

            return Color.FromRgb(
                Convert.ToByte(Hex.Substring(0, 2), 16),
                Convert.ToByte(Hex.Substring(2, 2), 16),
                Convert.ToByte(Hex.Substring(4, 2), 16)
            );
        }

        public static Color UserLineColor = Colors.Cyan;

        public static Color[] BgChannelColors => new Color[]    
        {
            Color.FromRgb(36,36,36),
            Color.FromRgb(28,28,28),
        };

        public static Color[] AnnColors => new Color[]
        {
            Color.FromArgb(255, 255, 69, 0),    // OrangeRed
            Color.FromArgb(255, 50, 205, 50),   // LimeGreen
            Color.FromArgb(255, 0, 191, 255),   // DeepSkyBlue
            Color.FromArgb(255, 255, 20, 147),  // DeepPink
            Color.FromArgb(255, 238, 130, 238), // Violet
            Color.FromArgb(255, 255, 215, 0),   // Gold
            Color.FromArgb(255, 72, 61, 139),   // DarkSlateBlue
            Color.FromArgb(255, 32, 178, 170),  // LightSeaGreen
            Color.FromArgb(255, 218, 112, 214), // Orchid
            Color.FromArgb(255, 60, 179, 113),  // MediumSeaGreen
            Color.FromArgb(255, 240, 128, 128), // LightCoral
            Color.FromArgb(255, 70, 130, 180),  // SteelBlue
            Color.FromArgb(255, 123, 104, 238), // MediumSlateBlue
            Color.FromArgb(255, 199, 21, 133),  // MediumVioletRed
            Color.FromArgb(255, 144, 238, 144), // LightGreen
            Color.FromArgb(255, 255, 160, 122), // LightSalmon
            Color.FromArgb(255, 32, 178, 170),  // LightSeaGreen
            Color.FromArgb(255, 95, 158, 160),  // CadetBlue
            Color.FromArgb(255, 255, 69, 0),    // OrangeRed
            Color.FromArgb(255, 0, 128, 128),   // Teal
            Color.FromArgb(255, 255, 105, 180), // HotPink
            Color.FromArgb(255, 0, 206, 209),   // DarkTurquoise
            Color.FromArgb(255, 46, 139, 87),   // SeaGreen
            Color.FromArgb(255, 255, 20, 147),  // DeepPink
            Color.FromArgb(255, 255, 99, 71),   // Tomato
            Color.FromArgb(255, 0, 255, 127),   // SpringGreen
            Color.FromArgb(255, 221, 160, 221), // Plum
            Color.FromArgb(255, 176, 224, 230), // PowderBlue
            Color.FromArgb(255, 128, 128, 0),   // Olive
            Color.FromArgb(255, 255, 140, 0),   // DarkOrange
            Color.FromArgb(255, 139, 69, 19),   // SaddleBrown
            Color.FromArgb(255, 34, 139, 34),   // ForestGreen
            Color.FromArgb(255, 255, 165, 0),   // Orange
            Color.FromArgb(255, 205, 92, 92),   // IndianRed
            Color.FromArgb(255, 0, 139, 139),   // DarkCyan
            Color.FromArgb(255, 238, 232, 170), // PaleGoldenrod
            Color.FromArgb(255, 255, 127, 80),  // Coral
            Color.FromArgb(255, 186, 85, 211),  // MediumOrchid
            Color.FromArgb(255, 107, 142, 35),  // OliveDrab
            Color.FromArgb(255, 147, 112, 219), // MediumPurple
            Color.FromArgb(255, 188, 143, 143), // RosyBrown
            Color.FromArgb(255, 240, 230, 140), // Khaki
            Color.FromArgb(255, 210, 105, 30),  // Chocolate
            Color.FromArgb(255, 127, 255, 212), // Aquamarine
            Color.FromArgb(255, 255, 228, 181), // Moccasin
            Color.FromArgb(255, 154, 205, 50),  // YellowGreen
            Color.FromArgb(255, 255, 228, 225), // MistyRose
            Color.FromArgb(255, 255, 239, 213), // PapayaWhip
            Color.FromArgb(255, 139, 0, 139),   // DarkMagenta
            Color.FromArgb(255, 245, 222, 179), // Wheat
            Color.FromArgb(255, 240, 255, 240), // Honeydew
            Color.FromArgb(255, 255, 248, 220), // Cornsilk
            Color.FromArgb(255, 218, 165, 32),  // Goldenrod
            Color.FromArgb(255, 192, 192, 192), // Silver
            Color.FromArgb(255, 255, 218, 185), // PeachPuff
            Color.FromArgb(255, 238, 130, 238), // Violet
            Color.FromArgb(255, 175, 238, 238), // PaleTurquoise
            Color.FromArgb(255, 72, 61, 139),   // DarkSlateBlue
            Color.FromArgb(255, 255, 160, 122), // LightSalmon
            Color.FromArgb(255, 255, 255, 0),   // Yellow
            Color.FromArgb(255, 189, 183, 107), // DarkKhaki
            Color.FromArgb(255, 0, 255, 255)    // Cyan
        };

        public static Color[] Palette => new Color[]
        {
            FromHex("#FF5733"), 
            FromHex("#33FF57"), 
            FromHex("#3357FF"), 
            FromHex("#FF33A1"),
            FromHex("#FFBD33"), 
            FromHex("#33FFF6"), 
            FromHex("#FF5733"), 
            FromHex("#57FF33"), 
            FromHex("#5733FF"), 
            FromHex("#33FFBD"), 
            FromHex("#FF33BD"),
            FromHex("#BD33FF"), 
            FromHex("#BDFF33"), 
            FromHex("#33FF57"), 
            FromHex("#FF33F6"), 
            FromHex("#F6FF33"),
            FromHex("#33FF73"), 
            FromHex("#FF7333"), 
            FromHex("#FF33C1"), 
            FromHex("#33FF85"),
            FromHex("#33C1FF"), 
            FromHex("#C1FF33"), 
            FromHex("#7333FF"), 
            FromHex("#FF3385"),
            FromHex("#3385FF"), 
            FromHex("#85FF33"), 
            FromHex("#33FF99"), 
            FromHex("#9933FF"),
            FromHex("#99FF33"), 
            FromHex("#FF3399"), 
            FromHex("#FF9C33"), 
            FromHex("#FF33E7"),
            FromHex("#E733FF"), 
            FromHex("#33E7FF"), 
            FromHex("#FF33C7"), 
            FromHex("#C733FF"),
            FromHex("#FF338E"), 
            FromHex("#338EFF"), 
            FromHex("#8EFF33"), 
            FromHex("#FF338E"),
            FromHex("#33FF9C"), 
            FromHex("#FF9C33"), 
            FromHex("#339CFF"), 
            FromHex("#FF339C"),
            FromHex("#9C33FF"), 
            FromHex("#FF8E33"), 
            FromHex("#33E733"), 
            FromHex("#339CFF"),
            FromHex("#9CFF33"), 
            FromHex("#FF339C"), 
            FromHex("#FF9C33"), 
            FromHex("#33FF9C"),
            FromHex("#FF33E7"), 
            FromHex("#E7FF33"), 
            FromHex("#33FFC7"), 
            FromHex("#C7FF33"),
            FromHex("#33F6FF"), 
            FromHex("#FF5733"), 
            FromHex("#FF33F6"), 
            FromHex("#F6FF33"),
            FromHex("#5733FF"), 
            FromHex("#33BDFF"), 
            FromHex("#BD33FF"), 
            FromHex("#33FFBD")
        };

        public static Color ErrorColor => Colors.Red;

        public static Color TxtColor => Colors.White;

        public static Color GetColor(int Index)
        {
            return Palette[Index % Palette.Length];
        }
    }
}
