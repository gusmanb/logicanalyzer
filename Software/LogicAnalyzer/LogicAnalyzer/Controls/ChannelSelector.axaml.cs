using Avalonia;
using Avalonia.Controls;
using System;

namespace LogicAnalyzer.Controls
{
    public partial class ChannelSelector : UserControl
    {
        public static readonly DirectProperty<ChannelSelector, string> ChannelNameProperty = AvaloniaProperty.RegisterDirect<ChannelSelector, string>(
            nameof(ChannelName),
            o => o.ChannelName,
            (o, v) => o.ChannelName = v);

        public static readonly DirectProperty<ChannelSelector, byte> ChannelNumberProperty = AvaloniaProperty.RegisterDirect<ChannelSelector, byte>(
            nameof(ChannelNumber),
            o => o.ChannelNumber,
            (o, v) => o.ChannelNumber = v);

        public static readonly DirectProperty<ChannelSelector, bool> EnabledProperty = AvaloniaProperty.RegisterDirect<ChannelSelector, bool>(
            nameof(Enabled),
            o => o.Enabled,
            (o, v) => o.Enabled = v);

        public string ChannelName 
        {
            get { return txtName.Text; }
            set { var old = txtName.Text; txtName.Text = value; RaisePropertyChanged(ChannelNameProperty, old, value); } 
        }
        byte number;

        public byte ChannelNumber
        {
            get { return number; }
            set { var old = number; number = value; tbChannel.Text = $"Channel {number + 1}"; RaisePropertyChanged(ChannelNumberProperty, old, value); }
        }
        
        public bool Enabled
        {
            get { return ckEnable.IsChecked ?? false; }
            set { bool old = ckEnable.IsChecked ?? false; ckEnable.IsChecked = true; RaisePropertyChanged(EnabledProperty, old, value); }
        }

        public event EventHandler<EventArgs> Selected;
        public event EventHandler<EventArgs> Deselected;

        public ChannelSelector()
        {
            InitializeComponent();
            ckEnable.Checked += CkEnable_Checked;
            ckEnable.Unchecked += CkEnable_Unchecked;
        }

        private void CkEnable_Unchecked(object? sender, Avalonia.Interactivity.RoutedEventArgs e)
        {
            txtName.IsEnabled = false;
            if(Deselected != null)
                Deselected(this, EventArgs.Empty);
        }

        private void CkEnable_Checked(object? sender, Avalonia.Interactivity.RoutedEventArgs e)
        {
            txtName.IsEnabled = true;
            if(Selected != null)
                Selected(this, EventArgs.Empty);
        }
    }
}
