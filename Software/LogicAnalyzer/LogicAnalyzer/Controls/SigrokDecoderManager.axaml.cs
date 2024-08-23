using Avalonia;
using Avalonia.Controls;
using Avalonia.Input;
using Avalonia.Markup.Xaml;
using Avalonia.Threading;
using LogicAnalyzer.Classes;
using SigrokDecoderBridge;
using System;
using System.Collections.Generic;
using System.Collections.ObjectModel;
using System.Linq;
using System.Threading;

namespace LogicAnalyzer.Controls;

public partial class SigrokDecoderManager : UserControl
{
    private SigrokProvider? _provider;

    public BatchObservableCollection<DecoderCategory> DecoderCategories { get;  } = new BatchObservableCollection<DecoderCategory>();

    Dictionary<string, SigrokDecoderOptions> decoderOptions = new Dictionary<string, SigrokDecoderOptions>();

    private CaptureChannel[]? channels;
    private int sampleRate;

    public event EventHandler<DecodingEventArgs>? DecodingComplete;

    Timer? decodeTimer;

    public CaptureChannel[]? Channels
    {
        get { return channels; }
    }

    public void SetChannels(int SampleRate, CaptureChannel[]? Channels)
    {
        channels = Channels;
        sampleRate = SampleRate;
        UpdateChannels();
    }

    private void UpdateChannels()
    {
        foreach(var opt in decoderOptions.Values)
        {
            opt.UpdateChannels(channels);
        }
    }

    public SigrokDecoderManager()
    {
        InitializeComponent();
        DataContext = this;
    }

    private void TxtFilter_PointerPressed(object? sender, PointerPressedEventArgs e)
    {
        txtFilter.Text = "";
    }

    private void TxtFilter_TextChanged(object? sender, TextChangedEventArgs e)
    {
        GenerateCategories();
    }

    public void Initialize(SigrokProvider Provider)
    {

        DecoderCategories.Clear();

        _provider = Provider;

        GenerateCategories();

    }

    private void GenerateCategories()
    {
        if(_provider == null)
            return;

        var result = new Dictionary<string, List<SigrokDecoderBase>>();

        var decoders = string.IsNullOrWhiteSpace(txtFilter.Text) ? 
            _provider.Decoders :
            _provider.Decoders.Where(d => 
            d.DecoderShortName.ToLower().Contains(txtFilter.Text.Trim().ToLower()) ||
            d.DecoderName.ToLower().Contains(txtFilter.Text.Trim().ToLower())
            ).ToArray();

        if (decoders == null || decoders.Length == 0)
        {
            DecoderCategories.Clear();
            return;
        }

        result["All"] = new List<SigrokDecoderBase>();

        result["All"].AddRange(decoders);

        foreach (var decoder in decoders)
        {
            foreach (var category in decoder.Categories)
            {
                if (!result.ContainsKey(category))
                    result[category] = new List<SigrokDecoderBase>();

                result[category].Add(decoder);
            }
        }

        List<DecoderCategory> finalCats = new List<DecoderCategory>();

        foreach (var cat in result.OrderBy(c => c.Key))
        {
            var category = new DecoderCategory() { Name = cat.Key };

            foreach (var decoder in cat.Value.OrderBy(d => d.DecoderShortName))
            {
                category.Decoders.Add(decoder);
            }

            finalCats.Add(category);
        }

        DecoderCategories.BeginUpdate();
        DecoderCategories.Clear();
        DecoderCategories.AddRange(finalCats);
        DecoderCategories.EndUpdate();

        if (!string.IsNullOrWhiteSpace(txtFilter.Text))
        {

            var first = tvDecoders.Items.FirstOrDefault();

            if (first == null)
                return;

            var treeViewItem = (TreeViewItem?)tvDecoders.TreeContainerFromItem(first);

            if(treeViewItem == null)
                return;

            treeViewItem.IsExpanded = true;
        }
    }

    private void Button_Click(object? sender, Avalonia.Interactivity.RoutedEventArgs e)
    {
        var decoder = (sender as Button)?.DataContext as SigrokDecoderBase;

        if (decoder == null || _provider == null)
            return;

        if (decoderOptions.ContainsKey(decoder.Id))
            return;

        _provider.AddDecoder(decoder);

        SigrokDecoderOptions options = new SigrokDecoderOptions();
        options.OptionsUpdated += Options_OptionsUpdated;
        options.RemoveDecoder += Options_RemoveDecoder;
        options.Decoder = decoder;
        options.UpdateChannels(channels);
        pnlControls.Children.Add(options);
        decoderOptions.Add(decoder.Id, options);

        
    }

    private void Options_RemoveDecoder(object? sender, EventArgs e)
    {
        var options = sender as SigrokDecoderOptions;
        
        if(options == null)
            return;

        pnlControls.Children.Remove(options);

        if (options.Decoder != null)
        {
            decoderOptions.Remove(options.Decoder.Id);
        }

        EnqueueDecoding();
    }

    private void Options_OptionsUpdated(object? sender, System.EventArgs e)
    {
        EnqueueDecoding();
    }


    private void EnqueueDecoding()
    {
        if(_provider == null)
            return;

        if (decodeTimer == null)
        {
            decodeTimer = new Timer((o) =>
            {
                Dispatcher.UIThread.InvokeAsync(() =>
                {
                    ExecuteDecoding();
                });

            }, null, 2000, Timeout.Infinite);
        }
        else
        {
            decodeTimer.Change(2000, Timeout.Infinite);
        }
    }

    private void ExecuteDecoding()
    {
        if (_provider == null)
            return;

        _provider.BeginSession();

        foreach (var options in decoderOptions.Values)
        {
            if (options == null || options.Decoder == null)
                continue;

            
            _provider.AddDecoder(options.Decoder);

            foreach (var option in options.Values)
            {
                _provider.SetDecoderOptionValue(options.Decoder.Id, option);
            }

            foreach (var channel in options.SelectedChannels)
            {
                if (channel.CaptureIndex != -1)
                    _provider.SetDecoderSelectedChannel(options.Decoder.Id, channel);
            }
        }

        var decoding = _provider.Execute(sampleRate, Channels);

        _provider.EndSession();

        if (DecodingComplete != null)
        {
            DecodingComplete(this, new DecodingEventArgs() { Annotations = decoding });
        }
    }

    public class DecodingEventArgs : EventArgs
    {
        public Dictionary<string, SigrokAnnotation[]>? Annotations { get; set; }
    }

    private void TextBlock_PointerPressed(object? sender, Avalonia.Input.PointerPressedEventArgs e)
    {
    }
}