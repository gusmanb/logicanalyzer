using Avalonia.Media;
using SigrokDecoderBridge;
using System;
using System.Collections.Generic;
using System.Linq;
using System.Text;
using System.Threading.Tasks;

namespace LogicAnalyzer.Classes
{
    public class AnnotationsGroup
    {
        public required Color GroupColor { get; set; }
        public required SigrokAnnotation[] Annotations { get; set; }
    }
}
