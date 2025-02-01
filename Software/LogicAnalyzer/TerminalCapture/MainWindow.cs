using Newtonsoft.Json;
using SharedDriver;
using System;
using System.Collections.Generic;
using System.Linq;
using System.Text;
using System.Threading.Tasks;
using Terminal.Gui;
using TerminalCapture.Classes;
using TerminalCapture.SettingsWizard;
using static System.Collections.Specialized.BitVector32;

namespace TerminalCapture
{
    public partial class MainWindow : Window
    {
        bool _isCapturing;
        AnalyzerDeviceInfo? _deviceInfo;
        CaptureSession? _currentSession;
        bool _captured = false;

        public MainWindow() 
        {
            Colors.ColorSchemes["EditableControl"] = new ColorScheme
            {
                Normal = new Terminal.Gui.Attribute(Color.Black, Color.BrightGreen),
                Focus = new Terminal.Gui.Attribute(Color.White, Color.Black),
                HotNormal = new Terminal.Gui.Attribute(Color.Black, Color.BrightBlue),
                HotFocus = new Terminal.Gui.Attribute(Color.Black, Color.BrightRed),
            };

            Colors.ColorSchemes["TitleLabel"] = new ColorScheme
            {
                Normal = new Terminal.Gui.Attribute(Color.White, Color.BrightBlue),
                Focus = new Terminal.Gui.Attribute(Color.White, Color.BrightBlue),
                HotNormal = new Terminal.Gui.Attribute(Color.White, Color.BrightBlue),
                HotFocus = new Terminal.Gui.Attribute(Color.White, Color.BrightBlue),
            };

            Title = "Terminal Capture - LogicAnalyzer";

            MenuBar bar = new MenuBar();
            bar.Menus = new MenuBarItem[] {
                new MenuBarItem ("_File", new MenuItem [] {

                    new MenuItem ("_New", "", NewSession),
                    new MenuItem ("_Open", "", OpenSession),
                    new MenuBarItem("_Save...", new[]
                    {
                        new MenuItem("Save se_ttings", "", SaveSettings),
                        new MenuItem("Save capture as LogicAnalyzer capture", "", SaveLAC),
                        new MenuItem("Save capture as CSV", "", SaveCSV)
                    }),
                    null,
                    new MenuItem ("_Quit", "", () => Application.RequestStop())
                }),
                new MenuBarItem ("_Capture", new MenuItem [] {
                    new MenuItem ("C_onfigure", "", Configure),
                    new MenuItem ("Start Ca_pture", "", StartCapture, () => { return !this._isCapturing && _currentSession != null; })
                }),
                new MenuBarItem("_Device", new MenuItem[] {
                    new MenuItem ("_Read device info", "", ReadDeviceInfo),
                    new MenuItem ("_View device info", "", ViewDeviceInfo),
                    new MenuItem("Se_t network address", "", SetNetworkAddress)
                }),
                new MenuBarItem ("_Help", new MenuItem [] {
                    new MenuItem("H_ow to use", "", ShowHelp),
                    new MenuItem ("_About", "", () => MessageBox.Query(50, 14, "About", "Terminal Capture - LogicAnalyzer\n\nA terminal based frontend for the LogicAnalyzer project.\n\n(c) 2025\n\nAuthor: Agustín Giménez Bernad", "Ok"))
                })
            };

            Add(bar);
        }

        private void SaveSettings()
        {
            if (_currentSession == null)
            {
                MessageBox.ErrorQuery(50, 10, "Error", "\nNo capture settings are available.", "Ok");
                return;
            }

            var dialog = new SaveDialog();
            dialog.Title = "Save capture settings";
            dialog.AllowedTypes = new() { new AllowedType("Capture settings", ".tcs") };
            Application.Run(dialog);

            if (!dialog.Canceled && !string.IsNullOrWhiteSpace(dialog.Path))
            {
                try
                {
                    string json = JsonConvert.SerializeObject(_currentSession.CloneSettings());
                    File.WriteAllText(dialog.Path, json);
                    MessageBox.Query("Success", "Settings saved successfully", "Ok");
                }
                catch
                {
                    MessageBox.ErrorQuery(50, 10, "Error", "\nCould not save the settings.", "Ok");
                }
            }
            
        }

        private void SaveLAC()
        {
            if (_currentSession == null || _currentSession.CaptureChannels == null || !_currentSession.CaptureChannels.Any(c => c.Samples != null && c.Samples.Length > 0))
            {
                MessageBox.ErrorQuery(50, 10, "Error", "\nNo capture is available.", "Ok");
                return;
            }
            var dialog = new SaveDialog();
            dialog.Title = "Save capture as LogicAnalyzer capture";
            dialog.AllowedTypes.Add(new AllowedType("LogicAnalyzer capture.", ".lac"));

            Application.Run(dialog);

            if (!dialog.Canceled && !string.IsNullOrWhiteSpace(dialog.Path))
            {

                if(!FileOperations.SaveLAC(_currentSession, Path.Combine(dialog.Path, dialog.FileName)))
                    MessageBox.ErrorQuery(50, 10, "Error", "\nCould not save the capture.", "Ok");
                else
                    MessageBox.Query("Success", "Capture saved successfully", "Ok");
            }            
        }

        private void SaveCSV()
        {
            if (_currentSession == null || _currentSession.CaptureChannels == null || !_currentSession.CaptureChannels.Any(c => c.Samples != null && c.Samples.Length > 0))
            {
                MessageBox.ErrorQuery(50, 10, "Error", "\nNo capture is available.", "Ok");
                return;
            }
            var dialog = new SaveDialog();
            dialog.Title = "Save capture as CSV";
            dialog.AllowedTypes.Add(new AllowedType("CSV file", ".csv"));

            Application.Run(dialog);

            if (!dialog.Canceled && !string.IsNullOrWhiteSpace(dialog.Path))
            {
                if(!FileOperations.SaveCSV(_currentSession, dialog.Path))
                    MessageBox.ErrorQuery(50, 10, "Error", "\nCould not save the capture.", "Ok");
                else
                    MessageBox.Query("Success", "Capture saved successfully", "Ok");
            }
        }

        private void OpenSession()
        {
            if (_isCapturing)
            {
                MessageBox.ErrorQuery(50, 10, "Error", "\nCannot open a new session while capturing", "Ok");
                return;
            }
            var dialog = new OpenDialog();
            dialog.Title = "Open capture settings";
            dialog.AllowedTypes.Add(new AllowedType("Capture settings", ".tcs"));
            dialog.AllowedTypes.Add(new AllowedType("LogicAnalyzer capture", ".lac"));
            dialog.AllowsMultipleSelection = false;

            Application.Run(dialog);

            if (dialog.FilePaths != null && dialog.FilePaths.Count > 0)
            {
                _captured = false;
                _currentSession = FileOperations.LoadSession(dialog.FilePaths[0]);

                if(_currentSession == null)
                    MessageBox.ErrorQuery(50, 10, "Error", "\nCould not load the capture settings.", "Ok");
                else
                    MessageBox.Query("Success", "Settings loaded successfully", "Ok");
            }
        }

        private void NewSession()
        {
            if (_isCapturing)
            {
                MessageBox.ErrorQuery(50, 10, "Error", "\nCannot create a new session while capturing", "Ok");
                return;
            }
            _currentSession = null;
            _captured = false;
        }

        private void ReadDeviceInfo()
        {
            var dialog = new Dialogs.DeviceSelectorDialog();
            Application.Run(dialog);
            if (dialog.SelectedDevice != null)
                ReadLimits(dialog.SelectedDevice);
        }

        private void ViewDeviceInfo()
        {
            if (_deviceInfo == null)
            {
                MessageBox.Query(50, 10, "Warning", "\nDevice info has not been read.", "Ok");
                return;
            }

            var dialog = new Dialogs.DeviceInfoDialog(_deviceInfo);
            Application.Run(dialog);
        }

        private void Configure()
        {
            if (_deviceInfo == null)
            {
                MessageBox.Query(50, 10, "Warning", "\nLimits have not been read, no restriction will be enforced and the resulting configuration may not work on your device.", "Ok");
            }
            var wizard = new ConfigurationWizard(_deviceInfo, _currentSession);
            
            Application.Run(wizard);

            if (wizard.Success)
                _currentSession = wizard.Configuration;
        }

        private void StartCapture()
        {
            if (_currentSession == null)
            {
                MessageBox.ErrorQuery(50, 10, "Error", "\nNo capture settings are available.", "Ok");
                return;
            }

            using var dialog = new Dialogs.DeviceSelectorDialog();
            Application.Run(dialog);

            if (dialog.SelectedDevice != null)
            {
                try
                {
                    using var captureDialog = new Dialogs.CaptureDialog(dialog.SelectedDevice, _currentSession);
                    Application.Run(captureDialog);
                    if (captureDialog.Success)
                    {
                        _captured = true;
                        MessageBox.Query(50, 10, "Capture Complete", "Capture has completed successfully.", "Ok");
                    }
                }
                catch { MessageBox.ErrorQuery("Error", "Error starting capture.", "Ok"); }
            }
        }

        private void SetNetworkAddress()
        {
            using var dlgDevice = new Dialogs.DeviceSelectorDialog(false);
            Application.Run(dlgDevice);
            if (dlgDevice.SelectedDevice == null)
                return;

            using var drv = new LogicAnalyzerDriver(dlgDevice.SelectedDevice);

            if (drv.DeviceVersion == null || !drv.DeviceVersion.Contains("WIFI"))
            {
                Console.WriteLine($"Device does not support WiFi. Aborting operation.");
                return;
            }

            using var dlgIp = new Dialogs.InputBox("Network Address", "Enter network address (IP:Port):", 40, 9);
            Application.Run(dlgIp);

            if (dlgIp.Value == null)
                return;

            string[] ipParts = dlgIp.Value.Split(':');
            if (ipParts.Length != 2)
            {
                MessageBox.ErrorQuery(50, 10, "Error", "\nInvalid address format.", "Ok");
                return;
            }

            if (!ushort.TryParse(ipParts[1], out ushort port))
            {
                MessageBox.ErrorQuery(50, 10, "Error", "\nInvalid port number.", "Ok");
                return;
            }

            var dlgAP = new Dialogs.InputBox("Access Point", "Enter connection string (AP:Pwd):", 40, 9);
            Application.Run(dlgAP);

            if (dlgAP.Value == null)
                return;

            var apParts = dlgAP.Value.Split(':');
            if (apParts.Length != 2)
            {
                MessageBox.ErrorQuery(50, 10, "Error", "\nInvalid access point format.", "Ok");
                return;
            }

            if(!drv.SendNetworkConfig(apParts[0], apParts[1], ipParts[0], port))
                MessageBox.ErrorQuery(50, 10, "Error", "\nCould not set network address.", "Ok");
            else
                MessageBox.Query("Success", "Network address set successfully", "Ok");
        }

        private void ShowHelp()
        {
            using var dlg = new Dialogs.HelpDialog();
            Application.Run(dlg);
        }

        private void ReadLimits(string SerialPort)
        {
            try
            {
                LogicAnalyzerDriver driver = new LogicAnalyzerDriver(SerialPort);
                _deviceInfo = driver.GetDeviceInfo();
                driver.Dispose();
                MessageBox.Query("Success", "Device info read successfully.", "Ok");
            }
            catch 
            {
                MessageBox.ErrorQuery(50, 10, "Error", "\nCould not read device limits", "Ok");
            }
        }
    }
}
