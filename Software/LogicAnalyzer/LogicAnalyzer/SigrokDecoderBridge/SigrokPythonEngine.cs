using Python.Runtime;
using System;
using System.Collections.Generic;
using System.Diagnostics;
using System.IO;
using System.Linq;
using System.Reflection;
using System.Resources;
using System.Text;
using System.Text.RegularExpressions;
using System.Threading.Tasks;

namespace SigrokDecoderBridge
{
    internal static class SigrokPythonEngine
    {

        const string winPyScript = @"import sys;
import os.path as op;
ver = str(sys.version_info.major) + str(sys.version_info.minor);
path = sys.exec_prefix;
print(op.join(path, 'Python' + ver + '.dll'));";

        const string macLinuxPyScript = @"from distutils import sysconfig;
import os.path as op;
v = sysconfig.get_config_vars();
fpaths = [op.join(v[pv], v['LDLIBRARY']) for pv in ('LIBDIR', 'LIBPL')]; 
print(list(filter(op.exists, fpaths))[0])";


        static string pythonExec;
        static string pythonVersion;

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
                return Path.Combine(BasePath, "decoders");
            }
        }

        static bool initialized = false;

        public static bool EnsureInitialized()
        {
            if (!initialized)
            {
                string? pythonPath = "";

                string cfgFile = Path.Combine(BasePath, "python.cfg");
                if (File.Exists(cfgFile))
                {
                    pythonPath = File.ReadAllText(cfgFile);
                }
                else
                {
                    pythonPath = FindPythonLibrary();
                }

                if (string.IsNullOrWhiteSpace(pythonPath))
                    return false;

                //Ensure the decode script is in place

                var info = Assembly.GetExecutingAssembly().GetName();
                var name = info.Name;
                using var stream = Assembly
                    .GetExecutingAssembly()
                    .GetManifestResourceStream($"LogicAnalyzer.SigrokDecoderBridge.sigrokdecode.py")!;
                using var output = File.Create(Path.Combine(DecoderPath, "sigrokdecode.py"));
                stream.CopyTo(output);


                Runtime.PythonDLL = pythonPath;


                PythonEngine.Initialize();

                dynamic os = Py.Import("os");
                dynamic sys = Py.Import("sys");
                sys.path.append(DecoderPath);

                initialized = true;

                return true;
            }

            return true;
        }

        private static string? FindPythonLibrary()
        {

            string? version = GetPythonVersion("python3");

            if (version == null)
            {
                version = GetPythonVersion("python");

                if (version == null)
                    return null;
                else
                    pythonExec = "python";
            }
            else
                pythonExec = "python3";

            if (!version.StartsWith("3"))
                return null;

            pythonVersion = version;

            if (System.OperatingSystem.IsMacOS() || System.OperatingSystem.IsLinux())
            {
                var res = RunPythonScript(pythonExec, macLinuxPyScript);

                if (res == null)
                    return null;

                return res.Split(new[] { '\r', '\n' }).FirstOrDefault();
            }
            else if (System.OperatingSystem.IsWindows())
            {
                var res = RunPythonScript(pythonExec, winPyScript);

                if (res == null)
                    return null;

                return res.Split(new[] { '\r', '\n' }).FirstOrDefault();
            }
            else
            {
                return null;
            }
        }

        private static string? GetPythonVersion(string PythonExecutable)
        {
            try
            {
                ProcessStartInfo sInfo = new ProcessStartInfo(PythonExecutable, $"-c \"import sys; ver = str(sys.version_info.major) + str(sys.version_info.minor); print(ver)\"");

                sInfo.RedirectStandardOutput = true;
                sInfo.UseShellExecute = false;
                sInfo.CreateNoWindow = true;

                var proc = Process.Start(sInfo);

                if (proc == null)
                    return null;

                proc.WaitForExit();
                var result = proc.StandardOutput.ReadToEnd();
                return result?.Trim();
            }
            catch { return null; }
        }

        private static string? RunPythonScript(string exec, string script)
        {
            try
            {
                ProcessStartInfo sInfo = new ProcessStartInfo(exec, $"-c \"{script}\"");

                sInfo.RedirectStandardOutput = true;
                sInfo.UseShellExecute = false;
                sInfo.CreateNoWindow = true;

                var proc = Process.Start(sInfo);

                if (proc == null)
                    return null;

                proc.WaitForExit();
                var result = proc.StandardOutput.ReadToEnd();
                return result?.Trim();
            }
            catch { return null; }
        }

        public static void EnsureDestroyed()
        {
            if (!initialized)
                return;

            PythonEngine.Shutdown();
        }

    }
}
