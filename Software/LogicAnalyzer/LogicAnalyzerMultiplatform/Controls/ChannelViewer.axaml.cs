using Avalonia;
using Avalonia.Controls;
using Avalonia.Markup.Xaml;
using Avalonia.Media;
using LogicAnalyzerMultiplatform.Classes;
using System;
using System.Collections.Generic;

namespace LogicAnalyzerMultiplatform.Controls
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

                newChannelGrid.Background = new SolidColorBrush(AnalyzerColors.BgChannelColors[buc % 2], 0.8f);

                ChannelGrid.Children.Add(newChannelGrid);

                //Create label
                var newChannelLabel = new TextBlock();

                newChannelLabel.SetValue(Grid.RowProperty, 0);

                newChannelLabel.VerticalAlignment = Avalonia.Layout.VerticalAlignment.Center;
                newChannelLabel.HorizontalAlignment = Avalonia.Layout.HorizontalAlignment.Center;

                newChannelLabel.Text = $"Channel {channels[buc] + 1}";

                newChannelLabel.Foreground = new SolidColorBrush(AnalyzerColors.FgChannelColors[buc]);

                newChannelGrid.Children.Add(newChannelLabel);

                //Create textbox
                var newChannelTextbox = new TextBox();
                newBoxes.Add(newChannelTextbox);

                newChannelTextbox.SetValue(Grid.RowProperty, 1);

                newChannelTextbox.VerticalAlignment = Avalonia.Layout.VerticalAlignment.Center;
                newChannelTextbox.HorizontalAlignment = Avalonia.Layout.HorizontalAlignment.Stretch;
                newChannelTextbox.Margin = new Thickness(5, 0, 5, 0);

                newChannelTextbox.Background = new SolidColorBrush(AnalyzerColors.BgChannelColors[1 - (buc % 2)], 0.8f);
                newChannelTextbox.Foreground = new SolidColorBrush(AnalyzerColors.TxtColor, 1);

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

            Channels = new int[] { 1, 3, 5 };
        }
    }
}
