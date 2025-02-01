using Avalonia;
using Avalonia.Controls;
using Avalonia.Input;
using Avalonia.Markup.Xaml;
using Avalonia.Threading;
using LogicAnalyzer.Classes;
using LogicAnalyzer.SigrokDecoderBridge;
using SharedDriver;
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

    internal ObservableCollection<SigrokDecoderOptions> decoderOptions = new ObservableCollection<SigrokDecoderOptions>();

    private AnalyzerChannel[]? channels;
    private int sampleRate;

    public event EventHandler<DecodingEventArgs>? DecodingComplete;

    int optCount = 0;

    Timer? decodeTimer;

    public AnalyzerChannel[]? Channels
    {
        get { return channels; }
    }

    public void SetChannels(int SampleRate, AnalyzerChannel[]? Channels)
    {
        channels = Channels;
        sampleRate = SampleRate;
        UpdateChannels();
    }

    private void UpdateChannels()
    {
        foreach(var opt in decoderOptions)
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

        SigrokDecoderOptions options = new SigrokDecoderOptions(this, AnalyzerColors.GetColor(optCount++));
        options.OptionsUpdated += Options_OptionsUpdated;
        options.RemoveDecoder += Options_RemoveDecoder;
        options.Decoder = decoder;
        options.UpdateChannels(channels);
        pnlControls.Children.Add(options);
        decoderOptions.Add(options);
    }

    private void Options_RemoveDecoder(object? sender, EventArgs e)
    {
        var options = sender as SigrokDecoderOptions;
        
        if(options == null)
            return;

        pnlControls.Children.Remove(options);

        decoderOptions.Remove(options);

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

        var tree = GenerateDecodingTree();

        var decoding = _provider.Execute(sampleRate, Channels, tree);

        if (DecodingComplete != null)
        {
            AnnotationsGroup[]? annotations = null;

            if (decoding != null)
            {
                List<AnnotationsGroup> anList = new List<AnnotationsGroup>();

                foreach (var pair in decoding)
                {
                    if ((pair.Value?.Length ?? 0) == 0)
                        continue;

                    var opt = decoderOptions.FirstOrDefault(o => o.OptionsName == pair.Key);

                    if (opt == null)
                        continue;

                    anList.Add(new AnnotationsGroup() { GroupColor = opt.OptColor, Annotations = pair.Value });
                }

                if(anList.Count != 0)
                    annotations = anList.ToArray();
                else
                    annotations = null;
            }

            DecodingComplete(this, new DecodingEventArgs() { Annotations = annotations });
        }
    }

    private SigrokDecodingTree GenerateDecodingTree()
    {
        var tree = new SigrokDecodingTree();

        var rootItems = decoderOptions.Where(o => o.RequiresInput == false);

        foreach(var opt in rootItems)
        {
            if(opt.Decoder == null)
                continue;

            var branch = new SigrokDecodingBranch() { Name = opt.OptionsName, Decoder = opt.Decoder, Channels = opt.SelectedChannels.Where(c => c.CaptureIndex != -1).ToArray(), Options = opt.Values.ToArray() };

            tree.Branches.Add(branch);

            PopulateBranch(opt, branch);
        }

        return tree;
    }

    private void PopulateBranch(SigrokDecoderOptions opt, SigrokDecodingBranch branch)
    {
        var children = decoderOptions.Where(o => o.RequiresInput && o.ParentDecoder == opt);

        foreach (var child in children)
        {
            if (child.Decoder == null)
                continue;

            var childBranch = new SigrokDecodingBranch() { Name = child.OptionsName, Decoder = child.Decoder, Channels = child.SelectedChannels.ToArray(), Options = child.Values.ToArray() };

            branch.Children.Add(childBranch);

            PopulateBranch(child, childBranch);
        }
    }

    public class DecodingEventArgs : EventArgs
    {
        public IEnumerable<AnnotationsGroup>? Annotations { get; set; }
    }
}