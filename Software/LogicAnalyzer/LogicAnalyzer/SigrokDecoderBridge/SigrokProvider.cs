using LogicAnalyzer.Classes;
using LogicAnalyzer.Controls;
using Microsoft.CodeAnalysis;
using Microsoft.CodeAnalysis.CSharp;
using System;
using System.Collections.Generic;
using System.Diagnostics;
using System.IO;
using System.Linq;
using System.Reflection;
using System.Text.RegularExpressions;

namespace SigrokDecoderBridge
{
    public class SigrokProvider : IDisposable
    {
        
        private Dictionary<string, IEnumerable<SigrokOutputValue>> sessionOutputs = new Dictionary<string, IEnumerable<SigrokOutputValue>>();

        private SigrokDecoderBase[]? decoders;

        public SigrokDecoderBase[] Decoders 
        {
            get 
            {
                if (decoders == null)
                    decoders = GetDecoders();

                return decoders;
            }
        }

        Dictionary<string, Dictionary<int, SigrokOptionValue>> decoderOptions = new Dictionary<string, Dictionary<int, SigrokOptionValue>>();
        Dictionary<string, Dictionary<int, SigrokSelectedChannel>> decoderChannels = new Dictionary<string, Dictionary<int, SigrokSelectedChannel>>();

        List<SigrokDecoderBase> activeDecoders = new List<SigrokDecoderBase>();

        public IEnumerable<SigrokDecoderBase> ActiveDecoders => activeDecoders;

        public void AddDecoder(SigrokDecoderBase Decoder)
        {
            activeDecoders.Add(Decoder);
            decoderOptions[Decoder.Id] = new Dictionary<int, SigrokOptionValue>();
            decoderChannels[Decoder.Id] = new Dictionary<int, SigrokSelectedChannel>();
        }
        public void SetDecoderOptionValue(string DecoderId, SigrokOptionValue Value)
        {
            if (!decoderOptions.ContainsKey(DecoderId))
                return;

            decoderOptions[DecoderId][Value.OptionIndex] = Value;
        }
        public void SetDecoderSelectedChannel(string DecoderId, SigrokSelectedChannel Channel)
        {
            if (!decoderChannels.ContainsKey(DecoderId))
                return;

            decoderChannels[DecoderId][Channel.SigrokIndex] = Channel;
        }

        private SigrokDecoderBase[] GetDecoders()
        {
            List<string> classTemplates = new List<string>();
            
            var dirs = Directory.GetDirectories(SigrokPythonEngine.DecoderPath);

            foreach (var dir in dirs)
            {
                if ((Directory.GetFiles(dir, "pd.py")?.Length ?? 0) > 0)
                {
                    string decoderCode = string.Format(CodeTemplates.DecoderTemplate, Regex.Replace(Path.GetFileNameWithoutExtension(dir), "[^a-zA-Z0-9_]+", ""), Path.GetFileNameWithoutExtension(dir));
                    classTemplates.Add(decoderCode);
                }
            }

            string moduleCode = string.Format(CodeTemplates.ModuleTemplate, string.Join("\r\n", classTemplates));

            var options = CSharpParseOptions.Default.WithLanguageVersion(LanguageVersion.Latest);

            var parsedSyntaxTree = SyntaxFactory.ParseSyntaxTree(moduleCode, options);

            var assemblyPath = Path.GetDirectoryName(typeof(object).Assembly.Location);

            var references = new MetadataReference[]
            {
                MetadataReference.CreateFromFile(typeof(object).Assembly.Location),
                MetadataReference.CreateFromFile(typeof(Object).Assembly.Location),
                MetadataReference.CreateFromFile(typeof(Console).Assembly.Location),
                MetadataReference.CreateFromFile(typeof(System.Runtime.AssemblyTargetedPatchBandAttribute).Assembly.Location),
                MetadataReference.CreateFromFile(typeof(Microsoft.CSharp.RuntimeBinder.CSharpArgumentInfo).Assembly.Location),
                MetadataReference.CreateFromFile(typeof(SigrokProvider).Assembly.Location),
                MetadataReference.CreateFromFile(typeof(SigrokDecoderBase).Assembly.Location),
                MetadataReference.CreateFromFile(Path.Combine(assemblyPath, "mscorlib.dll")),
                MetadataReference.CreateFromFile(Path.Combine(assemblyPath, "System.dll")),
                MetadataReference.CreateFromFile(Path.Combine(assemblyPath, "System.Core.dll")),
                MetadataReference.CreateFromFile(Path.Combine(assemblyPath, "System.Runtime.dll")),
            };

            var compilation = CSharpCompilation.Create("Analyzers.dll",
                new[] { parsedSyntaxTree },
                references: references,
                options: new CSharpCompilationOptions(OutputKind.DynamicallyLinkedLibrary,
                    optimizationLevel: OptimizationLevel.Release,
                    assemblyIdentityComparer: DesktopAssemblyIdentityComparer.Default));

            MemoryStream ms = new MemoryStream();

            var result = compilation.Emit(ms);

            if (!result.Success)
                throw new InvalidDataException();

            ms.Seek(0, SeekOrigin.Begin);

            var assembly = Assembly.Load(ms.ToArray());
            var types = assembly.GetTypes();

            List<SigrokDecoderBase> loadedAnalyzers = new List<SigrokDecoderBase>();

            foreach (var type in types)
            {
                try
                {
                    var analyzer = Activator.CreateInstance(type) as SigrokDecoderBase;

                    if (analyzer != null)// && analyzer.IsBaseAnalyzer)
                    {
                        analyzer.provider = this;
                        loadedAnalyzers.Add(analyzer);
                    }
                    else
                        analyzer?.Dispose();
                }
                catch { }
            }

            return loadedAnalyzers.ToArray();
        }

        public SigrokProvider()
        {
            if(!SigrokPythonEngine.EnsureInitialized())
                throw new Exception("Python engine could not be initialized");
        }

        public SigrokDecoderBase? GetDecoder(string DecoderName)
        {
            return Decoders.FirstOrDefault(t => t.DecoderName == DecoderName);
        }

        internal IEnumerable<SigrokOutputValue>? GetInput(string OutputName)
        { 
            if(!sessionOutputs.ContainsKey(OutputName))
                return null;

            return sessionOutputs[OutputName];
        }

        internal void AddOutput(string OutputName, IEnumerable<SigrokOutputValue> Output)
        {
            sessionOutputs[OutputName] = Output;
        }

        public Dictionary<string,SigrokAnnotation[]>? Execute(int SampleRate, CaptureChannel[]? Channels)
        {
            if(activeDecoders.Count == 0 || Channels == null)
                return null;

            Dictionary<string, SigrokAnnotation[]> annotations = new Dictionary<string, SigrokAnnotation[]>();

            var sorted = activeDecoders.TSort<SigrokDecoderBase>((a) => FindDependencies(a), true);

            foreach (var decoder in sorted)
            {
                var decOpts = decoderOptions.ContainsKey(decoder.Id) ? decoderOptions[decoder.Id].Values.ToArray() : null;
                var decChans = decoderChannels.ContainsKey(decoder.Id) ? decoderChannels[decoder.Id].Values.ToArray() : null;

                if(decChans == null || decOpts == null)
                    continue;

                if (!decoder.ValidateOptions(decOpts, decChans, Channels))
                    continue;

                var result = decoder.ExecuteAnalysis(SampleRate, decOpts, decChans, Channels);

                if (result != null)
                    annotations[decoder.Id] = result;
            }

            return annotations;
        }

        public IEnumerable<SigrokDecoderBase> FindDependencies(SigrokDecoderBase source)
        {
            List<SigrokDecoderBase> dependencies = new List<SigrokDecoderBase>();

            foreach (var dep in source.Inputs)
            {
                if (dep == "logic")
                    continue;

                dependencies.AddRange(activeDecoders.Where(t => t.Outputs.Contains(dep)));
            }

            return dependencies;
        }

        public void BeginSession()
        {
            activeDecoders.Clear();
            sessionOutputs.Clear();
            decoderOptions.Clear();
            decoderChannels.Clear();
        }

        public void EndSession()
        {
            activeDecoders.Clear();
            sessionOutputs.Clear();
            decoderOptions.Clear();
            decoderChannels.Clear();
        }

        public void Dispose()
        {
            AppContext.SetSwitch("System.Runtime.Serialization.EnableUnsafeBinaryFormatterSerialization", true);
            SigrokPythonEngine.EnsureDestroyed();
            AppContext.SetSwitch("System.Runtime.Serialization.EnableUnsafeBinaryFormatterSerialization", false);
        }
    }
}
