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
        public event EventHandler ChannelVisibilityChanged;

        private void CreateControls()
        {
            ChannelGrid.Children.Clear();

            if (channels == null || channels.Length == 0)
                return;

            ChannelGrid.RowDefinitions.Clear();

            List<TextBox> newBoxes = new List<TextBox>();

            //ChannelGrid.BeginBatchUpdate();

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


                var headerGrid = new Grid();
                headerGrid.ColumnDefinitions = new ColumnDefinitions("32,*");

                //Create eye icon
                var newChannelVisibility = new TextBlock();
                newChannelVisibility.FontFamily= FontFamily.Parse("avares://LogicAnalyzer/Assets/Fonts#Font Awesome 6 Free");
                newChannelVisibility.Text = "";
                newChannelVisibility.Margin = new Thickness(5, 0, 0, 0);
                newChannelVisibility.HorizontalAlignment = Avalonia.Layout.HorizontalAlignment.Center;
                newChannelVisibility.VerticalAlignment = Avalonia.Layout.VerticalAlignment.Center;
                newChannelVisibility.Foreground = GraphicObjectsCache.GetBrush(Colors.White);
                newChannelVisibility.Tag = channels[buc];
                newChannelVisibility.PointerPressed += (o, e) =>
                {
                    var channel = (o as TextBlock)?.Tag as CaptureChannel;

                    if (channel == null)
                        return;

                    channel.Hidden = true;

                    if(ChannelVisibilityChanged != null)
                        ChannelVisibilityChanged(this, EventArgs.Empty);
                };

                headerGrid.Children.Add(newChannelVisibility);

                //Create label
                var newChannelLabel = new TextBlock();

                newChannelLabel.SetValue(Grid.RowProperty, 0);
                newChannelLabel.SetValue(Grid.ColumnProperty, 1);

                newChannelLabel.VerticalAlignment = Avalonia.Layout.VerticalAlignment.Center;
                newChannelLabel.HorizontalAlignment = Avalonia.Layout.HorizontalAlignment.Left;

                newChannelLabel.Text = channels[buc].TextualChannelNumber;

                newChannelLabel.Foreground = GraphicObjectsCache.GetBrush(channels[buc].ChannelColor ??  AnalyzerColors.GetColor(channels[buc].ChannelNumber));

                newChannelLabel.Tag = channels[buc];
                newChannelLabel.PointerPressed += NewChannelLabel_PointerPressed;

                headerGrid.Children.Add(newChannelLabel);


                newChannelGrid.Children.Add(headerGrid);

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

            //ChannelGrid.EndBatchUpdate();
        }

        public void UpdateChannelVisibility()
        {
            if (channels == null)
                return;
            
            var chan = ChannelGrid.Children.Cast<Grid>().ToArray();
            var rows = ChannelGrid.RowDefinitions.ToArray();

            if (chan == null || rows == null)
                return;
            
            if(channels.Length != chan.Length || channels.Length != rows.Length)
                return;

            int vis = 0;

            for (int buc = 0; buc < channels.Length; buc++)
            {
                var txt = chan[buc].Children.Where(c => c is TextBox).FirstOrDefault() as TextBox;

                chan[buc].IsVisible = !channels[buc].Hidden;
                txt.Background = chan[buc].Background = GraphicObjectsCache.GetBrush(AnalyzerColors.BgChannelColors[vis % 2]);
                rows[buc].Height = channels[buc].Hidden ? GridLength.Auto : GridLength.Star;

                if (!channels[buc].Hidden)
                    vis++;
            }
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
