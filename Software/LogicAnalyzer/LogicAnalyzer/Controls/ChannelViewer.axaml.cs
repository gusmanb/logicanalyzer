using Avalonia;
using Avalonia.Controls;
using Avalonia.Markup.Xaml;
using Avalonia.Media;
using LogicAnalyzer.Classes;
using SharedDriver;
using System;
using System.Collections.Generic;
using System.Linq;

namespace LogicAnalyzer.Controls
{
    public partial class ChannelViewer : UserControl
    {
        TextBox[] boxes;

        CaptureChannel[] channels;
        public CaptureChannel[] Channels
        {
            get { return channels; }
            set 
            { 
                channels = value;
                CreateControls();
            }
        }

        public event EventHandler<ChannelEventArgs> ChannelClick;

        private void CreateControls()
        {
            ChannelGrid.Children.Clear();

            if (channels == null || channels.Length == 0)
                return;

            ChannelGrid.RowDefinitions.Clear();

            List<TextBox> newBoxes = new List<TextBox>();

            ChannelGrid.BeginBatchUpdate();

            for (int buc = 0; buc < channels.Length; buc++)
            {
                //Create new row
                ChannelGrid.RowDefinitions.Add(new RowDefinition(GridLength.Star));
                
                //Create channel grid
                var newChannelGrid = new Grid();
                
                newChannelGrid.SetValue(Grid.RowProperty, buc);

                newChannelGrid.VerticalAlignment = Avalonia.Layout.VerticalAlignment.Stretch;
                newChannelGrid.HorizontalAlignment = Avalonia.Layout.HorizontalAlignment.Stretch;
                
                newChannelGrid.RowDefinitions = new RowDefinitions("*,*");

                newChannelGrid.Background = GraphicObjectsCache.GetBrush(AnalyzerColors.BgChannelColors[buc % 2]);

                ChannelGrid.Children.Add(newChannelGrid);

                //Create label
                var newChannelLabel = new TextBlock();

                newChannelLabel.SetValue(Grid.RowProperty, 0);

                newChannelLabel.VerticalAlignment = Avalonia.Layout.VerticalAlignment.Center;
                newChannelLabel.HorizontalAlignment = Avalonia.Layout.HorizontalAlignment.Center;

                newChannelLabel.Text = channels[buc].TextualChannelNumber;

                newChannelLabel.Foreground = GraphicObjectsCache.GetBrush(channels[buc].ChannelColor ??  AnalyzerColors.FgChannelColors[buc % 24]);

                newChannelLabel.Tag = channels[buc];
                newChannelLabel.PointerPressed += NewChannelLabel_PointerPressed;

                newChannelGrid.Children.Add(newChannelLabel);

                //Create textbox
                var newChannelTextbox = new TextBox();
                newBoxes.Add(newChannelTextbox);

                newChannelTextbox.SetValue(Grid.RowProperty, 1);

                newChannelTextbox.VerticalAlignment = Avalonia.Layout.VerticalAlignment.Center;
                newChannelTextbox.HorizontalAlignment = Avalonia.Layout.HorizontalAlignment.Stretch;
                newChannelTextbox.Margin = new Thickness(5, 0, 5, 0);

                newChannelTextbox.Background = GraphicObjectsCache.GetBrush(AnalyzerColors.BgChannelColors[buc % 2]);
                newChannelTextbox.Foreground = GraphicObjectsCache.GetBrush(AnalyzerColors.TxtColor);

                newChannelTextbox.MinHeight = newChannelTextbox.MaxHeight = newChannelTextbox.Height = 18;
                newChannelTextbox.Padding = new Thickness(2);
                newChannelTextbox.BorderThickness = new Thickness(0);
                newChannelTextbox.FontSize = 10;
                newChannelTextbox.TextAlignment = TextAlignment.Center;
                newChannelTextbox.Text = channels[buc].ChannelName;
                newChannelTextbox.Tag = channels[buc];
                newChannelTextbox.GetPropertyChangedObservable(TextBox.TextProperty).Subscribe(NewChannelTextbox_TextChanged);
                newChannelGrid.Children.Add(newChannelTextbox);
            }

            boxes = newBoxes.ToArray();

            ChannelGrid.EndBatchUpdate();
        }

        private void NewChannelLabel_PointerPressed(object? sender, Avalonia.Input.PointerPressedEventArgs e)
        {
            var label = sender as TextBlock;

            if (label == null)
                return;

            var channel = label.Tag as CaptureChannel;

            if(channel == null) 
                return;

            if (ChannelClick == null)
                return;

            ChannelClick(sender , new ChannelEventArgs { Channel = channel });
        }

        void NewChannelTextbox_TextChanged(AvaloniaPropertyChangedEventArgs e)
        {
            ((e.Sender as TextBox).Tag as CaptureChannel).ChannelName = e.NewValue?.ToString();
        }

        public ChannelViewer()
        {
            InitializeComponent();
        }
    }

    public class ChannelEventArgs : EventArgs
    {
        public required CaptureChannel Channel { get; set; }
    }

    public class RegionEventArgs : EventArgs
    {
        public SampleRegion? Region { get; set; }
    }

    public class SamplesEventArgs : EventArgs
    {
        public int FirstSample { get; set; }
        public int SampleCount { get; set; }
    }

    public class SampleEventArgs : EventArgs
    {
        public int Sample { get; set; }
    }

    public class UserMarkerEventArgs : EventArgs
    {
        public int? Position { get; set; }
    }
}
