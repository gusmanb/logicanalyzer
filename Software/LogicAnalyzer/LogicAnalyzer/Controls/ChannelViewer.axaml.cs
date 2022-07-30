using Avalonia;
using Avalonia.Controls;
using Avalonia.Markup.Xaml;
using Avalonia.Media;
using LogicAnalyzer.Classes;
using System;
using System.Collections.Generic;
using System.Linq;

namespace LogicAnalyzer.Controls
{
    public partial class ChannelViewer : UserControl
    {
        TextBox[] boxes;

        int[] channels;
        public int[] Channels
        {
            get { return channels; }
            set 
            { 
                channels = value;
                CreateControls();
            }
        }

        public string[] ChannelsText
        {
            get { return boxes.Select(b => b.Text).ToArray(); }
            set
            {
                if (value == null || channels == null || value.Length != channels.Length)
                    return;
                else
                {
                    for (int buc = 0; buc < value.Length; buc++)
                        boxes[buc].Text = value[buc];
                }
            }
        }

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

                newChannelLabel.Text = $"Channel {channels[buc] + 1}";

                newChannelLabel.Foreground = GraphicObjectsCache.GetBrush(AnalyzerColors.FgChannelColors[buc]);

                newChannelGrid.Children.Add(newChannelLabel);

                //Create textbox
                var newChannelTextbox = new TextBox();
                newBoxes.Add(newChannelTextbox);

                newChannelTextbox.SetValue(Grid.RowProperty, 1);

                newChannelTextbox.VerticalAlignment = Avalonia.Layout.VerticalAlignment.Center;
                newChannelTextbox.HorizontalAlignment = Avalonia.Layout.HorizontalAlignment.Stretch;
                newChannelTextbox.Margin = new Thickness(5, 0, 5, 0);

                newChannelTextbox.Background = GraphicObjectsCache.GetBrush(AnalyzerColors.BgChannelColors[1 - (buc % 2)]);
                newChannelTextbox.Foreground = GraphicObjectsCache.GetBrush(AnalyzerColors.TxtColor);

                newChannelTextbox.MinHeight = newChannelTextbox.MaxHeight = newChannelTextbox.Height = 18;
                newChannelTextbox.Padding = new Thickness(2);
                newChannelTextbox.BorderThickness = new Thickness(0);
                newChannelTextbox.FontSize = 10;
                newChannelTextbox.TextAlignment = TextAlignment.Center;

                newChannelGrid.Children.Add(newChannelTextbox);
            }

            boxes = newBoxes.ToArray();

            ChannelGrid.EndBatchUpdate();

        }

        public ChannelViewer()
        {
            InitializeComponent();
        }
    }

    public class RegionEventArgs : EventArgs
    {
        public SelectedSampleRegion? Region { get; set; }
    }
}
