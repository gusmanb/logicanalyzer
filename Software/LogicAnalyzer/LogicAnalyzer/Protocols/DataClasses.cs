using Avalonia;
using Avalonia.Media;
using System;
using System.Collections.Generic;
using System.Linq;
using System.Text;
using System.Threading.Tasks;

namespace LogicAnalyzer.Protocols
{
    #region Data classes
    public class ProtocolAnalyzerSetting
    {
        /// <summary>
        /// Caption to show in the GIU
        /// </summary>
        public string Caption { get; set; } = "";
        /// <summary>
        /// Type of setting
        /// </summary>
        public ProtocolAnalyzerSettingType SettingType { get; set; }
        /// <summary>
        /// If SettingType is of type "list" this array must contain the list entries
        /// </summary>
        public string[]? ListValues { get; set; }
        /// <summary>
        /// If SettingType is of type "integer" this property must contain the maximum allowed value
        /// </summary>
        public int IntegerMaximumValue { get; set; } = 0;
        /// <summary>
        /// If SettingType is of type "integer" this property must contain the minimum allowed value
        /// </summary>
        public int IntegerMinimumValue { get; set; } = 100;
        /// <summary>
        /// If SettingType is of type "boolean" this property contains the text shown in the checkbox
        /// </summary>
        public string CheckCaption { get; set; } = "";
        public enum ProtocolAnalyzerSettingType
        {
            /// <summary>
            /// A boolean setting, represented as a checkbox
            /// </summary>
            Boolean,
            /// <summary>
            /// An integer setting, represented by a numeric up/down box
            /// </summary>
            Integer,
            /// <summary>
            /// A list setting, represented by a dropdown list
            /// </summary>
            List
        }
    }
    public class ProtocolAnalyzerSettingValue
    {
        public int SettingIndex { get; set; }
        public object? Value { get; set; }
    }
    public class ProtocolAnalyzerSignal
    {
        public string SignalName { get; set; }
        public bool Required { get; set; }
    }
    public class ProtocolAnalyzerSelectedChannel
    {
        public string SignalName { get; set; }
        public int ChannelIndex { get; set; }
        public byte[] Samples { get; set; }
    }
    public class ProtocolAnalyzedChannel : ProtocolAnalyzerSelectedChannel, IDisposable
    {
        public ProtocolAnalyzedChannel(string SignalName, int ChannelIndex, ProtocolAnalyzerSegmentRendererBase SegmentRenderer, ProtocolAnalyzerDataSegment[] Segments, Color ForeColor, Color BackColor)
        {
            this.SignalName = SignalName;
            this.ChannelIndex = ChannelIndex;
            this.SegmentRenderer = SegmentRenderer;
            this.Segments = Segments;
            this.ForeColor = ForeColor;
            this.BackColor = BackColor;

        }
        public ProtocolAnalyzerSegmentRendererBase SegmentRenderer { get; set; }
        public ProtocolAnalyzerDataSegment[] Segments { get; set; }
        public Color ForeColor { get; set; }
        public Color BackColor { get; set; }

        public void Render(ProtocolAnalyzerDataSegment Segment, DrawingContext Context, Rect RenderArea)
        {
            SegmentRenderer.RenderSegment(this, Segment, Context, RenderArea);
        }
        public void Dispose()
        {

        }
    }
    public class ProtocolAnalyzerDataSegment
    {
        public int FirstSample { get; set; }
        public int LastSample { get; set; }
        public string Value { get; set; }
    }
    #endregion
}
