using Avalonia;
using Avalonia.Controls;
using Avalonia.Markup.Xaml;
using Avalonia.Media;
using Avalonia.Threading;
using LogicAnalyzer.Classes;
using MsBox.Avalonia.Base;
using SharedDriver;
using SigrokDecoderBridge;
using System;
using System.Collections;
using System.Collections.Generic;
using System.Collections.ObjectModel;
using System.Collections.Specialized;
using System.Linq;
using System.Runtime.CompilerServices;
using System.Text;
using System.Threading;

namespace LogicAnalyzer.Controls;

public partial class SigrokDecoderOptions : UserControl
{
    private SigrokDecoderBase? decoder;
    public SigrokDecoderBase? Decoder 
    {
        get => decoder;
        set
        {
            decoder = value;
            CreateOptions();
        }
    }

    private SigrokDecoderManager? manager;

    public event EventHandler? RemoveDecoder;
    public event EventHandler? OptionsUpdated;

    public ObservableCollection<AnalyzerChannel> Channels { get; } = new ObservableCollection<AnalyzerChannel>();
    List<ComboBox> channelSelectors = new List<ComboBox>();
    List<Control> optionControls = new List<Control>();

    Dictionary<int, SigrokSelectedChannel> selectedChannels = new Dictionary<int, SigrokSelectedChannel>();
    public IEnumerable<SigrokSelectedChannel> SelectedChannels { get { return selectedChannels.Values; } }

    Dictionary<int, SigrokOptionValue> values = new Dictionary<int, SigrokOptionValue>();
    public IEnumerable<SigrokOptionValue> Values { get { return values.Values; } }

    ObservableCollection<CBOption>? sourceOptions;
    ComboBox? cbInputs;

    public int DecoderIndex { get; private set; }

    public string OptionsName { get; private set; } = "";

    public bool RequiresInput { get; private set; }

    public SigrokDecoderOptions? ParentDecoder { get; private set; }

    public Color OptColor { get; set; } = AnalyzerColors.GetColor(0);

    private void CreateOptions()
    {
        channelSelectors.Clear();
        pnlOptions.Children.Clear();
        optionControls.Clear();
        selectedChannels.Clear();
        values.Clear();

        if (decoder == null)
            return;

        var same = manager?.decoderOptions.Where(o => o.decoder?.Id == decoder.Id).ToArray();

        if(same != null && same.Length > 0)
            DecoderIndex = same.Select(decoder => decoder.DecoderIndex).Max() + 1;
        
        if(DecoderIndex == 0)
            OptionsName = $"{decoder.DecoderShortName}";
        else
            OptionsName = $"{decoder.DecoderShortName} ({DecoderIndex})";

        txtDecoder.Text = OptionsName;

        bool hasContent = false;

        var signals = decoder?.Channels;
        var options = decoder?.Options;
        var inputs = decoder?.Inputs;
        var outputs = decoder?.Outputs;

        //For now, assume single input
        if (inputs != null && inputs.Length > 0 && inputs[0] != "logic")
        {
            RequiresInput = true;

            Grid gridInputs = new Grid();
            gridInputs.HorizontalAlignment = Avalonia.Layout.HorizontalAlignment.Stretch;
            gridInputs.VerticalAlignment = Avalonia.Layout.VerticalAlignment.Top;
            gridInputs.RowDefinitions.Add(new RowDefinition { Height = GridLength.Auto });
            gridInputs.ColumnDefinitions.Add(new ColumnDefinition { Width = new GridLength(100, GridUnitType.Pixel) });
            gridInputs.ColumnDefinitions.Add(new ColumnDefinition { Width = GridLength.Star });
            gridInputs.RowDefinitions.Add(new RowDefinition { Height = GridLength.Auto });

            TextBlock txtInputs = new TextBlock();
            Grid.SetColumnSpan(txtInputs, 2);
            txtInputs.Text = "Inputs";
            txtInputs.Margin = new Thickness(0, 0, 0, 10);

            gridInputs.Children.Add(txtInputs);

            gridInputs.RowDefinitions.Add(new RowDefinition { Height = GridLength.Auto });

            TextBlock txtInput = new TextBlock();
            txtInput.Text = inputs[0];
            txtInput.VerticalAlignment = Avalonia.Layout.VerticalAlignment.Center;

            cbInputs = new ComboBox();
            cbInputs.SelectedIndex = 0;
            cbInputs.HorizontalAlignment = Avalonia.Layout.HorizontalAlignment.Stretch;
            cbInputs.SelectionChanged += (o, e) =>
                {
                    var selected = cbInputs.SelectedItem as CBOption;

                    if (selected == null)
                        ParentDecoder = null;
                    else
                        ParentDecoder = selected.Options;

                    OptionsUpdated?.Invoke(this, EventArgs.Empty);
                };

            cbInputs.Margin = new Thickness(0, 0, 0, 5);

            gridInputs.Children.Add(txtInput);
            gridInputs.Children.Add(cbInputs);

            Grid.SetRow(txtInput, 1);
            Grid.SetColumn(txtInput, 0);
            Grid.SetRow(cbInputs, 1);
            Grid.SetColumn(cbInputs, 1);

            sourceOptions = new ObservableCollection<CBOption>();
            cbInputs.ItemsSource = sourceOptions;
            GenerateSources();

            pnlOptions.Children.Add(gridInputs);

            hasContent = true;
        }

        if (signals != null && signals.Length > 0)
        {
            if (hasContent)
            {
                Separator sep = new Separator();
                sep.Margin = new Thickness(0, 10, 0, 10);
                pnlOptions.Children.Add(sep);
            }

            Grid gridChannels = new Grid();
            gridChannels.HorizontalAlignment = Avalonia.Layout.HorizontalAlignment.Stretch;
            gridChannels.VerticalAlignment = Avalonia.Layout.VerticalAlignment.Top;
            gridChannels.RowDefinitions.Add(new RowDefinition { Height = GridLength.Auto });
            gridChannels.ColumnDefinitions.Add(new ColumnDefinition { Width = new GridLength(100, GridUnitType.Pixel) });
            gridChannels.ColumnDefinitions.Add(new ColumnDefinition { Width = GridLength.Star });
            gridChannels.RowDefinitions.Add(new RowDefinition { Height = GridLength.Auto });

            TextBlock txtChannels = new TextBlock();
            Grid.SetColumnSpan(txtChannels, 2);
            txtChannels.Text = "Channels";
            txtChannels.Margin = new Thickness(0, 0, 0, 10);

            gridChannels.Children.Add(txtChannels);

            int row = 1;

            foreach (var signal in signals)
            {
                gridChannels.RowDefinitions.Add(new RowDefinition { Height = GridLength.Auto });

                TextBlock txtSignal = new TextBlock();
                txtSignal.Text = signal.Name;
                txtSignal.VerticalAlignment = Avalonia.Layout.VerticalAlignment.Center;

                if (signal.Required)
                    txtSignal.Foreground = new SolidColorBrush(Colors.PaleVioletRed);
                else
                    txtSignal.Foreground = new SolidColorBrush(Colors.LimeGreen);

                ComboBox cbChannel = new ComboBox();
                cbChannel.ItemsSource = Channels;
                cbChannel.SelectedIndex = 0;
                cbChannel.Tag = signal;
                cbChannel.HorizontalAlignment = Avalonia.Layout.HorizontalAlignment.Stretch;
                cbChannel.SelectionChanged += (o, e) =>
                {
                    var selectedChannel = cbChannel.SelectedItem as AnalyzerChannel;
                    if (selectedChannel == null)
                        return;

                    selectedChannels[signal.Index] = new SigrokSelectedChannel { SigrokIndex = signal.Index, CaptureIndex = Channels.IndexOf(selectedChannel) - 1 };

                    OptionsUpdated?.Invoke(this, EventArgs.Empty);
                };

                cbChannel.Margin = new Thickness(0, 0, 0, 5);
                channelSelectors.Add(cbChannel);

                gridChannels.Children.Add(txtSignal);
                gridChannels.Children.Add(cbChannel);

                Grid.SetRow(txtSignal, row);
                Grid.SetColumn(txtSignal, 0);
                Grid.SetRow(cbChannel, row);
                Grid.SetColumn(cbChannel, 1);

                row++;
            }

            pnlOptions.Children.Add(gridChannels);

            hasContent = true;
        }

        

        

        if (options != null && options.Length > 0)
        {

            if (hasContent)
            {
                Separator sep = new Separator();
                sep.Margin = new Thickness(0, 10, 0, 10);
                pnlOptions.Children.Add(sep);
            }

            Grid gridOptions = new Grid();
            gridOptions.HorizontalAlignment = Avalonia.Layout.HorizontalAlignment.Stretch;
            gridOptions.VerticalAlignment = Avalonia.Layout.VerticalAlignment.Top;
            gridOptions.RowDefinitions.Add(new RowDefinition { Height = GridLength.Auto });
            gridOptions.ColumnDefinitions.Add(new ColumnDefinition { Width = new GridLength(100, GridUnitType.Pixel) });
            gridOptions.ColumnDefinitions.Add(new ColumnDefinition { Width = GridLength.Star });
            gridOptions.RowDefinitions.Add(new RowDefinition { Height = GridLength.Auto });

            TextBlock txtOptions = new TextBlock();
            Grid.SetColumnSpan(txtOptions, 2);
            txtOptions.Text = "Options";
            txtOptions.Margin = new Thickness(0, 10, 0, 5);

            gridOptions.Children.Add(txtOptions);

            int row = 1;
            int idx = 0;
            
            foreach (var option in options)
            {

                SigrokOptionValue optValue = new SigrokOptionValue { OptionIndex = option.Index, Value = option.DefaultValue };

                values[optValue.OptionIndex] = optValue;

                gridOptions.RowDefinitions.Add(new RowDefinition { Height = GridLength.Auto });
                gridOptions.RowDefinitions.Add(new RowDefinition { Height = GridLength.Auto });

                TextBlock txtOption = new TextBlock();
                txtOption.Text = option.Caption;
                txtOption.VerticalAlignment = Avalonia.Layout.VerticalAlignment.Center;
                txtOption.Margin = new Thickness(0, 10, 0, 0);

                Control? optControl = null;
                switch (option.OptionType)
                {
                    case SigrokOptionType.Boolean:

                        var ck = new CheckBox { IsVisible = true, Name = $"Check_Index{idx++}", Content = option.CheckCaption, Margin = new Thickness(0, 10, 0, 0) };

                        if (option.DefaultValue != null)
                        {
                            ck.IsChecked = (bool)option.DefaultValue;
                        }

                        ck.IsCheckedChanged += (o, e) =>
                        {
                            optValue.Value = ck.IsChecked ?? false;
                            OptionsUpdated?.Invoke(this, EventArgs.Empty);
                        };

                        optControl = ck;

                        break;

                    case SigrokOptionType.String:

                        var tb = new TextBox { IsVisible = true, Name = $"Text_Index{idx++}", HorizontalAlignment = Avalonia.Layout.HorizontalAlignment.Stretch, Margin = new Thickness(0, 10, 0, 0) };

                        if (option.DefaultValue != null)
                        {
                            tb.Text = option.DefaultValue.ToString();
                        }

                        tb.TextChanged += (o, e) =>
                        {
                            optValue.Value = tb.Text;
                            OptionsUpdated?.Invoke(this, EventArgs.Empty);
                        };

                        optControl = tb;
                        
                        break;

                    case SigrokOptionType.Integer:
                    case SigrokOptionType.Double:

                        var nud = new NumericUpDown { IsVisible = true, Name = $"Numeric_Index{idx++}", Minimum = (decimal)option.MinimumValue, Maximum = (decimal)option.MaximumValue, HorizontalAlignment = Avalonia.Layout.HorizontalAlignment.Stretch, Margin = new Thickness(0, 10, 0, 0), Value = Math.Max((decimal)option.MinimumValue, 0) };

                        if (option.OptionType == SigrokOptionType.Double)
                            nud.FormatString = "0.00";

                        if (option.DefaultValue != null)
                        {
                            nud.Value = Convert.ToDecimal(option.DefaultValue);
                        }

                        nud.ValueChanged += (o, e) =>
                        {
                            optValue.Value = option.OptionType == SigrokOptionType.Integer ? (object)(int)nud.Value : (object)(double)nud.Value;
                            OptionsUpdated?.Invoke(this, EventArgs.Empty);
                        };

                        optControl = nud;
                        
                        break;

                    case SigrokOptionType.List:

                        var list = new ComboBox { IsVisible = true, Name = $"List_Index{idx++}", ItemsSource = option.ListValues, HorizontalAlignment = Avalonia.Layout.HorizontalAlignment.Stretch, Margin = new Thickness(0, 10, 0, 0) };

                        if (option.DefaultValue != null && option.ListValues != null)
                        {
                            list.SelectedIndex = Array.IndexOf(option.ListValues, option.DefaultValue);
                        }

                        list.SelectionChanged += (o, e) =>
                        {
                            optValue.Value = list.SelectedItem?.ToString();
                            OptionsUpdated?.Invoke(this, EventArgs.Empty);
                        };

                        optControl = list;
                        
                        break;


                }


                if (optControl == null)
                    continue;

                optControl.Tag = option;

                gridOptions.Children.Add(txtOption);
                gridOptions.Children.Add(optControl);

                optControl.HorizontalAlignment = Avalonia.Layout.HorizontalAlignment.Stretch;

                Grid.SetRow(txtOption, row++);
                Grid.SetColumnSpan(txtOption, 2);
                Grid.SetRow(optControl, row++);
                Grid.SetColumnSpan(optControl, 2);

                optionControls.Add(optControl);
            }

            pnlOptions.Children.Add(gridOptions);

            hasContent = true;
        }

        

        if ((inputs != null && inputs.Length > 0) || (outputs != null && outputs.Length > 0))
        {
            if (hasContent)
            {
                Separator sep = new Separator();
                sep.Margin = new Thickness(0, 10, 0, 10);
                pnlOptions.Children.Add(sep);
            }

            Grid gridInfo = new Grid();
            gridInfo.HorizontalAlignment = Avalonia.Layout.HorizontalAlignment.Stretch;
            gridInfo.VerticalAlignment = Avalonia.Layout.VerticalAlignment.Top;
            gridInfo.RowDefinitions.Add(new RowDefinition { Height = GridLength.Auto });
            gridInfo.ColumnDefinitions.Add(new ColumnDefinition { Width = new GridLength(100, GridUnitType.Pixel) });
            gridInfo.ColumnDefinitions.Add(new ColumnDefinition { Width = GridLength.Star });
            gridInfo.RowDefinitions.Add(new RowDefinition { Height = GridLength.Auto });

            TextBlock txtInfo = new TextBlock();
            Grid.SetColumnSpan(txtInfo, 2);
            txtInfo.Text = "Info";
            txtInfo.Margin = new Thickness(0, 0, 0, 10);

            gridInfo.Children.Add(txtInfo);

            int row = 1;

            if(inputs != null && inputs.Length > 0)
            {
                gridInfo.RowDefinitions.Add(new RowDefinition { Height = GridLength.Auto });

                TextBlock txtInputs = new TextBlock();
                txtInputs.Text = "Inputs:";
                txtInputs.Margin = new Thickness(0, 0, 0, 5);
                Grid.SetRow(txtInputs, row);

                gridInfo.Children.Add(txtInputs);

                TextBlock txtInput = new TextBlock();
                txtInput.Text = string.Join(", ", inputs);

                gridInfo.Children.Add(txtInput);

                Grid.SetRow(txtInput, row++);
                Grid.SetColumn(txtInput, 1);
            }

            if (outputs != null && outputs.Length > 0)
            {
                gridInfo.RowDefinitions.Add(new RowDefinition { Height = GridLength.Auto });

                TextBlock txtOutputs = new TextBlock();
                Grid.SetColumnSpan(txtOutputs, 2);
                txtOutputs.Text = "Outputs:";
                txtOutputs.Margin = new Thickness(0, 0, 0, 5);
                Grid.SetRow(txtOutputs, row);

                gridInfo.Children.Add(txtOutputs);

                TextBlock txtOutput = new TextBlock();
                txtOutput.Text = string.Join(", ", outputs);

                gridInfo.Children.Add(txtOutput);

                Grid.SetRow(txtOutput, row++);
                Grid.SetColumn(txtOutput, 1);
            }

            pnlOptions.Children.Add(gridInfo);

            hasContent = true;
        }

        OptionsUpdated?.Invoke(this, EventArgs.Empty);
    }

    public SigrokDecoderOptions(SigrokDecoderManager Manager, Color OptionColor) : this()
    {
        manager = Manager;
        manager.decoderOptions.CollectionChanged += DecoderOptions_CollectionChanged;
        OptColor = OptionColor;
        elColor.Fill = GraphicObjectsCache.GetBrush(OptionColor);
    }

    private void DecoderOptions_CollectionChanged(object? sender, NotifyCollectionChangedEventArgs e)
    {
        GenerateSources();
    }

    private void GenerateSources()
    {
        if (sourceOptions != null && cbInputs != null)
        {
            var selectedItem = cbInputs.SelectedItem as CBOption;
            var requiredInput = decoder?.Inputs?[0];

            if (requiredInput == null)
                return;

            sourceOptions.Clear();

            var sources = manager?.decoderOptions.Where(o => o.decoder?.Outputs?.Contains(requiredInput) == true && o != this).ToArray();

            if (sources != null)
            {
                foreach (var source in sources)
                {
                    sourceOptions.Add(new CBOption { Options = source });
                }

                if (selectedItem != null)
                {
                    var sel = sourceOptions.FirstOrDefault(o => o.Options == selectedItem.Options);
                    if (sel != null)
                        cbInputs.SelectedItem = sel;
                }
            }

        }
    }

    public SigrokDecoderOptions()
    {
        InitializeComponent();
        DataContext = this;
        Channels.Add(new AnalyzerChannel { ChannelNumber = -1, ChannelName = "<- None ->" });
    }
    
    private void ButtonRemove_Click(object? sender, Avalonia.Interactivity.RoutedEventArgs e)
    {
        if(RemoveDecoder != null)
        {
            RemoveDecoder(this, EventArgs.Empty);
        }
    }

    public void UpdateChannels(IEnumerable<AnalyzerChannel>? Channels)
    {
        this.Channels.Clear();
        this.Channels.Add(new AnalyzerChannel { ChannelNumber = -1, ChannelName = "<- None ->" });

        var selected = selectedChannels.Values.ToArray();
        selectedChannels.Clear();

        if (Channels != null)
        {
            foreach (var channel in Channels)
            {
                this.Channels.Add(channel);
            }

            foreach (var sel in selected)
            {
                if (sel.CaptureIndex < Channels.Count())
                {
                    selectedChannels[sel.SigrokIndex] = sel;
                    channelSelectors[sel.SigrokIndex].SelectedIndex = sel.CaptureIndex + 1;
                    continue;
                }
            }

        }

        OptionsUpdated?.Invoke(this, EventArgs.Empty);
    }

    public void SetValues(SigrokOptionValue[] Values)
    {
        foreach(var value in Values)
        {
            if (values.ContainsKey(value.OptionIndex))
            {
                values[value.OptionIndex].Value = value.Value;
                var control = optionControls.FirstOrDefault(c => (c.Tag as SigrokOption).Index == value.OptionIndex);

                if (control == null)
                    continue;

                switch (control)
                {
                    case CheckBox ck:
                        ck.IsChecked = (bool)value.Value;
                        break;

                    case TextBox tb:
                        tb.Text = value.Value?.ToString();
                        break;

                    case NumericUpDown nud:
                        nud.Value = Convert.ToDecimal(value.Value);
                        break;

                    default:
                        (control as ComboBox)?.SetValue(ComboBox.SelectedItemProperty, value.Value);
                        break;


                        //case Check b:
                        //    (control as CheckBox)?.SetValue(CheckBox.IsCheckedProperty, b);
                        //    break;

                        //case string s:
                        //    (control as TextBox)?.SetValue(TextBox.TextProperty, s);
                        //    break;

                        //case int i:
                        //    (control as NumericUpDown)?.SetValue(NumericUpDown.ValueProperty, i);
                        //    break;

                        //case double d:
                        //    (control as NumericUpDown)?.SetValue(NumericUpDown.ValueProperty, (decimal)d);
                        //    break;

                        //default:
                        //    (control as ComboBox)?.SetValue(ComboBox.SelectedItemProperty, option.Value);
                        //    break;
                }
            }
        }
    }

    public void SetChannels(SigrokSelectedChannel[] Channels)
    {
        foreach (var channel in Channels)
        {
            var selector = channelSelectors.FirstOrDefault(c => (c.Tag as SigrokChannel)?.Index == channel.SigrokIndex);

            if (selector == null)
                continue;

            int idx = channel.CaptureIndex + 1;

            if (idx >= selector.Items.Count)
                continue;

            var aChannel = this.Channels[idx];

            selector.SelectedItem = aChannel;
        }
    }

    public void SetInput(SigrokDecoderOptions? Input)
    {
        if (cbInputs == null)
            return;

        var selected = sourceOptions?.FirstOrDefault(o => o.Options == Input);

        if (selected != null)
            cbInputs.SelectedItem = selected;
    }

    class CBOption
    {
        public SigrokDecoderOptions Options { get; set; }

        public override string ToString()
        {
            return Options?.OptionsName ?? "";
        }
    }
}