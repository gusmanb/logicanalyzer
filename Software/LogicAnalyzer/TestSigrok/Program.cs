
using LogicAnalyzer.Protocols;
using SigrokDecoderBridge;

var loader = new SigrokProvider();
var decoders = loader.GetAnalyzers();

foreach (var decoder in decoders)
{
    Console.WriteLine($"Decoder {decoder.ProtocolName}");
    foreach(var signal in decoder.Signals)
    {
        Console.WriteLine($"-- Signal {signal.SignalName}");
    }

    foreach(var setting in decoder.Settings)
    {
        Console.WriteLine($"-- Setting {setting.Caption} - {setting.SettingType} ({setting.DefaultValue})");
    }
}

/*
var codec = decoders.Where(d => d.ProtocolName.StartsWith("Serial Peripheral")).FirstOrDefault();

if (codec != null)
{
    List<ProtocolAnalyzerSettingValue> settings = new List<ProtocolAnalyzerSettingValue>();

    settings.Add(new ProtocolAnalyzerSettingValue 
    {
        SettingIndex = 0,
        Value = "active-high"
    });
    settings.Add(new ProtocolAnalyzerSettingValue
    {
        SettingIndex = 1,
        Value = 1
    });
    settings.Add(new ProtocolAnalyzerSettingValue
    {
        SettingIndex = 2,
        Value = 1
    });
    settings.Add(new ProtocolAnalyzerSettingValue
    {
        SettingIndex = 3,
        Value = "lsb-first"
    });
    settings.Add(new ProtocolAnalyzerSettingValue
    {
        SettingIndex = 4,
        Value = 14
    });

    codec.Analyze(44100, 0, settings.ToArray(), new ProtocolAnalyzerSelectedChannel[0]);
}*/
var codec = decoders.Where(d => d.ProtocolName.StartsWith("Audio")).FirstOrDefault();

if (codec != null)
{
    codec.AnalyzeAnnotations(44100, 0, new ProtocolAnalyzerSettingValue[0], new ProtocolAnalyzerSelectedChannel[0]);
}

/*
using Python.Runtime;
using System.Reflection;
using System.Runtime.CompilerServices;
using System.Runtime.InteropServices;
Runtime.PythonDLL = "C:\\Program Files\\Python311\\python311.dll";
PythonEngine.Initialize();

using (Py.GIL())
{

    dynamic os = Py.Import("os");
    dynamic sys = Py.Import("sys");
    dynamic inspect = Py.Import("inspect");
    sys.path.append("C:\\Users\\geniw\\source\\repos\\LogicAnalyzer\\TestSigrok\\bin\\Debug\\net8.0");
    sys.path.append("C:\\Users\\geniw\\source\\repos\\LogicAnalyzer\\TestSigrok\\bin\\Debug\\net8.0\\decoders");
    //sys.path.append("C:\\Users\\geniw\\source\\repos\\LogicAnalyzer\\TestSigrok\\bin\\Debug\\net8.0\\decoders\\ac97");

    funcCall call = new funcCall();

    using (PyModule scope = Py.CreateScope())
    {

        scope.Exec("import sigrokdecode");
        //dynamic objDec = scope.Eval("sigrokdecode.Decoder");
        //objDec.cObj = call.ToPython();
        scope.Exec(@"import ac97");
        dynamic obj = scope.Eval("ac97.Decoder()");
        obj.cObj = call.ToPython();
        obj.decode();
    }
}

class funcCall
{
    public void HasChannel(dynamic channel)
    {
        Console.WriteLine($"Hello from C# {channel}");
    }
}*/