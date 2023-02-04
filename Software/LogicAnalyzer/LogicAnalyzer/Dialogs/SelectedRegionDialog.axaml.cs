using Avalonia;
using Avalonia.Controls;
using Avalonia.Interactivity;
using Avalonia.Markup.Xaml;
using Avalonia.Media;
using LogicAnalyzer.Classes;
using LogicAnalyzer.Extensions;
using MessageBox.Avalonia;
using System;
using System.Reflection;
using System.Threading.Tasks;

namespace LogicAnalyzer.Dialogs
{
    public partial class SelectedRegionDialog : Window
    {
        public SelectedSampleRegion SelectedRegion { get; set; } = new SelectedSampleRegion();
        public SelectedRegionDialog()
        {
            InitializeComponent();
            btnAccept.Click += BtnAccept_Click;
            btnCancel.Click += BtnCancel_Click;
#if DEBUG
            this.AttachDevTools();
#endif
        }

        protected override void OnOpened(EventArgs e)
        {
            base.OnOpened(e);
            this.FixStartupPosition();
        }
        private void BtnCancel_Click(object? sender, RoutedEventArgs e)
        {
            this.Close(false);
        }

        private async void BtnAccept_Click(object? sender, RoutedEventArgs e)
        {
            if (SelectedRegion == null)
            {
                await ShowError("Error", "No region selected, internal error.");
                return;
            }

            SelectedRegion.RegionColor = clrRegion.Color;
            SelectedRegion.RegionName = txtName.Text;
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
