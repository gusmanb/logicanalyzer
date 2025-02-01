using Avalonia;
using Avalonia.Controls;
using Avalonia.Interactivity;
using Avalonia.Markup.Xaml;
using Avalonia.Media;
using LogicAnalyzer.Classes;
using LogicAnalyzer.Controls;
using LogicAnalyzer.Extensions;
using SharedDriver;
using System;
using System.Collections.Generic;
using System.Linq;

namespace LogicAnalyzer.Dialogs;

public partial class MultiComposeDialog : Window
{
    public static readonly StyledProperty<DetectedDevice[]?> DevicesProperty = AvaloniaProperty.Register<MultiComposeDialog, DetectedDevice[]?>(nameof(Devices));

    public static readonly StyledProperty<string[]> RolesProperty = AvaloniaProperty.Register<MultiComposeDialog, string[]>(nameof(Roles));

    public string[] Roles 
    {
        get { return GetValue<string[]>(RolesProperty); }
        set { SetValue<string[]>(RolesProperty, value); }
    }

    public DetectedDevice[]? Devices 
    {
        get { return GetValue<DetectedDevice[]?>(DevicesProperty); }
        set { SetValue<DetectedDevice[]?>(DevicesProperty, value); UpdateRoles(); } 
    }

    LogicAnalyzerDriver? driver;
    bool closed = false;

    private void UpdateRoles()
    {
        if(Devices == null)
        {
            Roles = new string[0];
            return;
        }

        var roles = new List<string>();
        for(int buc = 0; buc < Devices.Length; buc++)
        {
            if(buc == 0)
            {
                roles.Add("Master");
            }
            else
            {
                roles.Add($"Slave {buc}");
            }
        }

        Roles = roles.ToArray();
    }

    public KnownDevice? ComposedDevice { get; set; }

    public MultiComposeDialog()
    {
        this.DataContext = this;
        InitializeComponent();
        lstDevices.SelectionChanged += LstDevices_SelectionChanged;
        btnCancel.Click += BtnCancel_Click;
        btnSave.Click += BtnSave_Click;
    }

    private async void BtnSave_Click(object? sender, RoutedEventArgs e)
    {
        if (driver != null)
        {
            driver.StopBlink();
            driver.Dispose();
            driver = null;
        }

        for (int buc = 0; buc < Devices!.Length; buc++)
        {
            if (!Devices.Any(d => d.AssignedIndex == buc))
            {
                await this.ShowError("Error", $"Please assign a device to role {Roles[buc]}");
                return;
            }
        }

        KnownDevice device = new KnownDevice()
        {
            Entries = Devices.Select(d => new KnownDeviceEntry() { SerialNumber = d.SerialNumber!, Order = d.AssignedIndex }).ToArray()
        };

        this.ComposedDevice = device;
        this.Close(true);
    }

    private void BtnCancel_Click(object? sender, RoutedEventArgs e)
    {
        if (driver != null)
        {
            driver.StopBlink();
            driver.Dispose();
            driver = null;
        }

        this.Close(false);
    }

    private async void LstDevices_SelectionChanged(object? sender, SelectionChangedEventArgs e)
    {
        if(driver != null)
        {
            driver.StopBlink();
            driver.Dispose();
            driver = null;
        }

        if (closed)
            return;

        if (lstDevices.SelectedItem is DetectedDevice device)
        {
            try
            {
                driver = new LogicAnalyzerDriver(device.PortName);
                driver.Blink();
            }
            catch 
            {
                await this.ShowError("Error", $"Could not open device {device.SerialNumber}");
            }
        }
    }

    protected override void OnClosing(WindowClosingEventArgs e)
    {
        closed = true;
        base.OnClosing(e);
        if(driver != null)
        {
            driver.StopBlink();
            driver.Dispose();
            driver = null;
        }
    }
}