using Python.Runtime;
using System;
using System.Collections.Generic;
using System.Diagnostics;
using System.Globalization;

namespace SigrokDecoderBridge
{
    public abstract class SigrokDecoderBase : IDisposable
    {
        PyModule thisModule;
        PyObject decoderObject;
        dynamic decoder;

        List<SigrokChannel> channels;
        List<SigrokOption> settings;
        List<RegisteredOutput> registeredOutputs = new List<RegisteredOutput>();

        List<string> categories = new List<string>();

        public string[] Categories
        {
            get
            {
                return categories.ToArray();
            }
        }

        const int SRD_CONF_SAMPLERATE = 0;

        long currentSample = -1;
        long sampleCount = 0;

        Dictionary<int, SigrokSelectedChannel> indexedChannels = new Dictionary<int, SigrokSelectedChannel>();

        Dictionary<int, int> currentState = new Dictionary<int, int>();
        Dictionary<int, int> lastState = new Dictionary<int, int>();
        protected abstract string decoderName { get; }

        public string Id 
        {
            get
            {
                return decoder.id;
            }
        }

        public string DecoderName
        {
            get
            {
                return decoder.longname;
            }
        }

        public string DecoderShortName
        {
            get
            {
                return decoder.name;
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

        public SigrokChannel[] Channels
        {
            get
            {
                return channels.ToArray();
            }
        }

        public SigrokOption[] Options
        {
            get
            {
                return settings?.ToArray() ?? new SigrokOption[0];
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
                channels = new List<SigrokChannel>();

                dynamic requiredSignals = decoder.channels;

                foreach (dynamic signal in requiredSignals)
                {
                    channels.Add(new SigrokChannel
                    {
                        Required = true,
                        Id = signal["id"],
                        Name = signal["name"],
                        Description = signal["desc"],
                        Index = channels.Count
                    });

                }

                dynamic optionalSignals = decoder.optional_channels;

                foreach (dynamic signal in optionalSignals)
                {
                    channels.Add(new SigrokChannel
                    {
                        Required = false,
                        Id = signal["id"],
                        Name = signal["name"],
                        Description = signal["desc"],
                        Index = channels.Count
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

                    string[] keys = GetKeys(option);

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
                        opt.OptionType = SigrokOptionType.String;
                    }

                    if (keys.Contains("values"))
                        opt.Values = GetKeys(option["values"]);



                    if (opt.Values != null)
                    {
                        var list = opt.Values.Select(o => o.ToString()).ToArray();
                        opt.ListValues = list;
                        opt.OptionType = SigrokOptionType.List;
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
                                    opt.OptionType = SigrokOptionType.String;
                                    opt.DefaultValue = opt.Default.AsManagedObject(typeof(string));
                                    break;
                                case "int":
                                    opt.MinimumValue = int.MinValue;
                                    opt.MaximumValue = int.MaxValue;
                                    opt.OptionType = SigrokOptionType.Integer;
                                    opt.DefaultValue = opt.Default.AsManagedObject(typeof(int));
                                    break;
                                case "float":
                                    opt.MinimumValue = (double)int.MinValue;
                                    opt.MaximumValue = (double)int.MaxValue;
                                    opt.OptionType = SigrokOptionType.Double;
                                    opt.DefaultValue = opt.Default.AsManagedObject(typeof(double));
                                    break;
                                case "bool":
                                    opt.OptionType = SigrokOptionType.Boolean;
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

        public bool ValidateOptions(SigrokOptionValue[] SelectedSettings, SigrokSelectedChannel[] SelectedChannels)
        {
            foreach (var selSet in SelectedSettings)
            {
                var setting = settings[selSet.OptionIndex];

                if (selSet.Value == null)
                    return false;


                switch (setting.OptionType)
                {
                    case SigrokOptionType.Boolean:
                        var bVal = selSet.Value as bool?;
                        if (bVal == null)
                            return false;
                        break;
                    case SigrokOptionType.Double:
                        var dVal = selSet.Value as double?;
                        if (dVal == null)
                            return false;
                        break;
                    case SigrokOptionType.Integer:
                        var iVal = selSet.Value as int?;
                        if (iVal == null)
                            return false;
                        break;
                    case SigrokOptionType.List:
                        var lVal = selSet.Value as string;

                        if (lVal == null)
                            return false;

                        if (!setting.Values.Contains(lVal))
                            return false;

                        break;
                    case SigrokOptionType.String:
                        var sVal = selSet.Value as string;

                        if (sVal == null)
                            return false;
                        break;
                }
            }

            var req = channels.Where(s => s.Required);
            foreach (var reqSig in req)
            {
                if (!SelectedChannels.Any(c => c.ChannelName == reqSig.Name))
                    return false;
            }

            return true;
        }

        public SigrokAnnotation[] ExecuteAnalysis(int SamplingRate, int TriggerSample, SigrokOptionValue[] SelectedSettings, SigrokSelectedChannel[] SelectedChannels)
        {
            using (Py.GIL())
            {
                if (SelectedSettings != null && SelectedSettings.Length > 0)
                {
                    Dictionary<string, PyObject> newSettings = new Dictionary<string, PyObject>();

                    foreach (var value in SelectedSettings)
                    {
                        var setting = settings[value.OptionIndex];

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

                for (int buc = 0; buc < channels.Count; buc++)
                {
                    var channel = SelectedChannels.Where(c => c.ChannelName == channels[buc].Name).FirstOrDefault();
                    if (channel != null)
                    {
                        currentState[buc] = channel.Samples[0];
                        lastState[buc] = channel.Samples[0];
                        lastState[buc] = -1;
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

                var ann = GenerateAnnotations();

                currentState.Clear();
                indexedChannels.Clear();

                return ann;
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

        private SigrokAnnotation[] GenerateAnnotations()
        {

            AnnotationRow[] annRows = GetAnnotationRows();

            Dictionary<int, List<SigrokAnnotationSegment>> segments = new Dictionary<int, List<SigrokAnnotationSegment>>();

            Dictionary<int, List<List<SigrokAnnotationSegment>>>
                segmentsPerRow = new Dictionary<int, List<List<SigrokAnnotationSegment>>>();

            List<SigrokAnnotation> annotations = new List<SigrokAnnotation>();

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

                    var segment = new SigrokAnnotationSegment
                    {
                        TypeId = annId,
                        Shape = ProtocolAnalyzerSegmentShape.Hexagon,
                        FirstSample = outVal.StartSample,
                        LastSample = outVal.EndSample,
                        Value = GetAnnotationValues(outVal.Value)
                    };

                    if (!segments.ContainsKey(annId))
                        segments[annId] = new List<SigrokAnnotationSegment>();

                    var segList = segments[annId];
                    segList.Add(segment);
                }
            }

            var keys = segments.Keys.Distinct().OrderBy(k => k).ToArray();

            foreach (var key in keys)
            {
                var row = annRows.Where(row => row.Types.Any(t => t.Index == key)).First();

                if (!segmentsPerRow.ContainsKey(row.Index))
                    segmentsPerRow[row.Index] = new List<List<SigrokAnnotationSegment>>();

                segmentsPerRow[row.Index].Add(segments[key]);
            }

            foreach (var pair in segmentsPerRow)
            {
                var row = annRows.Where(row => row.Index == pair.Key).First();

                var annotation = new SigrokAnnotation
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

        private string[] GetKeys(dynamic PythonObject)
        {
            List<string> items = new List<string>();

            foreach (var key in PythonObject)
                items.Add(key.ToString());

            return items.ToArray();
        }

        public void Dispose()
        {
            channels?.Clear();
            settings?.Clear();
            registeredOutputs?.Clear();
            decoderObject.Dispose();
            thisModule.Dispose();
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

                if (cnd.Any(cnd => cnd.IsZeroSkip()))
                {
                    PyTuple output;
                    var match = CheckConditions(lastState, currentState, cnd, out output);
                    decoder.matched = output;
                    decoder.samplenum = currentSample;
                    return CreateTuple(currentState);
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

                    lastState = currentState;
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

            for (int buc = 0; buc < channels.Count; buc++)
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

            var keys = (string[])GetKeys(condition.keys());
            var values = (string[])GetKeys(condition.values());

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
                Debug.WriteLine($"{startSample} - {endSample} {((PyObject)data).ToString()}");
                registeredOutputs[outputId].Outputs.Add(new SigrokOutputValue { StartSample = startSample, EndSample = endSample, Value = data });
            }
        }

        #endregion

        #region Internal classes
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

            public bool IsZeroSkip()
            {
                return parameters.Count == 1 && parameters[0].ConditionType == WaitConditionType.Skip && parameters[0].Channel == 0;
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
