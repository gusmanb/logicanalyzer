using Avalonia.Controls;
using Avalonia.Controls.Templates;
using Avalonia.LogicalTree;
using Avalonia.Media;
using Avalonia.VisualTree;
using LogicAnalyzer.Classes;
using LogicAnalyzer.Extensions;
using SharedDriver;
using System.Collections.Generic;
using System.Linq;

namespace LogicAnalyzer.Dialogs
{
    public partial class ShiftChannelsDialog : Window
    {
        bool selecting = false;

        List<ListBoxItem> updatedItems = new List<ListBoxItem>();

        public int ShiftAmmount { get; private set; }
        public ShiftDirection ShiftDirection { get; private set; }
        public ShiftMode ShiftMode { get; private set; }
        public AnalyzerChannel[] ShiftedChannels { get; set; }
        public ShiftChannelsDialog()
        {
            InitializeComponent();
            btnAccept.Click += BtnAccept_Click;
            btnCancel.Click += BtnCancel_Click;
            AddHandler(PointerPressedEvent, LstChannels_PointerPressed, handledEventsToo: true);
            AddHandler(PointerMovedEvent, LstChannels_PointerMoved, handledEventsToo: true);
            AddHandler(PointerReleasedEvent, LstChannels_PointerReleased, handledEventsToo: true);
            
        }

        private void BtnCancel_Click(object? sender, Avalonia.Interactivity.RoutedEventArgs e)
        {
            this.Close(false);
        }

        private async void BtnAccept_Click(object? sender, Avalonia.Interactivity.RoutedEventArgs e)
        {
            var selected = lstChannels.SelectedItems.Cast<AnalyzerChannel>().ToArray();

            if (selected == null || selected.Length == 0)
            {
                await this.ShowError("No channel", "No channel has been selected, you must at least select one channel to shift.");
                return;
            }

            ShiftedChannels = selected;
            ShiftAmmount = (int)nudShift.Value;

            if (rbLeft.IsChecked ?? false)
                ShiftDirection = ShiftDirection.Left;
            else
                ShiftDirection = ShiftDirection.Right;

            if (rbHigh.IsChecked ?? false)
                ShiftMode = ShiftMode.High;
            else if (rbLow.IsChecked ?? false)
                ShiftMode = ShiftMode.Low;
            else
                ShiftMode = ShiftMode.Rotate;

            this.Close(true);
        }

        public void Initialize(IEnumerable<AnalyzerChannel> Channels, int MaxShift)
        {
            lstChannels.ItemsSource = Channels;
            nudShift.Maximum = MaxShift;
        }

        private void LstChannels_PointerReleased(object? sender, Avalonia.Input.PointerReleasedEventArgs e)
        {
            selecting = false;
            updatedItems.Clear();
        }

        private void LstChannels_PointerPressed(object? sender, Avalonia.Input.PointerPressedEventArgs e)
        {
            var pos = e.GetCurrentPoint(lstChannels);

            if (!pos.Properties.IsLeftButtonPressed || !e.KeyModifiers.HasFlag(Avalonia.Input.KeyModifiers.Control))
                return;

            var item = (ListBoxItem)lstChannels.GetLogicalChildren().Where(c => (c as ListBoxItem).Bounds.Contains(pos.Position)).FirstOrDefault();

            updatedItems.Add(item);

            selecting = true;

            e.Handled = true;
        }

        private void LstChannels_PointerMoved(object? sender, Avalonia.Input.PointerEventArgs e)
        {
            if(!selecting) 
                return;

            var pos = e.GetCurrentPoint(lstChannels);

            var item = (ListBoxItem)lstChannels.GetLogicalChildren().Where(c => (c as ListBoxItem).Bounds.Contains(pos.Position)).FirstOrDefault();

            if (!updatedItems.Contains(item))
            {
                if (item != null)
                    item.IsSelected = !item.IsSelected;

                updatedItems.Add(item);
            }
        }
    }

    public enum ShiftDirection
    {
        Left,
        Right
    }

    public enum ShiftMode
    {
        High,
        Low,
        Rotate
    }
}
