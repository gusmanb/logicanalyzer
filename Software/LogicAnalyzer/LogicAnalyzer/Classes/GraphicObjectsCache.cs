using Avalonia.Media;
using System;
using System.Collections.Generic;
using System.Linq;
using System.Text;
using System.Threading.Tasks;

namespace LogicAnalyzer.Classes
{
    public static class GraphicObjectsCache
    {
        static Dictionary<Color, Brush> _brushes = new Dictionary<Color, Brush>();
        static Dictionary<string, Pen> _pens = new Dictionary<string, Pen>();

        public static Brush GetBrush(Color BrushColor)
        {
            if(!_brushes.ContainsKey(BrushColor))
            {
                SolidColorBrush brush = new SolidColorBrush(BrushColor);
                _brushes.Add(BrushColor, brush);
            }

            return _brushes[BrushColor];
        }

        public static Pen GetPen(Color PenColor, double PenThickness, IDashStyle Style = null)
        {
            string key = "COLOR" + PenColor.ToString() + PenThickness.ToString() + GetDashName(Style);

            if (!_pens.ContainsKey(key))
            {
                Pen pen = new Pen(PenColor.ToUint32(), PenThickness);
                pen.DashStyle = Style;
                _pens.Add(key, pen);
            }

            return _pens[key];
        }

        public static Pen GetPen(IBrush PenBrush, double PenThickness, IDashStyle Style = null)
        {
            string key = "BRUSH" + PenBrush.GetHashCode().ToString() + PenThickness.ToString() + GetDashName(Style);

            if (!_pens.ContainsKey(key))
            {
                Pen pen = new Pen(PenBrush, PenThickness);
                pen.DashStyle = Style;
                _pens.Add(key, pen);
            }

            return _pens[key];
        }

        static string GetDashName(IDashStyle Style)
        {
            return Style == null ? "" : string.Join("", Style.Dashes) + "-" + Style.Offset.ToString();
        }
    }
}
