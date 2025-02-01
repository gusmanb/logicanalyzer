using System;
using System.Collections.Generic;
using System.Linq;
using System.Text;
using System.Threading.Tasks;

namespace SharedDriver
{
    public class BurstInfo
    {
        public int BurstSampleStart { get; set; }
        public int BurstSampleEnd { get; set; }
        public ulong BurstSampleGap { get; set; }
        public ulong BurstTimeGap { get; set; }

        public string GetTime()
        {
            const double nanoInMicro = 1000.0;
            const double nanoInMilli = 1000000.0;
            const double nanoInSecond = 1000000000.0;

            if (BurstTimeGap < nanoInMicro)
            {
                return $"{BurstTimeGap} ns";
            }
            else if (BurstTimeGap < nanoInMilli)
            {
                double microseconds = BurstTimeGap / nanoInMicro;
                return $"{microseconds:F3} µs";
            }
            else if (BurstTimeGap < nanoInSecond)
            {
                double milliseconds = BurstTimeGap / nanoInMilli;
                return $"{milliseconds:F3} ms";
            }
            else
            {
                double seconds = BurstTimeGap / nanoInSecond;
                return $"{seconds:F3} s";
            }
        }

        public override string ToString()
        {
            string text = $"Burst: {BurstSampleStart} to {BurstSampleEnd}\nGap: {GetTime()} ({BurstSampleGap} samples)";
            return text;
        }
    }
}
