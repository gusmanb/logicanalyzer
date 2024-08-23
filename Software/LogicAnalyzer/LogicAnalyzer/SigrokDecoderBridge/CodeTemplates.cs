using System;
using System.Collections.Generic;
using System.Linq;
using System.Text;
using System.Threading.Tasks;

namespace SigrokDecoderBridge
{
    public static class CodeTemplates
    {
        public const string ModuleTemplate = @"
using SigrokDecoderBridge;
using System;

namespace SigrokDynamicDecoders
{{

{0}

}}

";
        public const string DecoderTemplate = @"
public class Decoder{0} : SigrokDecoderBase
{{
    protected override string decoderName => ""{1}"";
}}
";
    }
}
