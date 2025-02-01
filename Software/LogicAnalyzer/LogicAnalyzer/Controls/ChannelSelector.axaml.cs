using Avalonia;
using Avalonia.Controls;
using Avalonia.Media;
using LogicAnalyzer.Classes;
using System;
using System.Runtime.InteropServices;

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

        public static readonly DirectProperty<ChannelSelector, uint?> ChannelColorProperty = AvaloniaProperty.RegisterDirect<ChannelSelector, uint?>(
            nameof(ChannelColor),
            o => o.ChannelColor,
            (o, v) => o.ChannelColor = v);

        public string ChannelName 
        {
            get { return txtName.Text; }
            set { var old = txtName.Text; txtName.Text = value; RaisePropertyChanged(ChannelNameProperty, old, value); } 
        }

        byte number;
        public byte ChannelNumber
        {
            get { return number; }
            set { var old = number; number = value; tbChannel.Text = $"Channel {number + 1}"; UpdateColor(); RaisePropertyChanged(ChannelNumberProperty, old, value); }
        }
        
        public bool Enabled
        {
            get { return ckEnable.IsChecked ?? false; }
            set { bool old = ckEnable.IsChecked ?? false; ckEnable.IsChecked = value; RaisePropertyChanged(EnabledProperty, old, value); }
        }

        uint? color;
        public uint? ChannelColor
        {
            get { return color; }
            set { color = value; UpdateColor(); RaisePropertyChanged(ChannelColorProperty, null, value); }
        }

        public event EventHandler<EventArgs>? Selected;
        public event EventHandler<EventArgs>? Deselected;
        public event EventHandler<EventArgs>? ChangeColor;

        public ChannelSelector()
        {
            InitializeComponent();
            ckEnable.Checked += CkEnable_Checked;
            ckEnable.Unchecked += CkEnable_Unchecked;
            lblColor.PointerPressed += LblColor_PointerPressed;
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


        private void UpdateColor()
        {
            if (color == null)
            {
                lblColor.Foreground = GraphicObjectsCache.GetBrush(AnalyzerColors.GetColor(number));
            }
            else
            {
                lblColor.Foreground = GraphicObjectsCache.GetBrush(Color.FromUInt32(color.Value));
            }
        }


        private void LblColor_PointerPressed(object? sender, Avalonia.Input.PointerPressedEventArgs e)
        {
            e.Handled = true;

            if (ChangeColor != null)
                ChangeColor(this, EventArgs.Empty);

            if (RuntimeInformation.IsOSPlatform(OSPlatform.Linux) || RuntimeInformation.IsOSPlatform(OSPlatform.OSX))
                e.Pointer.Capture(null);
        }
    }
}
