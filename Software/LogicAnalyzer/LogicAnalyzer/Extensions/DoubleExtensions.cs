using System;
using System.Collections.Generic;
using System.Linq;
using System.Text;
using System.Threading.Tasks;

namespace LogicAnalyzer.Extensions
{
    public static class DoubleExtensions
    {
        public static string ToSmallTime(this double Time)
        {
            if (Time < 0.000001)
                return $"{Math.Round(Time * 1000000000, 3)}ns";
            else if (Time < 0.001)
                return $"{Math.Round(Time * 1000000, 3)}us";
            else if (Time < 1)
                return $"{Math.Round(Time * 1000, 3)}ms";
            else
                return $"{Math.Round(Time, 3)}s";
        }

        public static string ToLargeFrequency(this double Frequency)
        {
            if (Frequency > 999999)
                return $"{Math.Round(Frequency / 1000000, 2)}Mhz";
            else if (Frequency > 999)
                return $"{Math.Round(Frequency / 1000, 2)}Khz";
            else
                return $"{Math.Round(Frequency, 2)}Hz";
        }
    }
}
