using LogicAnalyzer.Protocols;
using Newtonsoft.Json;
using Python.Runtime;
using System;
using System.Collections.Generic;
using System.Diagnostics;
using System.Globalization;
using System.Linq;
using System.Text;
using System.Threading.Tasks;
using static LogicAnalyzer.Protocols.ProtocolAnalyzerSetting;
using static System.Formats.Asn1.AsnWriter;
using static System.Runtime.InteropServices.JavaScript.JSType;

namespace SigrokDecoderBridge
{
    public abstract class SigrokDecoderBase : ProtocolAnalyzerBase
    {
        PyModule thisModule;
        PyObject decoderObject;
        dynamic decoder;

        List<SigrokSignal> signals;
        List<SigrokOption> settings;
        List<RegisteredOutput> registeredOutputs = new List<RegisteredOutput>();

        List<string> categories = new List<string>();

        public override string[] Categories
        {
            get
            {
                return categories.ToArray();
            }
        }

        const int SRD_CONF_SAMPLERATE = 0;

        long currentSample = -1;
        long sampleCount = 0;

        Dictionary<int, ProtocolAnalyzerSelectedChannel> indexedChannels = new Dictionary<int, ProtocolAnalyzerSelectedChannel>();

        Dictionary<int, int> currentState = new Dictionary<int, int>();

        protected abstract string decoderName { get; }

        public override ProtocolAnalyzerType AnalyzerType
        {
            get
            {
                return ProtocolAnalyzerType.AnnotationAnalyzer;
            }
        }

        public override string ProtocolName
        {
            get
            {
                return decoder.longname;
            }
        }

        public bool IsBaseAnalyzer { get { return decoder.inputs[0] == "logic"; } }

        internal SigrokProvider provider;

        public string[] Inputs 
        { 
            get
            {
                using (Py.GIL())
                {
                    List<string> inputs = new List<string>();
                    foreach (string input in decoder.inputs)
                    {
                        inputs.Add(input);
                    }
                    return inputs.ToArray();
                }
            }
            
        }

        public string[] Outputs
        {
            get
            {
                using (Py.GIL())
                {
                    List<string> outputs = new List<string>();
                    foreach (string output in decoder.outputs)
                    {
                        outputs.Add(output);
                    }
                    return outputs.ToArray();
                }
            }
        }

        public override ProtocolAnalyzerSignal[] Signals
        {
            get
            {
                return signals.ToArray();
            }
        }

        public override ProtocolAnalyzerSetting[] Settings
        {
            get
            {
                return settings?.ToArray() ?? new ProtocolAnalyzerSetting[0];
            }
        }


        public SigrokDecoderBase()
        {
            using (Py.GIL())
            {
                //Create module scope
                thisModule = Py.CreateScope(decoderName + "_bridge");

                //Import the decoder and store reference
                thisModule.Exec($"import {decoderName}");
                decoder = thisModule.Eval($"{decoderName}.Decoder()");
                decoder.cObj = this.ToPython();
                decoderObject = decoder;

                InitializeCategories();
                InitializeSignals();
                InitializeOptions();
            }
        }

        private void InitializeSignals()
        {
            using (Py.GIL())
            {
                signals = new List<SigrokSignal>();

                dynamic requiredSignals = decoder.channels;

                foreach (dynamic signal in requiredSignals)
                {
                    signals.Add(new SigrokSignal
                    {
                        SignalName = signal["name"],
                        Required = true,
                        Id = signal["id"],
                        Name = signal["name"],
                        Desc = signal["desc"],
                        Index = signals.Count
                    });

                }

                dynamic optionalSignals = decoder.optional_channels;

                foreach (dynamic signal in optionalSignals)
                {
                    signals.Add(new SigrokSignal
                    {
                        SignalName = signal["name"],
                        Required = false,
                        Id = signal["id"],
                        Name = signal["name"],
                        Desc = signal["desc"],
                        Index = signals.Count
                    });
                }
            }
        }

        private void InitializeOptions()
        {
            using (Py.GIL())
            {
                settings = new List<SigrokOption>();

                dynamic options = decoder.options;

                if (options == null)
                {
                    return;
                }

                foreach (dynamic option in options)
                {

                    string[] keys = SigrokPythonEngine.GetKeys(option);

                    var opt = new SigrokOption
                    {
                        Id = option["id"],
                        Caption = option["desc"]
                    };

                    if (keys.Contains("default"))
                    {
                        opt.Default = option["default"];
                        opt.SigrokType = opt.Default.GetPythonType();
                    }
                    else
                    {
                        opt.SigrokType = ("").ToPython().GetPythonType();
                        opt.SettingType = ProtocolAnalyzerSettingType.String;
                    }

                    if (keys.Contains("values"))
                        opt.Values = SigrokPythonEngine.GetKeys(option["values"]);



                    if (opt.Values != null)
                    {
                        var list = opt.Values.Select(o => o.ToString()).ToArray();
                        opt.ListValues = list;
                        opt.SettingType = ProtocolAnalyzerSettingType.List;
                        opt.SigrokType = opt.Default.GetPythonType();
                        opt.DefaultValue = opt.Default.ToString();
                    }
                    else
                    {
                        if (opt.Default != null)
                        {
                            switch (opt.Default.GetPythonType().Name)
                            {
                                case "str":
                                    opt.SettingType = ProtocolAnalyzerSettingType.String;
                                    opt.DefaultValue = opt.Default.AsManagedObject(typeof(string));
                                    break;
                                case "int":
                                    opt.MinimumValue = int.MinValue;
                                    opt.MaximumValue = int.MaxValue;
                                    opt.SettingType = ProtocolAnalyzerSettingType.Integer;
                                    opt.DefaultValue = opt.Default.AsManagedObject(typeof(int));
                                    break;
                                case "float":
                                    opt.MinimumValue = (double)int.MinValue;
                                    opt.MaximumValue = (double)int.MaxValue;
                                    opt.SettingType = ProtocolAnalyzerSettingType.Double;
                                    opt.DefaultValue = opt.Default.AsManagedObject(typeof(double));
                                    break;
                                case "bool":
                                    opt.SettingType = ProtocolAnalyzerSettingType.Boolean;
                                    opt.DefaultValue = opt.Default.AsManagedObject(typeof(bool));
                                    break;
                                default:
                                    throw new Exception();
                            }
                        }
                    }

                    settings.Add(opt);
                }
            }
        }

        private void InitializeCategories()
        {
            using (Py.GIL())
            {
                dynamic categories = decoder.tags;

                if (categories == null)
                    return;

                foreach (dynamic category in categories)
                {
                    this.categories.Add((category as PyObject).ToString());
                }
            }
        }

        public override bool ValidateSettings(ProtocolAnalyzerSettingValue[] SelectedSettings, ProtocolAnalyzerSelectedChannel[] SelectedChannels)
        {
            foreach (var selSet in SelectedSettings)
            {
                var setting = settings[selSet.SettingIndex];

                if (selSet.Value == null)
                    return false;


                switch (setting.SettingType)
                {
                    case ProtocolAnalyzerSettingType.Boolean:
                        var bVal = selSet.Value as bool?;
                        if (bVal == null)
                            return false;
                        break;
                    case ProtocolAnalyzerSettingType.Double:
                        var dVal = selSet.Value as double?;
                        if (dVal == null)
                            return false;
                        break;
                    case ProtocolAnalyzerSettingType.Integer:
                        var iVal = selSet.Value as int?;
                        if (iVal == null)
                            return false;
                        break;
                    case ProtocolAnalyzerSettingType.List:
                        var lVal = selSet.Value as string;

                        if (lVal == null)
                            return false;

                        if (!setting.Values.Contains(lVal))
                            return false;

                        break;
                    case ProtocolAnalyzerSettingType.String:
                        var sVal = selSet.Value as string;

                        if (sVal == null)
                            return false;
                        break;
                }
            }

            var req = signals.Where(s => s.Required);
            foreach (var reqSig in req)
            {
                if (!SelectedChannels.Any(c => c.SignalName == reqSig.SignalName))
                    return false;
            }

            return true;
        }

        public override ProtocolAnalyzedAnnotation[] AnalyzeAnnotations(int SamplingRate, int TriggerSample, ProtocolAnalyzerSettingValue[] SelectedSettings, ProtocolAnalyzerSelectedChannel[] SelectedChannels)
        {
            using (Py.GIL())
            {
                if (SelectedSettings != null && SelectedSettings.Length > 0)
                {
                    Dictionary<string, PyObject> newSettings = new Dictionary<string, PyObject>();

                    foreach (var value in SelectedSettings)
                    {
                        var setting = settings[value.SettingIndex];

                        switch (setting.SigrokType.Name)
                        {
                            case "str":
                                newSettings[setting.Id] = value.Value.ToString().ToPython();
                                break;
                            case "int":
                                newSettings[setting.Id] = int.Parse(value.Value.ToString(), CultureInfo.InvariantCulture).ToPython();
                                break;
                            case "float":
                                newSettings[setting.Id] = double.Parse(value.Value.ToString(), CultureInfo.InvariantCulture).ToPython();
                                break;
                            case "bool":
                                newSettings[setting.Id] = bool.Parse(value.Value.ToString()).ToPython();
                                break;
                        }
                    }

                    decoder.options = CreateDictionary(newSettings);
                }

                currentState.Clear();
                indexedChannels.Clear();

                for (int buc = 0; buc < signals.Count; buc++)
                {
                    var channel = SelectedChannels.Where(c => c.SignalName == signals[buc].SignalName).FirstOrDefault();
                    if (channel != null)
                    {
                        currentState[buc] = -1;
                        indexedChannels[buc] = channel;
                    }
                }

                sampleCount = SelectedChannels == null || 
                    SelectedChannels.Length == 0 ? 
                    0 : SelectedChannels[0].Samples.LongLength;

                currentSample = -1;
                registeredOutputs.Clear();

                decoder.start();
                decoder.reset();

                //Initialize metadata (if needed)
                if (decoderObject.HasAttr("metadata"))
                    decoder.metadata(SRD_CONF_SAMPLERATE, SamplingRate);

                foreach (var input in Inputs)
                {
                    switch (input)
                    {
                        case "logic":
                            try
                            {
                                decoder.decode();
                            }
                            catch { }
                            break;

                        default:

                            var inputValues = provider.GetInput(input);

                            if (inputValues != null)
                            {
                                foreach (var inputVal in inputValues)
                                {
                                    decoder.decode(inputVal.StartSample, inputVal.EndSample, inputVal.Value);
                                }

                            }
                            break;
                    }
                }

                GenerateOutputs();

                return GenerateAnnotations();
            }
        }

        private void GenerateOutputs()
        {
            var outputs = Outputs;

            if(outputs == null || outputs.Length == 0)
                return;
            
            var registeredOutputs = this.registeredOutputs.Where(t => t.OutputType == AnnotationOutputType.OUTPUT_PYTHON).OrderBy(o => o.OutputId).ToArray();

            for (int buc = 0; buc < outputs.Length; buc++)
            {
                provider.AddOutput(outputs[buc], registeredOutputs[buc].Outputs);
            }
        }

        private PyDict CreateDictionary(Dictionary<string, PyObject> newSettings)
        {
            PyDict dict = new PyDict();
            foreach (var pair in newSettings)
            {
                dict[pair.Key] = pair.Value;
            }

            return dict;
        }

        private ProtocolAnalyzedAnnotation[] GenerateAnnotations()
        {

            AnnotationRow[] annRows = GetAnnotationRows();

            Dictionary<int, List<ProtocolAnalyzedAnnotationSegment>> segments = new Dictionary<int, List<ProtocolAnalyzedAnnotationSegment>>();

            Dictionary<int, List<List<ProtocolAnalyzedAnnotationSegment>>>
                segmentsPerRow = new Dictionary<int, List<List<ProtocolAnalyzedAnnotationSegment>>>();

            List<ProtocolAnalyzedAnnotation> annotations = new List<ProtocolAnalyzedAnnotation>();

            for (int buc = 0; buc < registeredOutputs.Count; buc++)
            {
                var output = registeredOutputs[buc];

                if (output.OutputType != AnnotationOutputType.OUTPUT_ANN)
                    continue;

                if (output.Outputs.Count == 0)
                    continue;

                foreach (var outVal in output.Outputs)
                {
                    int annId = (int)((PyObject)outVal.Value[0]).AsManagedObject(typeof(int));

                    var segment = new ProtocolAnalyzedAnnotationSegment
                    {
                        TypeId = annId,
                        Shape = ProtocolAnalyzerSegmentShape.Hexagon,
                        FirstSample = outVal.StartSample,
                        LastSample = outVal.EndSample,
                        Value = GetAnnotationValues(outVal.Value)
                    };

                    if (!segments.ContainsKey(annId))
                        segments[annId] = new List<ProtocolAnalyzedAnnotationSegment>();

                    var segList = segments[annId];
                    segList.Add(segment);
                }
            }

            var keys = segments.Keys.Distinct().OrderBy(k => k).ToArray();

            foreach (var key in keys)
            {
                var row = annRows.Where(row => row.Types.Any(t => t.Index == key)).First();

                if (!segmentsPerRow.ContainsKey(row.Index))
                    segmentsPerRow[row.Index] = new List<List<ProtocolAnalyzedAnnotationSegment>>();

                segmentsPerRow[row.Index].Add(segments[key]);
            }

            foreach (var pair in segmentsPerRow)
            {
                var row = annRows.Where(row => row.Index == pair.Key).First();

                var annotation = new ProtocolAnalyzedAnnotation
                {
                    AnnotationName = row.Name,
                    Segments = pair.Value.SelectMany(s => s).OrderBy(s => s.FirstSample).ToArray()
                };

                annotations.Add(annotation);
            }

            return annotations.ToArray();
        }

        private string[] GetAnnotationValues(dynamic outVal)
        {
            List<string> values = new List<string>();

            foreach (dynamic val in outVal[1])
                values.Add(val.ToString());

            return values.ToArray();
        }

        private AnnotationRow[] GetAnnotationRows()
        {
            List<AnnotationRow> annotations = new List<AnnotationRow>();

            using (Py.GIL())
            {
                var rows = decoder.annotation_rows;
                var anns = decoder.annotations;

                int rowIndex = 0;

                foreach (dynamic row in rows)
                {
                    var annRow = new AnnotationRow
                    {
                        Index = rowIndex++,
                        Id = row[0],
                        Name = row[1]
                    };

                    var typeIndexes = row[2];

                    List<AnnotationType> types = new List<AnnotationType>();

                    foreach (dynamic index in typeIndexes)
                    {
                        dynamic type = anns[index];
                        types.Add(new AnnotationType
                        {
                            Index = index,
                            Id = type[0],
                            Name = type[1]
                        });
                    }

                    annRow.Types = types.ToArray();

                    annotations.Add(annRow);

                }


                List<AnnotationType> anonTypes = new List<AnnotationType>();

                int idx = 0;

                foreach (dynamic type in anns)
                {

                    if (!annotations.Any(a => a.Types.Any(t => t.Id ==((PyObject) type[0]).ToString())))
                    {
                        anonTypes.Add(new AnnotationType
                        {
                            Index = idx++,
                            Id = type[0],
                            Name = type[1]
                        });
                    }
                    else
                        idx++;
                }

                if (anonTypes.Count > 0)
                {
                    annotations.Add(new AnnotationRow
                    {
                        Index = 0,
                        Id = decoder.id,
                        Name = decoder.name,
                        Types = anonTypes.ToArray()
                    });
                }
            }

            return annotations.ToArray();
        }

        public override void Dispose()
        {
            signals?.Clear();
            settings?.Clear();
            registeredOutputs?.Clear();
            decoderObject.Dispose();
            thisModule.Dispose();
            base.Dispose();
        }

        #region Bridge functions

        public bool HasChannel(int channel)
        {
            return indexedChannels.ContainsKey(channel);
        }

        public PyTuple? Wait(dynamic? conditions)
        {

            List<WaitCondition> cnd = new List<WaitCondition>();

            using (Py.GIL())
            {
                if (conditions == null)
                {
                    var nCond = new WaitCondition();
                    nCond.AddParameter(new WaitConditionParameter
                    {
                        Channel = 1,
                        ConditionType = WaitConditionType.Skip
                    });

                    cnd.Add(nCond);
                }
                else
                {
                    if (PyList.IsListType(conditions))
                    {
                        foreach (dynamic condition in conditions)
                        {
                            cnd.Add(GetCondition(condition));
                        }
                    }
                    else if (PyDict.IsDictType(conditions))
                    {
                        cnd.Add(GetCondition(conditions));
                    }
                }

                while (true)
                {
                    currentSample++;

                    if (currentSample >= sampleCount)
                        return null;

                    foreach (var condition in cnd)
                        condition.Tick();

                    var newState = CreateCurrentState();

                    PyTuple output;

                    var match = CheckConditions(currentState, newState, cnd, out output);

                    currentState = newState;

                    if (match)
                    {
                        decoder.matched = output;
                        decoder.samplenum = currentSample;
                        return CreateTuple(currentState);
                    }
                }

            }
        }

        private PyTuple? CreateTuple(Dictionary<int, int> currentState)
        {
            List<PyObject> inputs = new List<PyObject>();

            for (int buc = 0; buc < signals.Count; buc++)
            {
                if (currentState.ContainsKey(buc))
                {
                    inputs.Add(currentState[buc].ToPython());
                }
                else
                {
                    inputs.Add((0xFF).ToPython());
                }
            }

            PyTuple tuple = new PyTuple(inputs.ToArray());

            return tuple;
        }

        private bool CheckConditions(Dictionary<int, int> currentState, Dictionary<int, int> newState, List<WaitCondition> cnd, out PyTuple? Output)
        {
            Output = null;

            bool[] matches = cnd.Select(c => c.Matched(currentState, newState)).ToArray();

            if (matches.Any(b => b))
            {
                Output = PyTuple.AsTuple(matches.ToPython());
                return true;
            }

            return false;
        }

        Dictionary<int, int> CreateCurrentState()
        {
            Dictionary<int, int> state = new Dictionary<int, int>();

            foreach (var channelIndex in indexedChannels.Keys)
            {
                state[channelIndex] = indexedChannels[channelIndex].Samples[currentSample];
            }

            return state;
        }

        private WaitCondition GetCondition(dynamic condition)
        {
            WaitCondition cond = new WaitCondition();

            var keys = (string[])SigrokPythonEngine.GetKeys(condition.keys());
            var values = (string[])SigrokPythonEngine.GetKeys(condition.values());

            for (int buc = 0; buc < keys.Length; buc++)
            {
                string key = keys[buc];
                string val = values[buc];
                WaitConditionParameter param;

                if (key == null || val == null)
                {
                    param = new WaitConditionParameter
                    {
                        Channel = 1,
                        ConditionType = WaitConditionType.Skip
                    };
                }
                else
                {
                    if (key == "skip")
                    {
                        param = new WaitConditionParameter
                        {
                            Channel = int.Parse(val),
                            ConditionType = WaitConditionType.Skip
                        };
                    }
                    else
                    {
                        param = new WaitConditionParameter
                        {
                            Channel = int.Parse(key)
                        };

                        switch (val)
                        {
                            case "l":
                                param.ConditionType = WaitConditionType.Low;
                                break;
                            case "h":
                                param.ConditionType = WaitConditionType.High;
                                break;
                            case "r":
                                param.ConditionType = WaitConditionType.Rising;
                                break;
                            case "f":
                                param.ConditionType = WaitConditionType.Falling;
                                break;
                            case "e":
                                param.ConditionType = WaitConditionType.Edge;
                                break;
                            case "s":
                                param.ConditionType = WaitConditionType.Stable;
                                break;
                            default:
                                param.ConditionType = WaitConditionType.Skip;
                                break;
                        }
                    }
                }

                cond.AddParameter(param);
            }

            return cond;
        }

        public int Register(int outputType, dynamic metadataDefinition)
        {
            using (Py.GIL())
            {
                var output = new RegisteredOutput
                {
                    OutputType = (AnnotationOutputType)outputType,
                    MetadataDefinition = metadataDefinition,
                    OutputId = registeredOutputs.Count
                };

                registeredOutputs.Add(output);

                return output.OutputId;
            }
        }

        public void Put(int startSample, int endSample, int outputId, dynamic data)
        {
            using (Py.GIL())
            {
                registeredOutputs[outputId].Outputs.Add(new SigrokOutputValue { StartSample = startSample, EndSample = endSample, Value = data });
            }
        }

        #endregion

        #region Internal classes
        class SigrokSignal : ProtocolAnalyzerSignal
        {
            public string Id { get; set; }
            public string Name { get; set; }
            public string Desc { get; set; }
            public required int Index { get; set; }
        }

        class SigrokOption : ProtocolAnalyzerSetting
        {
            public string Id { get; set; }
            public PyObject Default { get; set; }
            public string[] Values { get; set; }
            public PyType SigrokType { get; set; }
        }

        class RegisteredOutput
        {
            public AnnotationOutputType OutputType { get; set; }
            public dynamic? MetadataDefinition { get; set; }
            public int OutputId { get; set; }
            public List<SigrokOutputValue> Outputs { get; set; } = new List<SigrokOutputValue>();
        }

        class WaitCondition
        {
            List<WaitConditionParameter> parameters = new List<WaitConditionParameter>();

            public void AddParameter(WaitConditionParameter parameter)
            {
                parameters.Add(parameter);
            }

            public void Tick()
            {
                foreach (var parameter in parameters)
                    parameter.Tick();
            }

            public bool Matched(Dictionary<int, int> currentState, Dictionary<int, int> newState)
            {
                return parameters.All(parameters => parameters.Matched(currentState, newState));
            }
        }

        class WaitConditionParameter
        {

            public int Channel { get; set; }
            public WaitConditionType ConditionType { get; set; }

            public void Tick()
            {
                if (ConditionType == WaitConditionType.Skip && Channel > 0)
                    Channel--;
            }

            public bool Matched(Dictionary<int, int> currentState, Dictionary<int, int> newState)
            {
                if (ConditionType == WaitConditionType.Skip)
                    return Channel == 0;

                if (!currentState.ContainsKey(Channel) || !newState.ContainsKey(Channel))
                    return false;

                switch (ConditionType)
                {
                    case WaitConditionType.Low:
                        return newState[Channel] == 0;
                    case WaitConditionType.High:
                        return newState[Channel] == 1;
                    case WaitConditionType.Rising:
                        return currentState[Channel] == 0 && newState[Channel] == 1;
                    case WaitConditionType.Falling:
                        return currentState[Channel] == 1 && newState[Channel] == 0;
                    case WaitConditionType.Edge:
                        return currentState[Channel] != newState[Channel];
                    case WaitConditionType.Stable:
                        return currentState[Channel] == newState[Channel];
                    default:
                        return false;
                }
            }
        }

        enum WaitConditionType
        {
            Skip,
            Low,
            High,
            Rising,
            Falling,
            Edge,
            Stable
        }

        enum AnnotationOutputType
        {
            OUTPUT_ANN = 0,
            OUTPUT_PYTHON = 1,
            OUTPUT_BINARY = 2,
            OUTPUT_LOGIC = 3,
            OUTPUT_META = 4
        }

        class AnnotationRow
        {
            public int Index { get; set; }
            public string Id { get; set; }
            public string Name { get; set; }
            public AnnotationType[] Types { get; set; }
        }

        class AnnotationType
        {
            public int Index { get; set; }
            public string Id { get; set; }
            public string Name { get; set; }
        }

        #endregion
    }
}
