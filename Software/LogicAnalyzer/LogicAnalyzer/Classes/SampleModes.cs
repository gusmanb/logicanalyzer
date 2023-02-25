using Microsoft.CodeAnalysis.CSharp.Syntax;
using System;
using System.Collections.Generic;
using System.Linq;
using System.Text;
using System.Threading.Tasks;

namespace LogicAnalyzer.Classes
{
    public static class SampleModes
    {
        public static SampleMode Mode0 = new SampleMode { MinPreSamples = 2, MaxPreSamples = 98303, MinPostSamples = 512, MaxPostSamples = 131069 };
        public static SampleMode Mode1 = new SampleMode { MinPreSamples = 2, MaxPreSamples = 49151, MinPostSamples = 512, MaxPostSamples = 65533 };
        public static SampleMode Mode2 = new SampleMode { MinPreSamples = 2, MaxPreSamples = 24576, MinPostSamples = 512, MaxPostSamples = 32765 };

        public static SampleMode Modes(int Mode) 
        {
            switch (Mode)
            {
                case 0:
                    return Mode0;
                    break;
                case 1:
                    return Mode1;
                    break;
                case 2:
                    return Mode2;
                    break;
            }

            throw new IndexOutOfRangeException("Modes accepted: 0 to 2");
        }
    }

    public class SampleMode
    {
        public int MinPreSamples { get; set; }
        public int MaxPreSamples { get; set; }
        public int MinPostSamples { get; set; }
        public int MaxPostSamples { get; set; }

        public int MaxTotalSamples { get { return MinPreSamples + MaxPostSamples; } }
    }
}
