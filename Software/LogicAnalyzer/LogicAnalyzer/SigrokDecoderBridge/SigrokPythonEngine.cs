using LogicAnalyzer.SigrokDecoderBridge;
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
                try
                {
                    Log("Initializing python system...");

                    string? pythonPath = "";

                    string cfgFile = Path.Combine(BasePath, "python.cfg");
                    if (File.Exists(cfgFile))
                    {
                        Log("Reading python path from config file...");
                        pythonPath = File.ReadAllText(cfgFile);
                        Log($"Stablished path: {pythonPath}");
                    }
                    else
                    {
                        Log("Initializing python installation detection...");
                        PythonInstallation py = new PythonInstallation("python");
                        PythonInstallation py3 = new PythonInstallation("python3");

                        var validInstallations = new[] { py, py3 }.Where(p => p.Success && p.MajorVersion == 3).ToArray();

                        Log("Valid installations found: " + validInstallations.Length);

                        if (validInstallations.Length > 0)
                        {
                            var selectedVersion = validInstallations.OrderByDescending(p => p.MinorVersion).First();
                            pythonPath = selectedVersion.Path;
                            Log($"Selected version: {selectedVersion.MajorVersion}.{selectedVersion.MinorVersion}");
                            Log($"Stablished path: {selectedVersion.Path}");
                        }
                        else
                        {
                            Log("No valid python installation found, aborting startup.");
                            return false;
                        }

                    }

                    if (string.IsNullOrWhiteSpace(pythonPath))
                    {
                        Log("Python library not found, aborting startup.");
                        return false;
                    }

                    Log($"Initializing decoders...");
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

                    Log($"Python initialization completed.");

                    return true;
                }
                catch(Exception ex) 
                {
                    Log($"Error initializing python engine: {ex.Message} - {ex.StackTrace}");
                    return false;
                }
            }

            return true;
        }

        private static void Log(string message)
        {
            File.AppendAllText("PythonInitLog.txt", $"{DateTime.Now.ToShortDateString()} - {DateTime.Now.ToShortDateString()} -> {message}" + Environment.NewLine);
        }

        public static void EnsureDestroyed()
        {
            if (!initialized)
                return;

            PythonEngine.Shutdown();
        }

    }
}
