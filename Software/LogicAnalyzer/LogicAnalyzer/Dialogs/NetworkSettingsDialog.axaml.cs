using Avalonia.Controls;
using LogicAnalyzer.Extensions;
using MessageBox.Avalonia;
using System;
using System.Reflection;
using System.Text.RegularExpressions;
using System.Threading.Tasks;

namespace LogicAnalyzer.Dialogs
{
    public partial class NetworkSettingsDialog : Window
    {
        static Regex regAddress = new Regex("([0-9]+\\.[0-9]+\\.[0-9]+\\.[0-9]+)");
        public string AccessPoint { get; set; }
        public string Password { get; set; }
        public string Address { get; private set; }
        public ushort Port { get; private set; }
        public NetworkSettingsDialog()
        {
            InitializeComponent();
            btnAccept.Click += BtnAccept_Click;
            btnCancel.Click += BtnCancel_Click;
        }
        protected override void OnOpened(EventArgs e)
        {
            base.OnOpened(e);
            this.FixStartupPosition();
        }

        private void BtnCancel_Click(object? sender, Avalonia.Interactivity.RoutedEventArgs e)
        {
            this.Close(false);
        }

        private async void BtnAccept_Click(object? sender, Avalonia.Interactivity.RoutedEventArgs e)
        {
            if (string.IsNullOrWhiteSpace(txtAccessPoint.Text))
            {
                await this.ShowError("Invalid settings", "No access point name provided.");
                return;
            }

            if (string.IsNullOrWhiteSpace(txtPassword.Text))
            {
                await this.ShowError("Invalid settings", "No password provided.");
                return;
            }

            if (!regAddress.IsMatch(txtAddress.Text))
            {
                await this.ShowError("Invalid settings", "Invalid IP address.");
                return;
            }

            AccessPoint = txtAccessPoint.Text;
            Password = txtPassword.Text;
            Address = txtAddress.Text;
            Port = (ushort)nudPort.Value;
            this.Close(true);
        }
    }
}
