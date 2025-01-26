using CommandLine;
using SharedDriver;
using System.Runtime.CompilerServices;
using Terminal.Gui;
using TerminalCapture;
using TerminalCapture.Classes;

if(args.Length == 0)
{
    Application.Run<MainWindow>().Dispose();
    Application.Shutdown();
    return 0;
}

return await Parser.Default.ParseArguments<CaptureOptions, TerminalOptions>(args)
        .MapResult(
            (CaptureOptions opts) => Capture(opts),
            (TerminalOptions opts) => RunTerminalCapture(),
            errs => Task.FromResult<int>(-1)
            );

static async Task<int> Capture(CaptureOptions opts)
{

    var ext = System.IO.Path.GetExtension(opts.OutputFile).ToLower();

    if(ext != ".lac" && ext != ".csv")
    {
        Console.WriteLine("Unsupported output format, only LogicAnalyzer captures (.lac) or comma sepparated values (.csv) files are supported.");
        return 1;
    }

    bool exportCsv = ext == ".csv";

    var settings = FileOperations.LoadSession(opts.SettingsFile);

    if(settings == null)
    {
        Console.WriteLine("Invalid settings file.");
        return 1;
    }

    try
    {

        LogicAnalyzerDriver driver = new LogicAnalyzerDriver(opts.SerialPort);
        TaskCompletionSource<bool> tcs = new TaskCompletionSource<bool>();

        driver.CaptureCompleted += (s, e) =>
        {
            if (exportCsv)
            {
                FileOperations.SaveCSV(e.Session, opts.OutputFile);
            }
            else
            {
                FileOperations.SaveLAC(e.Session, opts.OutputFile);
            }
            driver.Dispose();
            Console.WriteLine("Capture completed.");
            tcs.SetResult(true);
        };
        Console.CancelKeyPress += (s, e) =>
        {
            driver.StopCapture();
            Console.WriteLine("Capture aborted.");
            tcs.SetResult(false);
        };

        driver.StartCapture(settings);
        Console.WriteLine("Capture started, press Ctrl+C to stop.");
        await tcs.Task;
        driver.Dispose();
    }
    catch (Exception ex) 
    {
        Console.WriteLine($"Error capturing data: {ex.Message}");
        return 1;

    }
    return 0;
}

static async Task<int> RunTerminalCapture()
{
    Application.Run<MainWindow>().Dispose();
    Application.Shutdown();
    return 0;
}