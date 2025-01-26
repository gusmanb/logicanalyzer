using Microsoft.Win32;
using System;
using System.Collections.Generic;
using System.Linq;
using System.Runtime.InteropServices;
using System.Runtime.Versioning;
using System.Text;
using System.Text.RegularExpressions;
using System.Threading.Tasks;

namespace SharedDriver
{
    public static class DeviceDetector
    {
        /*
         
        VID/PID: 1902/3020
        Windows: HKEY_LOCAL_MACHINE\SYSTEM\CurrentControlSet\Services\usbser\Enum
                 HKEY_LOCAL_MACHINE\SYSTEM\CurrentControlSet\Enum\USB\VID_1209&PID_3020&MI_00

        Linux:   /sys/bus/usb/devices/x-y
                                            idProduct
                                            idVendor
        
                 /sys/bus/usb/devices/x-y:1-0/tty
                                                    
         */

        const string vid = "1209";
        const string pid = "3020";

        public static DetectedDevice[] Detect()
        { 
            if(RuntimeInformation.IsOSPlatform(OSPlatform.Windows))
            {
                return DetectWindows();
            }
            else if (RuntimeInformation.IsOSPlatform(OSPlatform.Linux))
            {
                return DetectLinux();
            }

            return new DetectedDevice[0];
        }

        private static string[] DetectMac()
        {
            return new string[0];
        }

        [SupportedOSPlatform("linux")]
        private static DetectedDevice[] DetectLinux()
        {
            if(!Directory.Exists("/sys/bus/usb/devices"))
                return new DetectedDevice[0];

            List<DetectedDevice> devices = new List<DetectedDevice>();

            var regDev = new Regex(@"^[0-9]+-[0-9]+$");

            foreach (var dir in Directory.GetDirectories("/sys/bus/usb/devices"))
            {
                var devName = Path.GetFileName(dir);

                if (!regDev.IsMatch(Path.GetFileName(devName)))
                    continue;

                try
                {
                    var idVendor = File.ReadAllText(Path.Combine(dir, "idVendor")).Trim();
                    var idProduct = File.ReadAllText(Path.Combine(dir, "idProduct")).Trim();
                    string serial = File.ReadAllText(Path.Combine(dir, "serial")).Trim();

                    if (idVendor != vid || idProduct != pid)
                        continue;

                    var ttyDir = dir + ":1.0/tty";

                    if (!Directory.Exists(ttyDir))
                        continue;

                    foreach (var tty in Directory.GetDirectories(ttyDir))
                    {
                        devices.Add(new DetectedDevice { PortName = "/dev/" + Path.GetFileName(tty), DevicePath = $"/sys/bus/usb/devices/{devName}:1.0", VID = vid, PID = pid, SerialNumber = serial, ParentId = devName });
                    }
                }
                catch { continue; }
            }

            return devices.ToArray();
        }

        [SupportedOSPlatform("windows")]
        private static DetectedDevice[] DetectWindows()
        {

            Regex regVidPid = new Regex(@"VID_(?<VID>[0-9A-F]{4})&PID_(?<PID>[0-9A-F]{4})");
            Regex regParent = new Regex(@"\\(?<PARENT>[0-9a-f]&[0-9a-f]+&[0-9a-f])&[0-9a-f]+$");

            List<DetectedDevice> devices = new List<DetectedDevice>();

            try
            {
                //Find serial devices
                var rkUsbSer = Registry.LocalMachine.OpenSubKey(@"SYSTEM\CurrentControlSet\Services\usbser\Enum", false);

                if (rkUsbSer != null)
                {
                    var count = (int?)rkUsbSer.GetValue("Count");

                    if (count != null)
                    {
                        for (int buc = 0; buc < count; buc++)
                        {
                            var entry = (string?)rkUsbSer.GetValue(buc.ToString());

                            if (entry != null)
                            {
                                var match = regVidPid.Match(entry);

                                if(!match.Success)
                                    continue;

                                var idVendor = match.Groups["VID"].Value;
                                var idProduct = match.Groups["PID"].Value;

                                if(idVendor != vid || idProduct != pid)
                                    continue;

                                match = regParent.Match(entry);

                                if(!match.Success)
                                    continue;

                                var parent = match.Groups["PARENT"].Value;

                                devices.Add(new DetectedDevice { VID = vid, PID = pid, DevicePath = entry, ParentId = parent });
                            }
                        }
                    }

                }

                //Read parent info

                var rkEnum = Registry.LocalMachine.OpenSubKey($@"SYSTEM\CurrentControlSet\Enum\USB\VID_{vid}&PID_{pid}", false);

                if (rkEnum != null)
                {
                    foreach (var devSer in rkEnum.GetSubKeyNames())
                    {
                        string keyPath = $@"SYSTEM\CurrentControlSet\Enum\USB\VID_{vid}&PID_{pid}\{devSer}";

                        var rkDevice = Registry.LocalMachine.OpenSubKey(keyPath, false);

                        if (rkDevice == null)
                            continue;

                        var prefix = (string?)rkDevice.GetValue("ParentIdPrefix");

                        if(prefix == null)
                            continue;

                        var dev = devices.FirstOrDefault(d => d.ParentId == prefix);

                        if (dev != null)
                        {
                            dev.SerialNumber = devSer;
                        }
                    }
                }

                foreach (var device in devices)
                {
                    var rkSer = Registry.LocalMachine.OpenSubKey($@"SYSTEM\CurrentControlSet\Enum\{device.DevicePath}\Device Parameters", false);

                    if (rkSer != null)
                    {
                        var portName = (string?)rkSer.GetValue("PortName");

                        if(portName != null)
                            device.PortName = portName;

                    }
                }
            }
            catch { }

            return devices.Where(d => d.PortName != null && d.SerialNumber != null).ToArray();
        }
    }

    public class DetectedDevice
    {
        public string VID { get; set; }
        public string PID { get; set; }
        public string ParentId { get; set; }
        public string DevicePath { get; set; }
        public string PortName { get; set; }
        public string SerialNumber { get; set; }
        public int AssignedIndex { get; set; }
    }

}
