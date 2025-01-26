using SharedDriver;
using System;
using System.Collections.Generic;
using System.Linq;
using System.Text;
using System.Threading.Tasks;
using Terminal.Gui;

namespace TerminalCapture.Dialogs
{
    public class CaptureDialog : Dialog
    {
        LogicAnalyzerDriver? _driver;
        CaptureSession _session;
        string _port;

        public bool Success { get; private set; }

        public CaptureDialog(string COMPort, CaptureSession Session)
        {
            _session = Session;
            _port = COMPort;

            Width = 65;
            Height = 8;
            Title = "Capture";
            
            var lbl = new Label() { Text = "Capture in progress... Press Cancel to abort.", Y = 1, Width = Dim.Percent(100), TextAlignment = Alignment.Center, ColorScheme = Colors.ColorSchemes["TitleLabel"] };

            var cancelButton = new Button() { Text = "Cancel" };
            cancelButton.Accepting += (o, e) => 
            {
                if (this._driver != null)
                {
                    this._driver.StopCapture();
                    this._driver.Dispose();
                }

                RequestStop();
            };

            cancelButton.X = Pos.Percent(50) - 3;
            cancelButton.Y = Pos.Percent(100) - 2;
            
            Add(lbl, cancelButton);
            _driver = new LogicAnalyzerDriver(_port);
            _driver.CaptureCompleted += Driver_CaptureCompleted;
            _driver.StartCapture(_session);

        }

        private void Driver_CaptureCompleted(object? sender, CaptureEventArgs e)
        {
            Success = true;
            _driver?.Dispose();
            RequestStop();
        }
    }
}
