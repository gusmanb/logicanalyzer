using System;
using System.Collections.Generic;
using System.Collections.ObjectModel;
using System.IO.Ports;
using System.Linq;
using System.Text;
using System.Threading.Tasks;
using Terminal.Gui;

namespace TerminalCapture.Dialogs
{
    public class DeviceSelectorDialog : Dialog
    {
        public string? SelectedDevice { get; private set; }

        ObservableCollection<string> devices;

        public DeviceSelectorDialog(bool AllowNetwork = true)
        {
            Title = "Select Device";
            Width = 50;
            Height = 15;

            var deviceList = new ListView();
            deviceList.Width = Dim.Fill()! - 2;
            deviceList.Height = Dim.Fill()! - 3;
            deviceList.X = 1;
            deviceList.Y = 1;
            deviceList.AllowsMarking = false;
            deviceList.CanFocus = true;
            deviceList.ColorScheme = Colors.ColorSchemes["EditableControl"];

            deviceList.SelectedItemChanged += (o, e) =>
            {
                SelectedDevice = this.devices![deviceList.SelectedItem];
            };

            devices = new ObservableCollection<string>(SerialPort.GetPortNames());

            if(AllowNetwork)
                devices.Add("Network");

            deviceList.SetSource(devices);

            var okButton = new Button() { Text = "Ok" };
            okButton.Accepting += (o, e) => 
            {
                if (SelectedDevice == null)
                {
                    MessageBox.ErrorQuery(50, 10, "Error", "You must select a device", "Ok");
                    e.Cancel = true;
                    return;
                }

                if(SelectedDevice == "Network")
                {
                    using var dlgAddr = new InputBox("Network Address", "Enter network address (IP:Port):", 40, 9);
                    Application.Run(dlgAddr);
                    if(dlgAddr.Value == null)
                    {
                        e.Cancel = true;
                        return;
                    }
                    SelectedDevice = dlgAddr.Value;
                }

                RequestStop(); 
            };
            okButton.X = Pos.Percent(50) - 10;
            okButton.Y = Pos.Percent(100) - 2;

            var cancelButton = new Button() { Text = "Cancel" };
            cancelButton.Accepting += (o, e) => { SelectedDevice = null; RequestStop(); };
            cancelButton.X = Pos.Percent(50) + 2;
            cancelButton.Y = Pos.Percent(100) - 2;

            Running = true;

            Add(deviceList, okButton, cancelButton);
        }
    }
}
