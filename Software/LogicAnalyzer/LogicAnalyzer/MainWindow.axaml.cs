using Avalonia;
using Avalonia.Controls;
using Avalonia.Controls.Primitives;
using Avalonia.Input;
using Avalonia.Interactivity;
using Avalonia.Media.Imaging;
using Avalonia.Platform;
using Avalonia.Shared.PlatformSupport;
using Avalonia.Threading;
using AvaloniaColorPicker;
using AvaloniaEdit.Utils;
using LogicAnalyzer.Classes;
using LogicAnalyzer.Controls;
using LogicAnalyzer.Dialogs;
using LogicAnalyzer.Extensions;
using LogicAnalyzer.Protocols;
using MessageBox.Avalonia;
using MessageBox.Avalonia.Enums;
using Newtonsoft.Json;
using SharedDriver;
using System;
using System.Collections.Generic;
using System.ComponentModel;
using System.Diagnostics;
using System.IO;
using System.IO.Ports;
using System.Linq;
using System.Net.WebSockets;
using System.Reflection;
using System.Runtime.InteropServices;
using System.Text;
using System.Threading;
using System.Threading.Tasks;
using static System.Net.Mime.MediaTypeNames;

namespace LogicAnalyzer
{
    public partial class MainWindow : PersistableWindowBase
    {
        IAnalizerDriver? driver;
        CaptureSettings settings;

        ProtocolAnalyzerLoader pLoader;
        public static MainWindow? Instance { get; private set; }

        UInt128[]? copiedSamples;

        MenuItem? mnuRepeatAnalysis;

        AnalysisSettings? analysisSettings;

        bool preserveSamples = false;
        Timer tmrPower;
        public MainWindow()
        {
            Instance = this;
            InitializeComponent();
            btnRefresh.Click += btnRefresh_Click;
            btnOpenClose.Click += btnOpenClose_Click;
            btnRepeat.Click += btnRepeat_Click;
            btnCapture.Click += btnCapture_Click;
            btnAbort.Click += btnAbort_Click;
            sampleMarker.RegionCreated += sampleMarker_RegionCreated;
            sampleMarker.RegionDeleted += sampleMarker_RegionDeleted;
            sampleMarker.UserMarkerSelected += SampleMarker_UserMarkerSelected;
            
            sampleMarker.MeasureSamples += SampleMarker_MeasureSamples;
            sampleMarker.ShiftSamples += SampleMarker_ShiftSamples;
            sampleMarker.SamplesCutted += SampleMarker_SamplesCutted;
            sampleMarker.SamplesCopied += SampleMarker_SamplesCopied;
            sampleMarker.SamplesPasted += SampleMarker_SamplesPasted;
            sampleMarker.SamplesInserted += SampleMarker_SamplesInserted;
            sampleMarker.SamplesDeleted += SampleMarker_SamplesDeleted;

            channelViewer.ChannelClick += ChannelViewer_ChannelClick;

            tkInScreen.PropertyChanged += tkInScreen_ValueChanged;
            scrSamplePos.Scroll += scrSamplePos_ValueChanged;
            scrSamplePos.PointerEnter += ScrSamplePos_PointerEnter;
            scrSamplePos.PointerLeave += ScrSamplePos_PointerLeave;
            mnuNew.Click += MnuNew_Click;
            mnuOpen.Click += mnuOpen_Click;
            mnuSave.Click += mnuSave_Click;
            mnuExit.Click += MnuExit_Click;
            mnuExport.Click += MnuExport_Click;
            mnuNetSettings.Click += MnuNetSettings_Click;
            mnuDocs.Click += MnuDocs_Click;
            mnuAbout.Click += MnuAbout_Click;
            AddHandler(InputElement.KeyDownEvent, MainWindow_KeyDown, handledEventsToo: true);

            LoadAnalyzers();
            RefreshPorts();

            tmrPower = new Timer((o) => 
            {
                Dispatcher.UIThread.InvokeAsync(() => 
                {
                    GetPowerStatus();
                });
            });
        }

        private async void ChannelViewer_ChannelClick(object? sender, ChannelEventArgs e)
        {
            var picker = new ColorPickerWindow();

            if (e.Channel.ChannelColor != null)
                picker.Color = e.Channel.ChannelColor.Value;
            else
                picker.Color = AnalyzerColors.FgChannelColors[e.Channel.ChannelNumber];

            var color = await picker.ShowDialog(this);

            if (color == null)
                return;

            e.Channel.ChannelColor = color;
            (sender as TextBlock).Foreground = GraphicObjectsCache.GetBrush(color.Value);
            samplePreviewer.UpdateSamples(channelViewer.Channels, sampleViewer.Samples);
            sampleViewer.InvalidateVisual();
        }

        private async void MnuAbout_Click(object? sender, RoutedEventArgs e)
        {
            var aboutDialog = new AboutDialog();
            await aboutDialog.ShowDialog(this);
        }

        private async void MnuDocs_Click(object? sender, RoutedEventArgs e)
        {
            try
            {
                OpenUrl("https://github.com/gusmanb/logicanalyzer/wiki");
            }
            catch 
            { 
                await this.ShowError("Cannot open page.", "Cannot start the default browser. You can access the online documentation in https://github.com/gusmanb/logicanalyzer/wiki");
            }
        }

        private void OpenUrl(string url)
        {
            try
            {
                Process.Start(url);
            }
            catch
            {
                // hack because of this: https://github.com/dotnet/corefx/issues/10361
                if (RuntimeInformation.IsOSPlatform(OSPlatform.Windows))
                {
                    url = url.Replace("&", "^&");
                    Process.Start(new ProcessStartInfo(url) { UseShellExecute = true });
                }
                else if (RuntimeInformation.IsOSPlatform(OSPlatform.Linux))
                {
                    Process.Start("xdg-open", url);
                }
                else if (RuntimeInformation.IsOSPlatform(OSPlatform.OSX))
                {
                    Process.Start("open", url);
                }
                else
                {
                    throw;
                }
            }
        }

        private void MainWindow_KeyDown(object? sender, Avalonia.Input.KeyEventArgs e)
        {
            if (e.KeyModifiers == Avalonia.Input.KeyModifiers.Control)
            {
                switch (e.Key)
                {
                    case Key.Left:
                        {
                            var currentVal = scrSamplePos.Value;
                            var maxVal = sampleViewer.SamplesInScreen;
                            int newVal = (int)currentVal - (maxVal / 10);

                            if (newVal < 0)
                                newVal = 0;

                            scrSamplePos.Value = newVal;
                            scrSamplePos_ValueChanged(scrSamplePos, null);
                        }
                        break;
                    case Key.Right:
                        {
                            var currentVal = scrSamplePos.Value;
                            var maxVal = sampleViewer.SamplesInScreen;
                            int newVal = (int)currentVal + (maxVal / 10);

                            if (newVal > scrSamplePos.Maximum)
                                newVal = (int)scrSamplePos.Maximum;

                            scrSamplePos.Value = newVal;
                            scrSamplePos_ValueChanged(scrSamplePos, null);
                        }
                        break;
                    case Key.Down:
                        {
                            var currentVal = scrSamplePos.Value;
                            var maxVal = sampleViewer.SamplesInScreen;
                            int newVal = (int)currentVal - maxVal;

                            if (newVal < 0)
                                newVal = 0;

                            scrSamplePos.Value = newVal;
                            scrSamplePos_ValueChanged(scrSamplePos, null);
                        }
                        break;
                    case Key.Up:
                        {
                            var currentVal = scrSamplePos.Value;
                            var maxVal = sampleViewer.SamplesInScreen;
                            int newVal = (int)currentVal + maxVal;

                            if (newVal > scrSamplePos.Maximum)
                                newVal = (int)scrSamplePos.Maximum;

                            scrSamplePos.Value = newVal;
                            scrSamplePos_ValueChanged(scrSamplePos, null);
                        }
                        break;
                }
            }
            else if (e.KeyModifiers == KeyModifiers.Shift)
            {
                switch (e.Key)
                {
                    case Key.Left:
                        {
                            var currentVal = scrSamplePos.Value;
                            int newVal = (int)currentVal - 1;

                            if (newVal < 0)
                                newVal = 0;

                            scrSamplePos.Value = newVal;
                            scrSamplePos_ValueChanged(scrSamplePos, null);
                        }
                        break;
                    case Key.Right:
                        {
                            var currentVal = scrSamplePos.Value;
                            int newVal = (int)currentVal + 1;

                            if (newVal > scrSamplePos.Maximum)
                                newVal = (int)scrSamplePos.Maximum;

                            scrSamplePos.Value = newVal;
                            scrSamplePos_ValueChanged(scrSamplePos, null);
                        }
                        break;

                }

            }
        }

        private async void SampleMarker_ShiftSamples(object? sender, EventArgs e)
        {
            var dlg = new ShiftChannelsDialog();
            dlg.Initialize(channelViewer.Channels, sampleViewer.Samples.Length - 1);

            if (await dlg.ShowDialog<bool>(this))
            {
                var samples = sampleViewer.Samples;

                foreach (var channel in dlg.ShiftedChannels)
                {
                    int idx = Array.IndexOf(channelViewer.Channels, channel);

                    var values = ExtractChannelSamples(idx, samples);

                    List<bool> shiftedSamples = new List<bool>();

                    if (dlg.ShiftDirection == ShiftDirection.Left)
                    {
                        shiftedSamples.AddRange(values.Skip(dlg.ShiftAmmount));

                        if (dlg.ShiftMode == ShiftMode.Low)
                            shiftedSamples.AddRange(Enumerable.Range(0, dlg.ShiftAmmount).Select(c => false));
                        else if (dlg.ShiftMode == ShiftMode.High)
                            shiftedSamples.AddRange(Enumerable.Range(0, dlg.ShiftAmmount).Select(c => true));
                        else
                            shiftedSamples.AddRange(values.Take(dlg.ShiftAmmount));
                    }
                    else
                    {
                        if (dlg.ShiftMode == ShiftMode.Low)
                            shiftedSamples.AddRange(Enumerable.Range(0, dlg.ShiftAmmount).Select(c => false));
                        else if (dlg.ShiftMode == ShiftMode.High)
                            shiftedSamples.AddRange(Enumerable.Range(0, dlg.ShiftAmmount).Select(c => true));
                        else
                            shiftedSamples.AddRange(values.Skip(values.Length - dlg.ShiftAmmount));

                        shiftedSamples.AddRange(values.Take(values.Length - dlg.ShiftAmmount));
                    }

                    RecomposeChannelSamples(idx, samples, shiftedSamples.ToArray());
                }

                sampleViewer.BeginUpdate();
                sampleViewer.Samples = samples;
                sampleViewer.EndUpdate();
                samplePreviewer.UpdateSamples(channelViewer.Channels, samples);
                samplePreviewer.ViewPosition = sampleViewer.FirstSample;
            }
        }

        private void RecomposeChannelSamples(int ChannelIndex, UInt128[] Samples, bool[] NewValues)
        {
            UInt128 clearMask = ~(((UInt128)1) << ChannelIndex);
            UInt128 trueValue = ((UInt128)1) << ChannelIndex;

            for (int buc = 0; buc < Samples.Length; buc++)
            {
                UInt128 newSample = Samples[buc] & clearMask;
                
                if (NewValues[buc])
                    newSample |= trueValue;

                Samples[buc] = newSample;
            }
        }
        private bool[] ExtractChannelSamples(int ChannelIndex, UInt128[] Samples)
        {
            UInt128 mask = ((UInt128)1) << ChannelIndex;

            List<bool> values = new List<bool>();

            for(int buc = 0; buc < Samples.Length; buc++) 
            {
                if ((Samples[buc] & mask) != 0)
                    values.Add(true);
                else
                    values.Add(false);
            }

            return values.ToArray();
        }

        private async void MnuNew_Click(object? sender, RoutedEventArgs e)
        {
            var dlg = new CaptureDialog();
            var drv = new EmulatedAnalizerDriver(5);
            dlg.Initialize(drv);

            if(await dlg.ShowDialog<bool>(this))
            {
                var stn = dlg.SelectedSettings;
                var channels = stn.CaptureChannels.Select(c => c.ChannelNumber).ToArray();
                var names = stn.CaptureChannels.Select(c => c.ChannelName).ToArray();
                var limits = drv.GetLimits(channels);

                var dlgCreate = new CreateSamplesDialog();
                dlgCreate.InsertMode = false;
                dlgCreate.Initialize(
                    channels,
                    names, 
                    stn.PreTriggerSamples + stn.PostTriggerSamples,
                    stn.PreTriggerSamples + stn.PostTriggerSamples);
                
                var samples = await dlgCreate.ShowDialog<UInt128[]?>(this);

                if (samples == null)
                    return;

                settings = stn;
                driver = drv;

                sampleViewer.BeginUpdate();
                sampleViewer.Samples = samples;
                sampleViewer.PreSamples = settings.PreTriggerSamples;
                sampleViewer.Channels = settings.CaptureChannels;
                sampleViewer.SamplesInScreen = Math.Min(100, samples.Length / 10);
                sampleViewer.FirstSample = Math.Max(settings.PreTriggerSamples - 10, 0);
                sampleViewer.ClearRegions();
                sampleViewer.ClearAnalyzedChannels();

                sampleViewer.EndUpdate();

                channelViewer.Channels = settings.CaptureChannels;

                samplePreviewer.ViewPosition = sampleViewer.FirstSample;
                samplePreviewer.UpdateSamples(channelViewer.Channels, samples);

                sampleMarker.VisibleSamples = sampleViewer.SamplesInScreen;
                sampleMarker.FirstSample = sampleViewer.FirstSample;
                sampleMarker.ClearRegions();
                sampleMarker.ClearAnalyzedChannels();

                scrSamplePos.Maximum = samples.Length - 1;
                scrSamplePos.Value = sampleViewer.FirstSample;
                tkInScreen.Value = sampleViewer.SamplesInScreen;

                mnuSave.IsEnabled = true;
                mnuProtocols.IsEnabled = true;
                mnuExport.IsEnabled = true;
                LoadInfo();
            }
        }

        private async void SampleMarker_SamplesPasted(object? sender, SampleEventArgs e)
        {
            if (e.Sample > sampleViewer.Samples.Length)
            {
                await this.ShowError("Out of range", "Cannot paste samples beyond the end of the sample range.");
                return;
            }

            if(copiedSamples != null)
                await InsertSamples(e.Sample, copiedSamples);
        }

        private async void SampleMarker_SamplesInserted(object? sender, SampleEventArgs e)
        {
            if (e.Sample > sampleViewer.Samples.Length)
            {
                await this.ShowError("Out of range", "Cannot insert samples beyond the end of the sample range.");
                return;
            }

            var channels = settings.CaptureChannels.Select(c => c.ChannelNumber).ToArray();
            var names = settings.CaptureChannels.Select(c => c.ChannelName).ToArray();

            var dlgCreate = new CreateSamplesDialog();
            dlgCreate.InsertMode = true;
            dlgCreate.Initialize(
                channels,
                names,
                driver.GetLimits(channels).MaxTotalSamples - sampleViewer.Samples.Length,
                10);

            var samples = await dlgCreate.ShowDialog<UInt128[]?>(this);

            if (samples == null)
                return;

            await InsertSamples(e.Sample, samples);
            
        }

        private async Task InsertSamples(int sample, UInt128[] newSamples)
        {
            var chans = settings.CaptureChannels.Select(c => c.ChannelNumber).ToArray();
            var maxSamples = driver.GetLimits(chans).MaxTotalSamples;

            if (sampleViewer.Samples.Length + newSamples.Length > maxSamples)
            {
                await this.ShowError("Error", $"Total samples exceed the maximum permitted for this mode ({maxSamples}).");
                return;
            }

            List<UInt128> samples = new List<UInt128>();
            samples.AddRange(sampleViewer.Samples.Take(sample));
            samples.AddRange(newSamples);
            samples.AddRange(sampleViewer.Samples.Skip(sample));

            var regions = sampleViewer.SelectedRegions;
            List<SampleRegion> finalRegions = new List<SampleRegion>();

            int preSamples = sample <= sampleViewer.PreSamples ? sampleViewer.PreSamples + newSamples.Length : sampleViewer.PreSamples;

            foreach (var region in regions)
            {
                int minRegion = Math.Min(region.FirstSample, region.LastSample);
                int maxRegion = Math.Max(region.FirstSample, region.LastSample);

                if (minRegion < sample && maxRegion >= sample)
                    region.LastSample += newSamples.Length;
                else if (maxRegion > sample)
                {
                    region.FirstSample += newSamples.Length;
                    region.LastSample += newSamples.Length;
                }

                finalRegions.Add(region);
            }

            UpdateSamples(sample, samples.ToArray(), preSamples, finalRegions);
        }

        private async void SampleMarker_SamplesCopied(object? sender, SamplesEventArgs e)
        {
            if (e.FirstSample + e.SampleCount > sampleViewer.Samples.Length)
            {
                await this.ShowError("Out of range", "Selected range outside of the sample bounds.");
                return;
            }

            copiedSamples = sampleViewer.Samples.Skip(e.FirstSample).Take(e.SampleCount).ToArray();
        }

        private async void SampleMarker_SamplesCutted(object? sender, SamplesEventArgs e)
        {
            if (e.FirstSample + e.SampleCount > sampleViewer.Samples.Length)
            {
                await this.ShowError("Out of range", "Selected range outside of the sample bounds.");
                return;
            }

            copiedSamples = sampleViewer.Samples.Skip(e.FirstSample).Take(e.SampleCount).ToArray();
            await DeleteSamples(e);
        }

        private async void SampleMarker_SamplesDeleted(object? sender, SamplesEventArgs e)
        {
            if (e.FirstSample >= sampleViewer.Samples.Length)
            {
                await this.ShowError("Out of range", "Selected range outside of the sample bounds.");
                return;
            }

            await DeleteSamples(e);
        }

        async Task DeleteSamples(SamplesEventArgs e)
        {
            var lastSample = e.FirstSample + e.SampleCount - 1;
            var triggerSample = sampleViewer.PreSamples - 1;

            var preDelete = sampleViewer.Samples.Take(e.FirstSample);
            var postDelete = sampleViewer.Samples.Skip(e.FirstSample + e.SampleCount + 1);

            var finalSamples = preDelete.Concat(postDelete).ToArray();

            var finalPreSamples = e.FirstSample > triggerSample ? sampleViewer.PreSamples : sampleViewer.PreSamples - e.SampleCount;

            var regions = sampleViewer.SelectedRegions;
            List<SampleRegion> finalRegions = new List<SampleRegion>();

            foreach (var region in regions)
            {
                int minRegion = Math.Min(region.FirstSample, region.LastSample);
                int maxRegion = Math.Max(region.FirstSample, region.LastSample);

                if (minRegion >= e.FirstSample && maxRegion <= lastSample) //removed
                    continue;

                if (maxRegion <= e.FirstSample && maxRegion <= lastSample) //Region before delete, do not modify
                {
                    finalRegions.Add(region);
                    continue;
                }
                else if (minRegion >= e.FirstSample && minRegion >= lastSample) //Region after delete, offset n samples
                {
                    region.FirstSample -= e.SampleCount;
                    region.LastSample -= e.SampleCount;
                    finalRegions.Add(region);
                    continue;
                }
                else if (minRegion >= e.FirstSample && maxRegion > lastSample) //Begin of region cropped
                {
                    region.FirstSample = lastSample;
                    region.LastSample = maxRegion;

                    if (region.LastSample - region.FirstSample < 1) //Regions smaller than 2 samples are removed
                        continue;

                    region.FirstSample -= e.SampleCount;
                    region.LastSample -= e.SampleCount;
                    finalRegions.Add(region);
                    continue;
                }
                else if (minRegion < e.FirstSample && maxRegion <= lastSample) //End of region cropped
                {
                    region.FirstSample = minRegion;
                    region.LastSample = e.FirstSample;

                    if (region.LastSample - region.FirstSample < 1) //Regions smaller than 2 samples are removed
                        continue;

                    finalRegions.Add(region);
                    continue;
                }
                else //Deleted samples are inside region (not possible, just left for sanity)
                {
                    region.LastSample -= e.SampleCount;

                    if (region.LastSample - region.FirstSample < 1) //Regions smaller than 2 samples are removed
                        continue;

                    finalRegions.Add(region);
                    continue;
                }
            }

            UpdateSamples(e.FirstSample, finalSamples, finalPreSamples, finalRegions);
        }

        private void UpdateSamples(int firstSample, UInt128[] finalSamples, int finalPreSamples, List<SampleRegion> finalRegions)
        {
            sampleViewer.BeginUpdate();
            sampleViewer.Samples = finalSamples;
            sampleViewer.PreSamples = 0;
            sampleViewer.Bursts = null;

            if (sampleViewer.FirstSample > finalSamples.Length - 1)
                sampleViewer.FirstSample = finalSamples.Length - 1;

            sampleViewer.ClearRegions();
            sampleViewer.ClearAnalyzedChannels();

            if (finalRegions.Count > 0)
                sampleViewer.AddRegions(finalRegions);

            sampleViewer.EndUpdate();

            samplePreviewer.UpdateSamples(channelViewer.Channels, finalSamples);
            samplePreviewer.ViewPosition = sampleViewer.FirstSample;

            sampleMarker.VisibleSamples = sampleViewer.SamplesInScreen;
            sampleMarker.FirstSample = sampleViewer.FirstSample;
            sampleMarker.ClearRegions();
            sampleMarker.ClearAnalyzedChannels();

            if (finalRegions.Count > 0)
                sampleMarker.AddRegions(finalRegions);

            scrSamplePos.Maximum = finalSamples.Length - 1;
            scrSamplePos.Value = firstSample - 1;

            settings.PreTriggerSamples = finalPreSamples;
            settings.PostTriggerSamples = finalSamples.Length - finalPreSamples;
        }

        private void SampleMarker_UserMarkerSelected(object? sender, UserMarkerEventArgs e)
        {
            if (e.Position > sampleViewer.Samples.Length)
                return;

            sampleViewer.BeginUpdate();

            if (e.Position == null)
                sampleViewer.UserMarker = null;
            else
                sampleViewer.UserMarker = e.Position;

            sampleViewer.EndUpdate();
        }

        private async void SampleMarker_MeasureSamples(object? sender, SamplesEventArgs e)
        {
            if (e.FirstSample + e.SampleCount > sampleViewer.Samples.Length)
            {
                await this.ShowError("Out of range", "Selected range outside of the sample bounds.");
                return;
            }

            List<byte[]> samples = new List<byte[]>();

            for (int buc = 0; buc < (sampleViewer.Channels?.Length ?? 0); buc++)
                samples.Add(ExtractSamples(buc, sampleViewer.Samples, e.FirstSample, e.SampleCount));

            var names = channelViewer.Channels.Select(c => c.ChannelName).ToArray();

            for (int buc = 0; buc < names.Length; buc++)
                if (string.IsNullOrWhiteSpace(names[buc]))
                    names[buc] = (buc + 1).ToString();

            MeasureDialog dlg = new MeasureDialog();
            dlg.SetData(names, samples, settings.Frequency);
            await dlg.ShowDialog(this);

        }

        private async void MnuNetSettings_Click(object? sender, RoutedEventArgs e)
        {
            var dlg = new NetworkSettingsDialog();

            if (await dlg.ShowDialog<bool>(this))
            {
                bool res = driver.SendNetworkConfig(dlg.AccessPoint, dlg.Password, dlg.Address, dlg.Port);

                if (!res)
                    await this.ShowError("Error", "Error updating network settings, restart the device and try again.");
                else
                    await this.ShowInfo("Updated", "Network settings updated successfully.");
            }
        }

        private async void MnuExport_Click(object? sender, RoutedEventArgs e)
        {
            try
            {
                var sf = new SaveFileDialog();
                {
                    sf.Filters.Add(new FileDialogFilter { Name = "Comma-separated values file", Extensions = new System.Collections.Generic.List<string> { "csv" } });

                    var file = await sf.ShowAsync(this);

                    if (string.IsNullOrWhiteSpace(file))
                        return;

                    StreamWriter sw = new StreamWriter(File.Create(file));

                    StringBuilder sb = new StringBuilder();

                    for (int buc = 0; buc < channelViewer.Channels.Length; buc++)
                    {
                        sb.Append(string.IsNullOrWhiteSpace(channelViewer.Channels[buc].ChannelName) ? $"Channel {buc + 1}" : channelViewer.Channels[buc].ChannelName);

                        if (buc < channelViewer.Channels.Length - 1)
                            sb.Append(",");
                    }

                    sw.WriteLine(sb.ToString());

                    for (int sample = 0; sample < sampleViewer.Samples.Length; sample++)
                    {
                        sb.Clear();

                        for (int buc = 0; buc < channelViewer.Channels.Length; buc++)
                        {
                            if ((sampleViewer.Samples[sample] & ((UInt128)1 << buc)) == 0)
                                sb.Append("0,");
                            else
                                sb.Append("1,");
                        }

                        sb.Remove(sb.Length - 1, 1);

                        sw.WriteLine(sb.ToString());
                    }

                    sw.Close();
                    sw.Dispose();
                }
            }
            catch (Exception ex)
            {
                await this.ShowError("Unhandled exception", $"{ex.Message} - {ex.StackTrace}");
            }
        }

        private void MnuExit_Click(object? sender, RoutedEventArgs e)
        {
            Close();
        }

        private void Driver_CaptureCompleted(object? sender, CaptureEventArgs e)
        {
            if (e.Samples == null)
                return;

            Dispatcher.UIThread.InvokeAsync(() =>
            {
                sampleViewer.BeginUpdate();
                sampleViewer.Samples = e.Samples;
                sampleViewer.PreSamples = e.PreSamples;
                sampleViewer.Channels = settings.CaptureChannels;

                if(!preserveSamples)
                    sampleViewer.SamplesInScreen = Math.Min(100, e.Samples.Length / 10);

                sampleViewer.FirstSample = Math.Max(e.PreSamples - 10, 0);

                if (settings.LoopCount > 0)
                {
                    int pos = e.PreSamples;
                    List<int> bursts = new List<int>();

                    for (int buc = 0; buc < settings.LoopCount; buc++)
                    {
                        pos = pos + settings.PostTriggerSamples;
                        bursts.Add(pos);
                    }

                    sampleViewer.Bursts = bursts.ToArray();
                }
                else
                    sampleViewer.Bursts = null;

                sampleViewer.ClearRegions();
                sampleViewer.ClearAnalyzedChannels();
                sampleViewer.EndUpdate();

                channelViewer.Channels = settings.CaptureChannels;

                samplePreviewer.UpdateSamples(channelViewer.Channels, e.Samples);
                samplePreviewer.ViewPosition = sampleViewer.FirstSample;

                scrSamplePos.Maximum = e.Samples.Length - 1;
                scrSamplePos.Value = sampleViewer.FirstSample;
                tkInScreen.Value = sampleViewer.SamplesInScreen;

                sampleMarker.VisibleSamples = sampleViewer.SamplesInScreen;
                sampleMarker.FirstSample = sampleViewer.FirstSample;
                sampleMarker.ClearRegions();
                sampleMarker.ClearAnalyzedChannels();

                btnCapture.IsEnabled = true;
                btnRepeat.IsEnabled = true;
                btnOpenClose.IsEnabled = true;
                btnAbort.IsEnabled = false;
                mnuProtocols.IsEnabled = true;
                mnuSave.IsEnabled = true;
                mnuExport.IsEnabled = true;
                mnuSettings.IsEnabled = driver.DriverType == AnalyzerDriverType.Serial && (driver.DeviceVersion?.Contains("WIFI") ?? false);
                LoadInfo();
                GetPowerStatus();
            });
        }

        private void Form1_Load(object sender, EventArgs e)
        {
            LoadAnalyzers();
            RefreshPorts();
        }

        void LoadAnalyzers()
        {

            string path = Path.Combine(Path.GetDirectoryName(System.Reflection.Assembly.GetExecutingAssembly().Location), "analyzers");

            if(!Directory.Exists(path))
                path = Path.Combine(Path.GetDirectoryName(System.Reflection.Assembly.GetExecutingAssembly().Location), "Analyzers");

            if (!Directory.Exists(path))
            {
                mnuProtocols.Items = new MenuItem[] { new MenuItem { Header = "<- None ->" } };
                return;
            }

            pLoader = new ProtocolAnalyzerLoader(path);

            var protocols = pLoader.ProtocolNames;
            mnuProtocols.Items = null;

            if (protocols.Length == 0)
                mnuProtocols.Items = new MenuItem[] { new MenuItem { Header = "<- None ->" } };
            else
            {
                List<MenuItem> finalItems = new List<MenuItem>();

                finalItems.AddRange(pLoader.ProtocolNames.Select(p =>
                {
                    var itm = new MenuItem { Header = p, Tag = p };
                    itm.Click += ProtocolAnalyzer_Click;
                    return itm;
                }).ToArray());

                mnuRepeatAnalysis = new MenuItem { Header = "Repeat last analysis" };
                mnuRepeatAnalysis.IsEnabled = false;
                mnuRepeatAnalysis.Click += MnuRepeatAnalysis_Click;
                finalItems.Add(mnuRepeatAnalysis);

                var clearItem = new MenuItem { Header = "C_lear analysis data" };
                clearItem.Click += ClearItem_Click;
                finalItems.Add(clearItem);

                

                mnuProtocols.Items = finalItems;
            }
        }

        private void MnuRepeatAnalysis_Click(object? sender, RoutedEventArgs e)
        {

            if (analysisSettings == null || analysisSettings.Channels == null || analysisSettings.Analyzer == null || analysisSettings.Settings == null)
                return;

            var channels = analysisSettings.Channels;
            var samples = sampleViewer.Samples;

            foreach (var channel in channels)
                ExtractSamples(channel, samples);

            var analysisResult = analysisSettings.Analyzer.Analyze(settings.Frequency, settings.PreTriggerSamples - 1, analysisSettings.Settings, channels);

            if (analysisResult != null)
            {
                sampleViewer.BeginUpdate();
                sampleViewer.AddAnalyzedChannels(analysisResult);
                sampleViewer.EndUpdate();
                sampleMarker.BeginUpdate();
                sampleMarker.AddAnalyzedChannels(analysisResult);
                sampleMarker.EndUpdate();
            }
        }

        private void ClearItem_Click(object? sender, RoutedEventArgs e)
        {
            sampleViewer.BeginUpdate();
            sampleViewer.ClearAnalyzedChannels();
            sampleViewer.EndUpdate();
            sampleMarker.BeginUpdate();
            sampleMarker.ClearAnalyzedChannels();
            sampleMarker.EndUpdate();
        }

        private async void ProtocolAnalyzer_Click(object? sender, RoutedEventArgs e)
        {
            var item = (sender as MenuItem)?.Tag?.ToString();

            if (item == null)
                return;

            var analyzer = pLoader.GetAnalyzer(item);

            var dlg = new ProtocolAnalyzerSettingsDialog();
            {

                if (analysisSettings != null && analysisSettings.Analyzer == analyzer)
                    dlg.InitialSettings = analysisSettings;

                dlg.Analyzer = analyzer;
                dlg.Channels = channelViewer.Channels.Select(c => 
                {
                    var ch = new ProtocolAnalyzerSettingsDialog.Channel 
                    { 
                        ChannelIndex = c.ChannelNumber, 
                        ChannelName = string.IsNullOrWhiteSpace(c.ChannelName) ? 
                        $"Channel {c.ChannelNumber + 1}" : 
                        c.ChannelName 
                    };

                    return ch; 
                
                }).ToArray();

                if (await dlg.ShowDialog<bool>(this) != true)
                    return;

                if (dlg.SelectedSettings == null)
                    return;

                var channels = dlg.SelectedChannels;
                var samples = sampleViewer.Samples;

                foreach (var channel in channels)
                    ExtractSamples(channel, samples);

                var analysisResult = analyzer.Analyze(settings.Frequency, settings.PreTriggerSamples - 1, dlg.SelectedSettings, channels);

                if (analysisResult != null)
                {
                    sampleViewer.BeginUpdate();
                    sampleViewer.AddAnalyzedChannels(analysisResult);
                    sampleViewer.EndUpdate();

                    sampleMarker.BeginUpdate();
                    sampleMarker.AddAnalyzedChannels(analysisResult);
                    sampleMarker.EndUpdate();
                }

                analysisSettings = new AnalysisSettings { Analyzer = analyzer, Channels = channels, Settings = dlg.SelectedSettings };

                if(mnuRepeatAnalysis != null)
                    mnuRepeatAnalysis.IsEnabled = true;
            }
        }

        private void ExtractSamples(ProtocolAnalyzerSelectedChannel channel, UInt128[]? samples)
        {
            if (channel == null || samples == null)
                return;

            int idx = channel.ChannelIndex;
            UInt128 mask = (UInt128)1 << idx;
            channel.Samples = samples.Select(s => (s & mask) != 0 ? (byte)1 : (byte)0).ToArray();
        }

        private byte[] ExtractSamples(int channel, UInt128[] samples, int firstSample, int count)
        {
            UInt128 mask = (UInt128)1 << channel;
            return samples.Skip(firstSample).Take(count).Select(s => (s & mask) != 0 ? (byte)1 : (byte)0).ToArray();
        }

        private async void btnOpenClose_Click(object? sender, EventArgs e)
        {
            if (driver == null)
            {
                if (ddPorts.SelectedIndex == -1)
                {
                    await this.ShowError("Error", "Select a serial port to connect.");
                    return;
                }

                try
                {
                    if (ddPorts.SelectedItem?.ToString() == "Multidevice")
                    {
                        MultiConnectDialog dlg = new MultiConnectDialog();

                        if (!await dlg.ShowDialog<bool>(this))
                            return;

                        driver = new MultiAnalizerDriver(dlg.ConnectionStrings);
                    }
                    else if (ddPorts.SelectedItem?.ToString() == "Network")
                    {
                        NetworkDialog dlg = new NetworkDialog();
                        if (!await dlg.ShowDialog<bool>(this))
                            return;

                        driver = new LogicAnalyzerDriver(dlg.Address + ":" + dlg.Port);
                    }
                    else
                        driver = new LogicAnalyzerDriver(ddPorts.SelectedItem?.ToString() ?? "");

                    driver.CaptureCompleted += Driver_CaptureCompleted;
                }
                catch(Exception ex)
                {
                    await this.ShowError("Error", $"Cannot connect to device: ({ex.Message}).");
                    return;
                }

                lblConnectedDevice.Text = driver.DeviceVersion;
                ddPorts.IsEnabled = false;
                btnRefresh.IsEnabled = false;
                btnOpenClose.Content = "Close device";
                btnCapture.IsEnabled = true;
                btnRepeat.IsEnabled = true;
                mnuSettings.IsEnabled = driver.DriverType == AnalyzerDriverType.Serial && (driver.DeviceVersion?.Contains("WIFI") ?? false);
                tmrPower.Change(30000, Timeout.Infinite);
            }
            else
            {
                driver.Dispose();
                driver = null;
                lblConnectedDevice.Text = "< None >";
                ddPorts.IsEnabled = true;
                btnRefresh.IsEnabled = true;
                btnOpenClose.Content = "Open device";
                RefreshPorts();
                btnCapture.IsEnabled = false;
                btnRepeat.IsEnabled = false;
                mnuSettings.IsEnabled = false;
                tmrPower.Change(Timeout.Infinite, Timeout.Infinite);
            }

            GetPowerStatus();
        }

        void GetPowerStatus()
        {
            if (driver == null || !driver.IsNetwork)
            {
                pnlPower.IsVisible = false;
                return;
            }

            if(driver.IsCapturing)
                return;

            var powerStatus = driver.GetVoltageStatus();

            if (string.IsNullOrWhiteSpace(powerStatus) || powerStatus == "UNSUPPORTED")
            {
                pnlPower.IsVisible = false;
                return;
            }

            string[] parts = powerStatus.Split("_");

            if(parts.Length == 2 ) 
            {
                lblVoltage.Text = parts[0];

                var assets = AvaloniaLocator.Current.GetService<IAssetLoader>();
                using var str = assets.Open(new Uri(parts[1] == "1" ? "avares://LogicAnalyzer/Assets/plug.png" : "avares://LogicAnalyzer/Assets/battery.png"));
                Bitmap bmp = new Bitmap(str);
                var oldSrc = imgPowerSource.Source;
                imgPowerSource.Source = bmp;
                pnlPower.IsVisible = true;
                if (oldSrc is IDisposable)
                    ((IDisposable)oldSrc).Dispose();
            }
                    
        }
        private void btnRefresh_Click(object? sender, RoutedEventArgs e)
        {
            RefreshPorts();
        }

        void RefreshPorts()
        {
            ddPorts.Items = null;
            ddPorts.Items = SerialPort.GetPortNames().Concat(new string[] { "Network", "Multidevice" }).ToArray();
        }

        private async void btnRepeat_Click(object? sender, RoutedEventArgs e)
        {
            if (settings == null)
            {
                await this.ShowError("Error", "No capture to repeat");
                return;
            }
            preserveSamples = true;
            BeginCapture();
        }

        private async void btnCapture_Click(object? sender, RoutedEventArgs e)
        {
            var dialog = new CaptureDialog();
            dialog.Initialize(driver);
            if (!await dialog.ShowDialog<bool>(this))
                return;

            settings = dialog.SelectedSettings;
            preserveSamples = false;
            
            tmrPower.Change(Timeout.Infinite, Timeout.Infinite);

            try
            {
                BeginCapture();

                var settingsFile = $"cpSettings{driver.DriverType}.json";
                AppSettingsManager.PersistSettings(settingsFile, settings);

            }
            finally 
            { 
                tmrPower.Change(30000, Timeout.Infinite); 
            }

        }

        private void btnAbort_Click(object? sender, RoutedEventArgs e)
        {
            driver.StopCapture();
            btnCapture.IsEnabled = true;
            btnRepeat.IsEnabled = true;
            btnOpenClose.IsEnabled = true;
            btnAbort.IsEnabled = false;
        }

        private async void BeginCapture()
        {

            if (settings.TriggerType != 0)
            {
                var error = driver.StartPatternCapture(settings.Frequency, settings.PreTriggerSamples, settings.PostTriggerSamples, settings.CaptureChannels.Select(c => c.ChannelNumber).ToArray(), settings.TriggerChannel, settings.TriggerBitCount, settings.TriggerPattern, settings.TriggerType == 2 ? true : false);

                if(error != CaptureError.None)
                    await ShowError(error);
            }
            else
            {
                var error = driver.StartCapture(settings.Frequency, settings.PreTriggerSamples, settings.PostTriggerSamples, settings.LoopCount, settings.CaptureChannels.Select(c => c.ChannelNumber).ToArray(), settings.TriggerChannel, settings.TriggerInverted);

                if (error != CaptureError.None)
                {
                    await ShowError(error);
                    return;
                }
            }

            btnCapture.IsEnabled = false;
            btnRepeat.IsEnabled = false;
            btnOpenClose.IsEnabled = false;
            btnAbort.IsEnabled = true;
            mnuSettings.IsEnabled = false;
        }

        private async Task ShowError(CaptureError error)
        {
            switch (error)
            {
                case CaptureError.Busy:
                    await this.ShowError("Error", "Device is busy, stop the capture before starting a new one.");
                    return;
                case CaptureError.BadParams:
                    await this.ShowError("Error", "Specified parameters are incorrect. Check the documentation in the repository to validate them.");
                    return;
                case CaptureError.HardwareError:
                    await this.ShowError("Error", "Device reported error starting capture. Restart the device and try again.");
                    return;
                case CaptureError.UnexpectedError:
                    await this.ShowError("Error", "Unexpected error, restart the application and the device and try again.");
                    return;
            }
        }
        private void ScrSamplePos_PointerLeave(object? sender, Avalonia.Input.PointerEventArgs e)
        {
            samplePreviewer.IsVisible = false;
        }

        private void ScrSamplePos_PointerEnter(object? sender, Avalonia.Input.PointerEventArgs e)
        {
            samplePreviewer.IsVisible = true;
        }
        private void scrSamplePos_ValueChanged(object? sender, ScrollEventArgs e)
        {
            if (sampleViewer.Samples != null)
            {
                sampleViewer.BeginUpdate();
                sampleViewer.FirstSample = (int)scrSamplePos.Value;
                sampleViewer.EndUpdate();
                samplePreviewer.ViewPosition = sampleViewer.FirstSample;
                sampleMarker.FirstSample = sampleViewer.FirstSample;
            }
        }

        private void tkInScreen_ValueChanged(object? sender, Avalonia.AvaloniaPropertyChangedEventArgs e)
        {
            if (sampleViewer.Samples != null)
            {
                sampleViewer.BeginUpdate();
                sampleViewer.SamplesInScreen = (int)tkInScreen.Value;
                sampleViewer.EndUpdate();
                sampleMarker.VisibleSamples = sampleViewer.SamplesInScreen;
            }

            tbSamples.Text = $"{(int)tkInScreen.Value} samples";
        }

        private void btnJmpTrigger_Click(object? sender, RoutedEventArgs e)
        {
            if (sampleViewer.Samples != null && settings != null)
            {
                sampleViewer.BeginUpdate();
                sampleViewer.FirstSample = (int)Math.Max(settings.PreTriggerSamples - (tkInScreen.Value / 10), 0);
                sampleViewer.EndUpdate();
                scrSamplePos.Value = sampleViewer.FirstSample;
                sampleMarker.FirstSample = sampleViewer.FirstSample;
            }
        }

        private async void mnuSave_Click(object? sender, RoutedEventArgs e)
        {
            try
            {
                var sf = new SaveFileDialog();
                {
                    sf.Filters.Add(new FileDialogFilter { Name = "Logic analyzer captures", Extensions = new System.Collections.Generic.List<string> { "lac" } });
                    var file = await sf.ShowAsync(this);

                    if (string.IsNullOrWhiteSpace(file))
                        return;

                    var sets = settings.Clone();
                    sets.PreTriggerSamples = sampleViewer.PreSamples;
                    sets.LoopCount = sampleViewer.Bursts?.Length ?? 0;

                    ExportedCapture ex = new ExportedCapture { Settings = sets, Samples = sampleViewer.Samples, SelectedRegions = sampleViewer.SelectedRegions };

                    File.WriteAllText(file, JsonConvert.SerializeObject(ex, new JsonConverter[] { new SampleRegion.SampleRegionConverter() }));
                }
            }
            catch (Exception ex)
            {
                await this.ShowError("Unhandled exception", $"{ex.Message} - {ex.StackTrace}");
            }
        }

        private async void mnuOpen_Click(object? sender, RoutedEventArgs e)
        {
            try
            {
                var sf = new OpenFileDialog();
                {
                    sf.Filters.Add(new FileDialogFilter { Name = "Logic analyzer captures", Extensions = new System.Collections.Generic.List<string> { "lac" } });

                    var file = (await sf.ShowAsync(this))?.FirstOrDefault();

                    if (string.IsNullOrWhiteSpace(file))
                        return;

                    ExportedCapture? ex = null;
                    try
                    {
                        ex = JsonConvert.DeserializeObject<ExportedCapture>(File.ReadAllText(file), new JsonConverter[] { new SampleRegion.SampleRegionConverter() });
                    }
                    catch { }

                    if (ex == null)
                    {
                        var exEs = JsonConvert.DeserializeObject<OldExportedCapture>(File.ReadAllText(file), new JsonConverter[] { new SampleRegion.SampleRegionConverter() });

                        if (exEs != null)
                        {
                            var oldset = exEs.Settings;

                            CaptureChannel[] channels = new CaptureChannel[oldset.CaptureChannels.Length];
                            for (int buc = 0; buc < channels.Length; buc++)
                                channels[buc] = new CaptureChannel 
                                { 
                                    ChannelName = (oldset.ChannelTexts?.Length ?? 0) > buc ? oldset.ChannelTexts[buc] : "",
                                    ChannelNumber = (int)oldset.CaptureChannels[buc] 
                                };

                            var newSettings = new CaptureSettings
                            {
                                CaptureChannels = channels,
                                Frequency = oldset.Frequency,
                                PostTriggerSamples = oldset.PostTriggerSamples,
                                PreTriggerSamples = oldset.PreTriggerSamples,
                                LoopCount = 0,
                                TriggerBitCount = oldset.TriggerBitCount,
                                TriggerChannel = oldset.TriggerChannel,
                                TriggerInverted = oldset.TriggerInverted,
                                TriggerPattern = oldset.TriggerPattern,
                                TriggerType = oldset.TriggerType
                            };

                            ex = new ExportedCapture
                            {
                                Samples = exEs.Samples,
                                Settings = newSettings,
                                SelectedRegions = exEs.SelectedRegions
                            };
                        }
                    }

                    if (ex == null)
                        return;

                    settings = ex.Settings;

                    sampleViewer.BeginUpdate();
                    sampleViewer.Samples = ex.Samples;
                    sampleViewer.PreSamples = ex.Settings.PreTriggerSamples;
                    sampleViewer.Channels = ex.Settings.CaptureChannels;
                    sampleViewer.SamplesInScreen = Math.Min(100, ex.Samples.Length / 10);
                    sampleViewer.FirstSample = Math.Max(ex.Settings.PreTriggerSamples - 10, 0);
                    sampleViewer.ClearRegions();
                    sampleViewer.ClearAnalyzedChannels();

                    if (ex.SelectedRegions != null)
                        sampleViewer.AddRegions(ex.SelectedRegions);

                    sampleViewer.EndUpdate();

                    channelViewer.Channels = ex.Settings.CaptureChannels;

                    samplePreviewer.UpdateSamples(channelViewer.Channels, ex.Samples);
                    samplePreviewer.ViewPosition = sampleViewer.FirstSample;

                    sampleMarker.VisibleSamples = sampleViewer.SamplesInScreen;
                    sampleMarker.FirstSample = sampleViewer.FirstSample;
                    sampleMarker.ClearRegions();
                    sampleMarker.ClearAnalyzedChannels();

                    if (ex.SelectedRegions != null)
                        sampleMarker.AddRegions(ex.SelectedRegions);

                    scrSamplePos.Maximum = ex.Samples.Length - 1;
                    scrSamplePos.Value = sampleViewer.FirstSample;
                    tkInScreen.Value = sampleViewer.SamplesInScreen;

                    

                    mnuSave.IsEnabled = true;
                    mnuProtocols.IsEnabled = true;
                    mnuExport.IsEnabled = true;

                    driver = new EmulatedAnalizerDriver(5);

                    LoadInfo();
                }
            }
            catch(Exception ex) 
            {
                await this.ShowError("Unhandled exception", $"{ex.Message} - {ex.StackTrace}");
            }
        }

        void LoadInfo()
        {

            string triggerType = settings.TriggerType == 0 ? "Edge" : (settings.TriggerType == 1 ? "Complex" : "Fast");

            lblFreq.Text = String.Format("{0:n0}", settings.Frequency) + " Hz";
            lblPreSamples.Text = String.Format("{0:n0}", settings.PreTriggerSamples);
            lblPostSamples.Text = String.Format("{0:n0}", settings.PostTriggerSamples);
            lblSamples.Text = String.Format("{0:n0}", settings.PostTriggerSamples + settings.PreTriggerSamples);
            lblChannels.Text = settings.CaptureChannels.Length.ToString();
            lblTrigger.Text = $"{triggerType}, channel {settings.TriggerChannel + 1}";
            lblValue.Text = settings.TriggerType == 0 ? (settings.TriggerInverted ? "Negative" : "Positive") : GenerateStringTrigger(settings.TriggerPattern, settings.TriggerBitCount);
        }

        private string GenerateStringTrigger(ushort triggerPattern, int bitCount)
        {
            string value = "";
            for(int buc = 0; buc < bitCount; buc++)
                value += (triggerPattern & (1 << buc)) == 0 ? "0" : "1";
            return value;
        }

        private void sampleMarker_RegionCreated(object? sender, RegionEventArgs e)
        {
            sampleViewer.BeginUpdate();
            sampleViewer.AddRegion(e.Region);
            sampleViewer.EndUpdate();
        }

        private void sampleMarker_RegionDeleted(object? sender, RegionEventArgs e)
        {
            sampleViewer.BeginUpdate();
            sampleViewer.RemoveRegion(e.Region);
            sampleViewer.EndUpdate();
        }
    }
}
