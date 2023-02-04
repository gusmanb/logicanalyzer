using Avalonia.Controls;
using LogicAnalyzer.Extensions;
using MessageBox.Avalonia;
using System;
using System.Reflection;
using System.Text.RegularExpressions;
using System.Threading.Tasks;

namespace LogicAnalyzer.Dialogs
{
    public partial class NetworkDialog : Window
    {
        static Regex regAddress = new Regex("([0-9]+\\.[0-9]+\\.[0-9]+\\.[0-9]+)");
        public string Address { get; private set; }
        public ushort Port { get; private set; }
        public NetworkDialog()
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
            if (!regAddress.IsMatch(txtAddress.Text))
            {
                await ShowError("Invalid address", "The specified address is not in the correct format.");
                return;
            }
            this.Address = txtAddress.Text;
            this.Port = (ushort)nudPort.Value;
            this.Close(true);
        }

        private async Task ShowError(string Title, string Text)
        {
            var box = MessageBoxManager.GetMessageBoxStandardWindow(Title, Text, icon: MessageBox.Avalonia.Enums.Icon.Error);

            var prop = box.GetType().GetField("_window", BindingFlags.Instance | BindingFlags.NonPublic);
            var win = prop.GetValue(box) as Window;

            win.Icon = this.Icon;
            await box.ShowDialog(this);
        }
    }
}
