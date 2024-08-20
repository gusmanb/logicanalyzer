using System;
using System.Collections.Generic;
using System.Diagnostics;
using System.IO;
using System.Linq;
using System.Reflection;
using System.Text;
using System.Threading.Tasks;
using Tmds.DBus.Protocol;

namespace LogicAnalyzer.Protocols
{
    internal class ProtocolAnalyzerLoader : IDisposable
    {
        string path;

        List<ProtocolAnalyzerBase> loadedAnalyzers = new List<ProtocolAnalyzerBase>();
        List<ProtocolAnalyzerProviderBase> loadedProviders = new List<ProtocolAnalyzerProviderBase>();
        public string[] ProtocolNames { get { return loadedAnalyzers.Select(a => a.ProtocolName).ToArray(); } }

        public Dictionary<string, List<string>> CategorizedProtocols
        {
            get
            {
                var result = new Dictionary<string, List<string>>();

                var protos = ProtocolNames;

                if(protos.Length == 0)
                    return new Dictionary<string, List<string>>();

                result["All"] = new List<string>();

                result["All"].AddRange(protos);

                foreach (var analyzer in loadedAnalyzers)
                {
                    foreach (var category in analyzer.Categories)
                    {
                        if (!result.ContainsKey(category))
                            result[category] = new List<string>();

                        result[category].Add(analyzer.ProtocolName);
                    }
                }

                return result.OrderBy(p => p.Key).ToDictionary();
            }
        }

        public ProtocolAnalyzerLoader(string ProtocolStoragePath)
        {
            path = ProtocolStoragePath;

            if (!Directory.Exists(ProtocolStoragePath))
                return;

            var libraries = Directory.GetFiles(ProtocolStoragePath, "*.dll");
            var baseType = typeof(ProtocolAnalyzerBase);
            var loadBaseType = typeof(ProtocolAnalyzerProviderBase);

            AppDomain.CurrentDomain.AssemblyResolve += CurrentDomain_AssemblyResolve;

            foreach (var library in libraries)
            {
                try
                {
                    var assembly = Assembly.LoadFile(library);
                    var analyzerTypes = assembly.GetTypes().Where(t => baseType.IsAssignableFrom(t)).ToArray();

                    foreach (var type in analyzerTypes)
                    {
                        if (type.IsAbstract)
                            continue;

                        var analyzer = Activator.CreateInstance(type);
                        loadedAnalyzers.Add((ProtocolAnalyzerBase)analyzer);
                    }

                    var loaderTypes = assembly.GetTypes().Where(t => loadBaseType.IsAssignableFrom(t)).FirstOrDefault();

                    if (loaderTypes != null)
                    {
                        var loader = Activator.CreateInstance(loaderTypes) as ProtocolAnalyzerProviderBase;
                        
                        if (loader != null)
                        {
                            loadedProviders.Add(loader);
                            loadedAnalyzers.AddRange(loader.GetAnalyzers());
                        }
                    }
                }
                catch(Exception ex) 
                {
                    Debug.WriteLine(ex.Message);
                }
            }

            AppDomain.CurrentDomain.AssemblyResolve -= CurrentDomain_AssemblyResolve;
        }

        public void BeginSession()
        {
            foreach (var loader in loadedProviders)
                loader.BeginAnalysisSession();
        }

        public void EndSession()
        {
            foreach (var loader in loadedProviders)
                loader.EndAnalysisSession();
        }

        public ProtocolAnalyzerBase? GetAnalyzer(string ProtocolName)
        {
            return loadedAnalyzers.FirstOrDefault(a => a.ProtocolName == ProtocolName);
        }

        private Assembly? CurrentDomain_AssemblyResolve(object? sender, ResolveEventArgs args)
        {
            var file = Path.Combine(path, new AssemblyName(args.Name).Name + ".dll");
            if (File.Exists(file))
                return Assembly.LoadFile(file);

            return null;
        }

        public void Dispose()
        {

            foreach (var analyzer in loadedAnalyzers)
                analyzer.Dispose();

            foreach (var loader in loadedProviders)
                loader.Dispose();
        }
    }
}
