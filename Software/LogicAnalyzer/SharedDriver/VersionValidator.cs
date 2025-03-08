using System;
using System.Collections.Generic;
using System.Linq;
using System.Text;
using System.Text.RegularExpressions;
using System.Threading.Tasks;

namespace SharedDriver
{
    internal static class VersionValidator
    {
        public const int MAJOR_VERSION = 6;
        public const int MINOR_VERSION = 5;

        static Regex regVersion = new Regex(".*?(V([0-9]+)_([0-9]+))$");

        public static DeviceVersion GetVersion(string? DeviceVersion)
        {
            var verMatch = regVersion.Match(DeviceVersion ?? "");

            if (verMatch == null || !verMatch.Success || !verMatch.Groups[2].Success)
                return new DeviceVersion { IsValid = false };

            int majorVer = int.Parse(verMatch.Groups[2].Value);
            int minorVer = int.Parse(verMatch.Groups[3].Value);

            return new DeviceVersion
            {
                Major = majorVer,
                Minor = minorVer,
                IsValid = majorVer >= MAJOR_VERSION && (majorVer > MAJOR_VERSION || minorVer >= MINOR_VERSION)
            };
        }
    }

    internal class DeviceVersion
    {
        public int Major { get; set; }
        public int Minor { get; set; }
        public bool IsValid { get; set; }
    }
}
