using System;
using System.Collections.Generic;
using System.Linq;
using System.Text;
using System.Threading.Tasks;

namespace SigrokDecoderBridge
{
    internal class SigrokOutputValue
    {
        public int StartSample { get; set; }
        public int EndSample { get; set; }
        public required dynamic Value { get; set; }
    }
}
