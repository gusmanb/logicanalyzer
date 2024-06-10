using System;
using System.Collections.Generic;
using System.Linq;
using System.Runtime.CompilerServices;
using System.Text;
using System.Threading.Tasks;

namespace LogicAnalyzer.Classes
{
    public class BurstInfo
    {
        public int SampleNumber { get; set; }

        public uint Nanoseconds { get; set; }

        public string GetTime()
        {
            DefaultInterpolatedStringHandler defaultInterpolatedStringHandler;
            if (Nanoseconds < 1000.0)
            {
                defaultInterpolatedStringHandler = new DefaultInterpolatedStringHandler(3, 1);
                defaultInterpolatedStringHandler.AppendFormatted<uint>(Nanoseconds);
                defaultInterpolatedStringHandler.AppendLiteral(" ns");
                return defaultInterpolatedStringHandler.ToStringAndClear();
            }
            if (Nanoseconds < 1000000.0)
            {
                double microseconds = Nanoseconds / 1000.0;
                defaultInterpolatedStringHandler = new DefaultInterpolatedStringHandler(3, 1);
                defaultInterpolatedStringHandler.AppendFormatted<double>(microseconds, "F3");
                defaultInterpolatedStringHandler.AppendLiteral(" µs");
                return defaultInterpolatedStringHandler.ToStringAndClear();
            }
            if (Nanoseconds < 1000000000.0)
            {
                double milliseconds = Nanoseconds / 1000000.0;
                defaultInterpolatedStringHandler = new DefaultInterpolatedStringHandler(3, 1);
                defaultInterpolatedStringHandler.AppendFormatted<double>(milliseconds, "F3");
                defaultInterpolatedStringHandler.AppendLiteral(" ms");
                return defaultInterpolatedStringHandler.ToStringAndClear();
            }
            double seconds = Nanoseconds / 1000000000.0;
            defaultInterpolatedStringHandler = new DefaultInterpolatedStringHandler(2, 1);
            defaultInterpolatedStringHandler.AppendFormatted<double>(seconds, "F3");
            defaultInterpolatedStringHandler.AppendLiteral(" s");
            return defaultInterpolatedStringHandler.ToStringAndClear();
        }
    }
}
