using Avalonia;
using Avalonia.Controls;
using Avalonia.Markup.Xaml;
using LogicAnalyzer.Classes;
using SigrokDecoderBridge;
using System.Collections.Generic;
using System.Collections.ObjectModel;
using System.Linq;

namespace LogicAnalyzer.Controls;

public partial class SigrokDecoderManager : UserControl
{
    private SigrokProvider? _provider;

    public ObservableCollection<DecoderCategory> DecoderCategories { get;  } = new ObservableCollection<DecoderCategory>();

    public SigrokDecoderManager()
    {
        InitializeComponent();
        
        DataContext = this;
    }

    public void Initialize(SigrokProvider Provider)
    {

        DecoderCategories.Clear();

        _provider = Provider;

        var result = new Dictionary<string, List<SigrokDecoderBase>>();

        var decoders = _provider.Decoders;

        if (decoders == null || decoders.Length == 0)
            return;

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

        foreach(var cat in result.OrderBy(c => c.Key))
        {
            var category = new DecoderCategory() { Name = cat.Key };

            foreach (var decoder in cat.Value.OrderBy(d => d.DecoderShortName))
            {
                category.Decoders.Add(decoder);
            }

            DecoderCategories.Add(category);
        }

    }

    private void Button_Click(object? sender, Avalonia.Interactivity.RoutedEventArgs e)
    {
        var decoder = (sender as Button)?.DataContext as SigrokDecoderBase;

        if (decoder == null)
            return;

        SigrokDecoderOptions options = new SigrokDecoderOptions();
        options.Decoder = decoder;

        pnlControls.Children.Add(options);
    }
}