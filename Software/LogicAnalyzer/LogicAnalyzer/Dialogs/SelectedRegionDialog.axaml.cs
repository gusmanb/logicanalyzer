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
        public SampleRegion NewRegion { get; set; } = new SampleRegion();
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
            if (NewRegion == null)
            {
                await this.ShowError("Error", "No region selected, internal error.");
                return;
            }

            NewRegion.RegionColor = clrRegion.Color;
            NewRegion.RegionName = txtName.Text;
            this.Close(true);
        }

    }
}
