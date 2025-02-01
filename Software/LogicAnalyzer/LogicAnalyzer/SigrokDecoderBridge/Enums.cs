using System;
using System.Collections.Generic;
using System.Linq;
using System.Text;
using System.Threading.Tasks;

namespace SigrokDecoderBridge
{
    public enum SigrokOptionType
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
        /// An double setting, represented by a numeric up/down box
        /// </summary>
        Double,
        /// <summary>
        /// A list setting, represented by a dropdown list
        /// </summary>
        List,
        /// <summary>
        /// A string setting, represented by a text box
        /// </summary>
        String
    }


    public enum ProtocolAnalyzerSegmentShape
    {
        Rectangle,
        RoundRectangle,
        Hexagon,
        Circle
    }


}
