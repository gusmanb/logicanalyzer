using System;
using System.Collections.Generic;
using System.Linq;
using System.Reflection;
using System.Text;
using System.Threading.Tasks;

namespace LogicAnalyzer.Protocols
{
    internal class ProtocolAnalyzerLoader
    {
        List<ProtocolAnalyzerBase> loadedAnalyzers = new List<ProtocolAnalyzerBase>();

        public string[] ProtocolNames { get { return loadedAnalyzers.Select(a => a.ProtocolName).ToArray(); } }

        public ProtocolAnalyzerBase? GetAnalyzer(string ProtocolName)
        {
            return loadedAnalyzers.FirstOrDefault(a => a.ProtocolName == ProtocolName);
        }

        public ProtocolAnalyzerLoader(string ProtocolStoragePath)
        {
            if (!Directory.Exists(ProtocolStoragePath))
                return;

            var libraries = Directory.GetFiles(ProtocolStoragePath, "*.dll");
            var baseType = typeof(ProtocolAnalyzerBase);

            foreach (var library in libraries)
            {
                var assembly = Assembly.LoadFile(library);
                var analyzerTypes = assembly.GetTypes().Where(t => baseType.IsAssignableFrom(t)).ToArray();

                foreach (var type in analyzerTypes)
                {
                    var analyzer = Activator.CreateInstance(type);
                    loadedAnalyzers.Add((ProtocolAnalyzerBase)analyzer);
                }
            }
        }
    }
}
