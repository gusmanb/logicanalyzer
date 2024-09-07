using Avalonia;
using Avalonia.Controls;
using Avalonia.Markup.Xaml;
using SharedDriver;

namespace LogicAnalyzer;

public partial class AnalyzerInfoDialog : Window
{
    public AnalyzerInfoDialog()
    {
        InitializeComponent();
    }

    public void Initialize(AnalyzerDriverBase Driver)
    {
        var info = Driver.GetDeviceInfo();
        lblType.Text = info.Name.ToString();
        lblChan.Text = info.Channels.ToString();
        lblFreq.Text = info.MaxFrequency.ToString("#,##0");
        lblBuf.Text = info.BufferSize.ToString("#,##0");
        lblMinPreEight.Text = info.ModeLimits[0].MinPreSamples.ToString("#,##0");
        lblMaxPreEight.Text = info.ModeLimits[0].MaxPreSamples.ToString("#,##0");
        lblMinPostEight.Text = info.ModeLimits[0].MinPostSamples.ToString("#,##0");
        lblMaxPostEight.Text = info.ModeLimits[0].MaxPostSamples.ToString("#,##0");
        lblMaxTotalEight.Text = info.ModeLimits[0].MaxTotalSamples.ToString("#,##0");
        lblMinPreSixteen.Text = info.ModeLimits[1].MinPreSamples.ToString("#,##0");
        lblMaxPreSixteen.Text = info.ModeLimits[1].MaxPreSamples.ToString("#,##0");
        lblMinPostSixteen.Text = info.ModeLimits[1].MinPostSamples.ToString("#,##0");
        lblMaxPostSixteen.Text = info.ModeLimits[1].MaxPostSamples.ToString("#,##0");
        lblMaxTotalSixteen.Text = info.ModeLimits[1].MaxTotalSamples.ToString("#,##0");
        lblMinPreTwentyFour.Text = info.ModeLimits[2].MinPreSamples.ToString("#,##0");
        lblMaxPreTwentyFour.Text = info.ModeLimits[2].MaxPreSamples.ToString("#,##0");
        lblMinPostTwentyFour.Text = info.ModeLimits[2].MinPostSamples.ToString("#,##0");
        lblMaxPostTwentyFour.Text = info.ModeLimits[2].MaxPostSamples.ToString("#,##0");
        lblMaxTotalTwentyFour.Text = info.ModeLimits[2].MaxTotalSamples.ToString("#,##0");
    }
}