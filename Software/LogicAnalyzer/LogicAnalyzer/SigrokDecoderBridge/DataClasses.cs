using Python.Runtime;
using System;
using System.Collections.Generic;
using System.Linq;
using System.Text;
using System.Threading.Tasks;

namespace SigrokDecoderBridge
{
    public class SigrokChannel
    {
        public string Id { get; set; }
        public string Name { get; set; }
        public string Description { get; set; }
        public bool Required { get; set; }
        public required int Index { get; set; }
    }
    public class SigrokSelectedChannel
    {
        //Index of the channel, as provided in the channels array
        public int CaptureIndex { get; set; }
        //Index of the channel, as provided in the settings array
        public int SigrokIndex { get; set; }
    }

    public class SigrokOption
    {

        /// <summary>
        /// Caption to show in the GIU
        /// </summary>
        public string Caption { get; set; } = "";
        /// <summary>
        /// Type of setting
        /// </summary>
        public SigrokOptionType OptionType { get; set; }
        /// <summary>
        /// If SettingType is of type "list" this array must contain the list entries
        /// </summary>
        public string[]? ListValues { get; set; }
        /// <summary>
        /// If SettingType is a numeric type this property must contain the maximum allowed value
        /// </summary>
        public double MaximumValue { get; set; } = 100;
        /// <summary>
        /// If SettingType is a numeric type this property must contain the minimum allowed value
        /// </summary>
        public double MinimumValue { get; set; } = 0;
        /// <summary>
        /// If SettingType is of type "boolean" this property contains the text shown in the checkbox
        /// </summary>
        public string CheckCaption { get; set; } = "";

        /// <summary>
        /// If provided, the default value for the setting
        /// </summary>
        public object? DefaultValue { get; set; }
        public int Index { get; set; }
        public string Id { get; set; }
        internal PyObject Default { get; set; }
        public string[] Values { get; set; }
        public PyType SigrokType { get; set; }
    }

    public class SigrokOptionValue
    {
        //Index of the setting, as provided in the settings array
        public int OptionIndex { get; set; }
        //The selected value
        public object? Value { get; set; }
    }

    public class SigrokAnnotation
    {
        public string AnnotationName { get; set; }
        public SigrokAnnotationSegment[] Segments { get; set; }

    }

    public class SigrokAnnotationSegment
    {
        /// <summary>
        /// An ID used to give color to the segment
        /// </summary>
        public int TypeId { get; set; }
        /// <summary>
        /// Shape to use to render the segment
        /// </summary>
        public ProtocolAnalyzerSegmentShape Shape { get; set; }
        /// <summary>
        /// Start sample of the segment
        /// </summary>
        public int FirstSample { get; set; }
        /// <summary>
        /// End sample of the segment
        /// </summary>
        public int LastSample { get; set; }
        /// <summary>
        /// List of values. This list goes from largest to shortest possible representation
        /// </summary>
        public string[] Value { get; set; }
    }

    internal class SigrokOutputValue
    {
        public int StartSample { get; set; }
        public int EndSample { get; set; }
        public required dynamic Value { get; set; }
    }
}
