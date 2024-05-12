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
    /// <summary>
    /// Represents a setting presented to the user in the configuration GUI
    /// </summary>
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
    /// <summary>
    /// Represents a value set by the user in the configuration of the analyzer
    /// </summary>
    public class ProtocolAnalyzerSettingValue
    {
        //Index of the setting, as provided in the settings array
        public int SettingIndex { get; set; }
        //The selected value
        public object? Value { get; set; }
    }
    /// <summary>
    /// Represents a signal presented to the user in the configuration GUI
    /// </summary>
    public class ProtocolAnalyzerSignal
    {
        //Name to show in the GUI
        public string SignalName { get; set; }
        //If true the signal must be provided, else the signal is optional
        public bool Required { get; set; }
        /// <summary>
        /// If true the signal is a bus and the size will be requested to the protocol analyzer
        /// </summary>
        public bool IsBus { get; set; }
    }

    /// <summary>
    /// Represents a channel selected by the user in the GUI
    /// </summary>
    public class ProtocolAnalyzerSelectedChannel
    {
        //Signal name for which the channel was selected
        public string SignalName { get; set; }
        //Index (for buses)
        public int BusIndex { get; set; }
        //Channel index in the channel viewer
        public int ChannelIndex { get; set; }
        //List of samples
        public byte[] Samples { get; set; }
    }
    /// <summary>
    /// Represents an analyzed channel where we want to show overlayed information
    /// </summary>
    public class ProtocolAnalyzedChannel : ProtocolAnalyzerSelectedChannel, IDisposable
    {
        /// <summary>
        /// Constructor
        /// </summary>
        /// <param name="SignalName">Name of the signal that represents the channel</param>
        /// <param name="ChannelIndex">Channel index, the same that has been received in the ProtocolAnalyzerSelectedChannel</param>
        /// <param name="SegmentRenderer">Overlay data renderer</param>
        /// <param name="Segments">Segments to render</param>
        /// <param name="ForeColor">Fore color used by the renderer</param>
        /// <param name="BackColor">Background color used by the renderer</param>
        public ProtocolAnalyzedChannel(string SignalName, int ChannelIndex, ProtocolAnalyzerSegmentRendererBase SegmentRenderer, ProtocolAnalyzerDataSegment[] Segments, Color ForeColor, Color BackColor)
        {
            this.SignalName = SignalName;
            this.ChannelIndex = ChannelIndex;
            this.SegmentRenderer = SegmentRenderer;
            this.Segments = Segments;
            this.ForeColor = ForeColor;
            this.BackColor = BackColor;

        }
        /// <summary>
        /// Instance of the segment renderer
        /// </summary>
        public virtual ProtocolAnalyzerSegmentRendererBase SegmentRenderer { get; set; }
        /// <summary>
        /// Array of segments to render
        /// </summary>
        public virtual ProtocolAnalyzerDataSegment[] Segments { get; set; }
        /// <summary>
        /// Foreground color used by the renderer
        /// </summary>
        public virtual Color ForeColor { get; set; }
        /// <summary>
        /// Background color used by the renderer
        /// </summary>
        public virtual Color BackColor { get; set; }

        /// <summary>
        /// Function called by the program to render a segment
        /// </summary>
        /// <param name="Segment"></param>
        /// <param name="Context"></param>
        /// <param name="RenderArea"></param>
        public virtual void Render(ProtocolAnalyzerDataSegment Segment, DrawingContext Context, Rect RenderArea)
        {
            SegmentRenderer.RenderSegment(this, Segment, Context, RenderArea);
        }
        public virtual void Dispose()
        {

        }
    }
    /// <summary>
    /// Represents a data segment to overlay in the channel
    /// </summary>
    public class ProtocolAnalyzerDataSegment
    {
        /// <summary>
        /// Initial sample of the segment
        /// </summary>
        public int FirstSample { get; set; }
        /// <summary>
        /// Final sample of the segment
        /// </summary>
        public int LastSample { get; set; }
        /// <summary>
        /// Value to render in the segment
        /// </summary>
        public string Value { get; set; }
    }
    #endregion
}
