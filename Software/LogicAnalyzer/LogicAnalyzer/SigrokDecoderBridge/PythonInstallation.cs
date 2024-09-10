using System;
using System.Collections.Generic;
using System.Diagnostics;
using System.IO;
using System.Linq;
using System.Text;
using System.Threading.Tasks;

namespace LogicAnalyzer.SigrokDecoderBridge
{
    public class PythonInstallation
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

        public string InterpreterName { get; }
        public string? Version { get; }
        public int MajorVersion { get; set; }
        public int MinorVersion { get; set; }
        public string? Path { get; }
        public bool Success { get; }

        public PythonInstallation(string InterpreterName)
        {
            Log(InterpreterName, "Initializing Python Installation Detection...");

            this.InterpreterName = InterpreterName;

            this.Version = GetPythonVersion(InterpreterName);

            if (string.IsNullOrWhiteSpace(Version))
            {
                Log(InterpreterName, "Python version not found, aborting.");
                this.Path = "";
                this.Success = false;
                return;
            }
            else
            {
                Log(InterpreterName, $"Python version found: {Version}");

                int part;

                if (int.TryParse(Version[0].ToString(), out part))
                {
                    this.MajorVersion = part;
                }

                if (int.TryParse(Version.Substring(1), out part))
                {
                    this.MinorVersion = part;
                }

                Log(InterpreterName, $"Python version parsed: {MajorVersion}.{MinorVersion}");
            }

            this.Path = GetPythonPath(InterpreterName);

            if(string.IsNullOrWhiteSpace(Path))
            {
                Log(InterpreterName, "Cannot retrieve Python library path, aborting.");
                this.Success = false;
                return;
            }
            else
            {
                Log(InterpreterName, $"Python path found: {Path}");
                this.Success = true;
            }

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

        private static string? GetPythonPath(string PythonExecutable)
        {
            if (System.OperatingSystem.IsMacOS() || System.OperatingSystem.IsLinux())
            {
                Log(PythonExecutable, "PythonExecutable, Finding python library on Mac/Linux...");
                var res = RunPythonScript(PythonExecutable, macLinuxPyScript);

                Log(PythonExecutable, $"PythonExecutable, Script output: {res}");

                if (res == null)
                {
                    Log(PythonExecutable, "Python library not found, aborting.");
                    return null;
                }

                var path = res.Split(new[] { '\r', '\n' }, StringSplitOptions.RemoveEmptyEntries).FirstOrDefault();

                Log(PythonExecutable, $"Final python path: {path}");

                return path;
            }
            else if (System.OperatingSystem.IsWindows())
            {
                Log(PythonExecutable, "Finding python library on Windows...");
                var res = RunPythonScript(PythonExecutable, winPyScript);

                Log(PythonExecutable, $"Script output: {res}");

                if (res == null)
                {
                    Log(PythonExecutable, "Python library not found, aborting.");
                    return null;
                }

                var path = res.Split(new[] { '\r', '\n' }, StringSplitOptions.RemoveEmptyEntries).FirstOrDefault();

                Log(PythonExecutable, $"Final python path: {path}");

                return path;
            }
            else
            {
                Log(PythonExecutable, "Unknown operating system, aborting.");
                return null;
            }
        }

        private static void Log(string interpreter, string message)
        {
            File.AppendAllText("PythonInitLog.txt", $"{DateTime.Now.ToShortDateString()} - {DateTime.Now.ToShortDateString()} -> Target Interpreter: {interpreter},  {message}" + Environment.NewLine);
        }

    }
}