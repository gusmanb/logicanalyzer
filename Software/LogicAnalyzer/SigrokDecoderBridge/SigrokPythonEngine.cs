using Avalonia;
using Python.Runtime;
using System;
using System.Collections.Generic;
using System.Diagnostics;
using System.Linq;
using System.Reflection;
using System.Resources;
using System.Text;
using System.Text.RegularExpressions;
using System.Threading.Tasks;

namespace SigrokDecoderBridge
{
    public static class SigrokPythonEngine
    {
        public static string BasePath
        {
            get
            {
                return Path.GetFullPath(Path.GetDirectoryName(typeof(SigrokPythonEngine).GetTypeInfo().Assembly.Location) ?? ".");
            }
        }

        public static string DecoderPath
        {
            get
            {
                return Path.Combine(BasePath, "SigrokDecoders");
            }
        }

        static bool initialized = false;

        public static void EnsureInitialized()
        {
            if (!initialized)
            {
                string pythonPath = "";

                string cfgFile = Path.Combine(BasePath, "python.cfg");
                if (File.Exists(cfgFile))
                {
                    pythonPath = File.ReadAllText(cfgFile);
                }
                else
                {
                    try
                    {
                        ProcessStartInfo sInfo = new ProcessStartInfo("python", "-c \"import sys; print(sys.executable)\"");
                        sInfo.RedirectStandardOutput = true;
                        sInfo.UseShellExecute = false;
                        sInfo.CreateNoWindow = true;

                        var proc = Process.Start(sInfo);
                        proc.WaitForExit();
                        var tmpPath = Path.GetFullPath(Path.GetDirectoryName(proc.StandardOutput.ReadToEnd().Trim()));

                        var reg = new Regex("python[0-9][0-9]+[^\\\\]*?\\.dll", RegexOptions.IgnoreCase);
                        var dlls = Directory.GetFiles(tmpPath, "*.dll").Where(t => reg.IsMatch(t));
                        pythonPath = dlls.FirstOrDefault();
                    }
                    catch { }
                }

                if(string.IsNullOrWhiteSpace(pythonPath))
                {
                    throw new Exception("Unable to find Python installation");
                }

                //Ensure the decode script is in place

                var info = Assembly.GetExecutingAssembly().GetName();
                var name = info.Name;
                using var stream = Assembly
                    .GetExecutingAssembly()
                    .GetManifestResourceStream($"{name}.sigrokdecode.py")!;
                using var output = File.Create(Path.Combine(DecoderPath, "sigrokdecode.py"));
                stream.CopyTo(output);


                Runtime.PythonDLL = pythonPath;
                PythonEngine.Initialize();

                dynamic os = Py.Import("os");
                dynamic sys = Py.Import("sys");
                sys.path.append(DecoderPath);

                initialized = true;
            }
        }

        public static void EnsureDestroyed()
        {
            if (!initialized)
                return;

            PythonEngine.Shutdown();
        }

        public static string[] GetKeys(dynamic PythonObject)
        {
            List<string> items = new List<string>();

            foreach (var key in PythonObject)
                items.Add(key.ToString());

            return items.ToArray();
        }
    }
}
