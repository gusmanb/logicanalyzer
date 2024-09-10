using Avalonia.Media;
using SharedDriver;
using System;
using System.Collections.Generic;
using System.Linq;
using System.Text;
using System.Threading.Tasks;

namespace LogicAnalyzer.Classes
{
    public static class AnalyzerColors
    {
        public static Color GetChannelColor(AnalyzerChannel Channel)
        {
            return Channel.ChannelColor == null ? GetColor(Channel.ChannelNumber) : Color.FromUInt32(Channel.ChannelColor.Value);
        }
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

        public static Color[] BgChannelColors = new Color[]    
        {
            Color.FromRgb(36,36,36),
            Color.FromRgb(28,28,28),
        };

        public static Color[] Palette = new Color[]
        {
            FromHex("#FF7333"), 
            FromHex("#33FF57"), 
            FromHex("#3357FF"), 
            FromHex("#FF33A1"),
            FromHex("#FFBD33"), 
            FromHex("#33FFF6"),
            FromHex("#BD33FF"),
            FromHex("#57FF33"), 
            FromHex("#5733FF"), 
            FromHex("#33FFBD"), 
            FromHex("#FF33BD"),
            FromHex("#FF5733"), 
            FromHex("#BDFF33"), 
            FromHex("#33FF57"), 
            FromHex("#FF33F6"), 
            FromHex("#F6FF33"),
            FromHex("#33FF73"),
            FromHex("#FF5733"),
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

        public static Color ErrorColor = Colors.Red;

        public static Color TxtColor = Colors.White;

        public static Color GetColor(int Index)
        {
            return Palette[Index % Palette.Length];
        }
    }
}
