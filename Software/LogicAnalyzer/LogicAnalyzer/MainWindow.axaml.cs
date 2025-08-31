using Avalonia;
using Avalonia.Controls;
using Avalonia.Controls.Primitives;
using Avalonia.Input;
using Avalonia.Interactivity;
using Avalonia.Media;
using Avalonia.Media.Imaging;
using Avalonia.Platform;
using Avalonia.Threading;
using LogicAnalyzer.Classes;
using LogicAnalyzer.Controls;
using LogicAnalyzer.Dialogs;
using LogicAnalyzer.Extensions;
using LogicAnalyzer.Interfaces;
using LogicAnalyzer.SigrokDecoderBridge;
using MsBox.Avalonia;
using Newtonsoft.Json;
using SharedDriver;
using SigrokDecoderBridge;
using SkiaSharp;
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
        const string Version = "LogicAnalyzer 6.5";

        AnalyzerDriverBase? driver;
        CaptureSession session;

        SigrokProvider? decoderProvider;
        public static MainWindow? Instance { get; private set; }

        IEnumerable<byte[]>? copiedSamples;

        MenuItem? mnuRepeatAnalysis;

        AnalysisSettings? analysisSettings;

        //bool preserveSamples = false;
        Timer tmrHideSamples;
        DispatcherTimer tmrSliderToolTip;

        List<ISampleDisplay> sampleDisplays = new List<ISampleDisplay>();
        List<IRegionDisplay> regionDisplays = new List<IRegionDisplay>();
        List<IMarkerDisplay> markerDisplays = new List<IMarkerDisplay>();

        List<KnownDevice> knownDevices = new List<KnownDevice>();
        KnownDevice? currentKnownDevice = null;

        ProfilesSet? profiles;
        GeneralSettings generalSettings;

        public bool PreviewPinned { get { return samplePreviewer.Pinned; } set { samplePreviewer.Pinned = value; } }

        protected override string[]? PersistProperties
        {
            get
            {
                return ["PreviewPinned"];
            }
        }

        public MainWindow()
        {
            Instance = this;
            InitializeComponent();
            this.Title = Version;
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

           samplePreviewer.PinnedChanged += SamplePreviewer_PinnedChanged;
            samplePreviewer.ViewChanged += SamplePreviewer_ViewChanged;

            sampleViewer.PointerWheelChanged += SampleViewer_PointerWheelChanged;
            tkInScreen.PointerWheelChanged += TkInScreen_PointerWheelChanged;
            scrSamplePos.PointerWheelChanged += ScrSamplePos_PointerWheelChanged;
            samplePreviewer.PointerWheelChanged += ScrSamplePos_PointerWheelChanged;

            lblInfo.PointerPressed += LblInfo_PointerPressed;
            lblBootloader.PointerPressed += LblBootloader_PointerPressed;
            lblForget.PointerPressed += LblForget_PointerPressed;

            channelViewer.ChannelClick += ChannelViewer_ChannelClick;
            channelViewer.ChannelVisibilityChanged += ChannelViewer_ChannelVisibilityChanged;
            tkInScreen.PropertyChanged += tkInScreen_ValueChanged;
            scrSamplePos.Scroll += scrSamplePos_ValueChanged;
            scrSamplePos.PointerEntered += ScrSamplePos_PointerEnter;
            scrSamplePos.PointerExited += ScrSamplePos_PointerLeave;
            mnuNew.Click += MnuNew_Click;
            mnuOpen.Click += mnuOpen_Click;
            mnuSave.Click += mnuSave_Click;
            mnuExit.Click += MnuExit_Click;
            mnuExport.Click += MnuExport_Click;
            mnuNetSettings.Click += MnuNetSettings_Click;
            mnuGeneralSettings.Click += MnuGeneralSettings_Click;
            mnuDocs.Click += MnuDocs_Click;
            mnuAbout.Click += MnuAbout_Click;
            AddHandler(InputElement.KeyDownEvent, MainWindow_KeyDown, handledEventsToo: true);

            pnlPower.PointerPressed += (o, e) => GetPowerStatus();

            tmrHideSamples = new Timer((o) =>
            {
                Dispatcher.UIThread.InvokeAsync(() =>
                {
                    if(!samplePreviewer.Pinned)
                        samplePreviewer.IsVisible = false;
                });
            });

            tmrSliderToolTip = new DispatcherTimer { Interval = TimeSpan.FromSeconds(1) };
            tmrSliderToolTip.Tick += (o, e) =>
            {
                ToolTip.SetIsOpen(tkInScreen, false);
                tmrSliderToolTip.Stop();
            };

            this.Closed += (o, e) =>
            {
                if (driver != null && driver.IsCapturing)
                {
                    driver.StopCapture();
                    driver.Dispose();
                }

                if(decoderProvider != null)
                    decoderProvider.Dispose();
            };

            sampleDisplays.Add(sampleViewer);
            sampleDisplays.Add(samplePreviewer);
            sampleDisplays.Add(annotationsViewer);
            sampleDisplays.Add(sampleMarker);

            markerDisplays.Add(sampleViewer);
            markerDisplays.Add(annotationsViewer);

            regionDisplays.Add(sampleViewer);
            regionDisplays.Add(sampleMarker);
            regionDisplays.Add(annotationsViewer);

             Task.Run(() => LoadKnownDevices());

            RefreshPorts();
            LoadProfiles();

            generalSettings = AppSettingsManager.GetSettings<GeneralSettings>("GeneralSettings.json") ?? new GeneralSettings();
            tkInScreen.Minimum = generalSettings.MinSamples;
            tkInScreen.Maximum = generalSettings.MaxSamples;
            lblMinSamples.Text = generalSettings.MinSamples.ToString();
            lblMaxSamples.Text = generalSettings.MaxSamples.ToString();
            if (tkInScreen.Value < tkInScreen.Minimum)
                tkInScreen.Value = tkInScreen.Minimum;
            if (tkInScreen.Value > tkInScreen.Maximum)
                tkInScreen.Value = tkInScreen.Maximum;

            try
            {
                decoderProvider = new SigrokProvider();
                sgManager.Initialize(decoderProvider);
                sgManager.DecodingComplete += SgManager_DecodingComplete;
            }
            catch (Exception ex)
            {
                _ = this.ShowError("Error loading decoders.", "Cannot load Sigrok decoders. Make sure Python is installed on your computer. If, despite being installed, you still have problems, you can specify the path to the Python library in \"python.cfg\".");
            }
        }

        private void LoadProfiles()
        {
            mnuProfiles.Items.Clear();

            var addProfile = new MenuItem { Header = "Add profile" };
            addProfile.Click += AddProfile_Click;
            mnuProfiles.Items.Add(addProfile);
            mnuProfiles.Items.Add(new Separator());

            profiles = AppSettingsManager.GetSettings<ProfilesSet>("profiles.json");

            if (profiles != null)
            {
                foreach(var profile in profiles.Profiles)
                {
                    var mnuProfile = new MenuItem { Header = profile.Name };
                    mnuProfiles.Items.Add(mnuProfile);

                    var mnuLoad = new MenuItem { Header = "Load profile" };
                    mnuLoad.Tag = profile;
                    mnuLoad.Click += MnuLoad_Click;
                    mnuProfile.Items.Add(mnuLoad);

                    var mnuDelete = new MenuItem { Header = "Delete profile" };
                    mnuDelete.Tag = profile;
                    mnuDelete.Click += MnuDelete_Click;
                    mnuProfile.Items.Add(mnuDelete);
                }

            }
        }

        private void SaveProfiles()
        {
            AppSettingsManager.PersistSettings("profiles.json", profiles ?? new ProfilesSet());
        }

        private async void MnuDelete_Click(object? sender, RoutedEventArgs e)
        {

            var profile = (sender as MenuItem)?.Tag as Profile;

            if (profile == null)
                return;

            if (await this.ShowConfirm("Delete profile", $"Are you sure you want to delete the profile \"{profile.Name}\"?"))
            {
                profiles?.Profiles.Remove(profile);
                SaveProfiles();
                LoadProfiles();
            }
        }

        private async void MnuLoad_Click(object? sender, RoutedEventArgs e)
        {

            if (driver == null)
            {
                await this.ShowError("Load profile", "No device connected, cannot load profile.");
                return;
            }

            var mnu = sender as MenuItem;

            if (mnu == null)
                return;

            var profile = mnu.Tag as Profile;

            if (profile == null)
                return;

            if (driver.IsCapturing)
            {
                if (! await this.ShowConfirm("Load profile", "There is a capture in progress. Do you want to stop it and load the profile?"))
                    return;

                driver.StopCapture();
            }

            session = profile.CaptureSettings ?? new CaptureSession();
            updateChannels(true);
            mnuSave.IsEnabled = false;
            mnuExport.IsEnabled = false;
            clearRegions();
            updateSamplesInDisplay(Math.Max(session.PreTriggerSamples - 10, 0), (int)tkInScreen.Value);
            LoadInfo();

            var settingsFile = $"cpSettings{driver.DriverType}.json";
            var settings = session.Clone();

            foreach (var channel in settings.CaptureChannels)
                channel.Samples = null;

            AppSettingsManager.PersistSettings(settingsFile, settings);

            sgManager.DecodingTree = profile.DecoderConfiguration ?? new SerializableDecodingTree();
        }

        private async void AddProfile_Click(object? sender, RoutedEventArgs e)
        {
            var dlg = MessageBoxManager.GetMessageBoxCustom(new MsBox.Avalonia.Dto.MessageBoxCustomParams
            {
                ButtonDefinitions = new List<MsBox.Avalonia.Models.ButtonDefinition>
                {
                    new MsBox.Avalonia.Models.ButtonDefinition { Name = "Cancel", IsCancel = true, IsDefault = false },
                    new MsBox.Avalonia.Models.ButtonDefinition { Name = "Save", IsCancel = false, IsDefault = true }
                },
                InputParams = new MsBox.Avalonia.Dto.InputParams
                {
                    Label = "New profile name:", Multiline = false
                },
                Icon = MsBox.Avalonia.Enums.Icon.Setting,
                ContentTitle = "Add profile",
                ContentMessage = "Enter the name for the new profile.",
                Width = 400,
                ShowInCenter = true,
                WindowStartupLocation = WindowStartupLocation.CenterOwner
            });

            var result = await dlg.ShowWindowDialogAsync(this);

            if(result == "Save")
            {
                var profileName = dlg.InputValue;

                if (string.IsNullOrWhiteSpace(profileName))
                    return;

                if (profiles == null)
                    profiles = new ProfilesSet();

                var profile = new Profile
                {
                    Name = profileName,
                    CaptureSettings = session?.CloneSettings(),
                    DecoderConfiguration = sgManager.DecodingTree
                };

                profiles.Profiles.Add(profile);
                SaveProfiles();
                LoadProfiles();
            }
        }

        private async void LblForget_PointerPressed(object? sender, PointerPressedEventArgs e)
        {
            if(currentKnownDevice != null)
            {

                if (await this.ShowConfirm("Forget device", "Are you sure you want to forget this device?"))
                {

                    knownDevices.Remove(currentKnownDevice);
                    currentKnownDevice = null;
                    AppSettingsManager.PersistSettings("knownDevices.json", knownDevices);
                    lblForget.IsVisible = false;

                    if (driver != null)
                        btnOpenClose_Click(sender, e);
                }
            }
        }

        private void LoadKnownDevices()
        {
            var knownDevices = AppSettingsManager.GetSettings<List<KnownDevice>>("knownDevices.json");

            if(knownDevices != null)
                this.knownDevices = knownDevices;
        }

        private async void LblBootloader_PointerPressed(object? sender, PointerPressedEventArgs e)
        {
            if (driver != null && !driver.IsCapturing)
            {

                if (await this.ShowConfirm("Bootloader", "Are you sure you want to put the device in bootloader mode?"))
                {

                    if (driver.EnterBootloader())
                    {
                        driver.Dispose();
                        driver = null;
                        syncUI();
                        await this.ShowInfo("Bootloader", "Device entered bootloader mode.");
                    }
                    else
                    {
                        await this.ShowError("Bootloader", "Error entering bootloader mode. Device may need to be disconnected.");
                    }
                }
            }
        }

        private async void LblInfo_PointerPressed(object? sender, PointerPressedEventArgs e)
        {
            if(driver != null)
            {
                var dlg = new AnalyzerInfoDialog();
                dlg.Initialize(driver);
                await dlg.ShowDialog(this);

                if (RuntimeInformation.IsOSPlatform(OSPlatform.Linux) || RuntimeInformation.IsOSPlatform(OSPlatform.OSX))
                    e.Pointer.Capture(null);
            }
        }

        private void ScrSamplePos_PointerWheelChanged(object? sender, PointerWheelEventArgs e)
        {
            if(e.Delta.Y < 0)
            {
                var currentVal = scrSamplePos.Value;
                int newVal = (int)(currentVal - scrSamplePos.Maximum / 20);

                if (newVal < 0)
                    newVal = 0;

                updateSamplesInDisplay(newVal, (int)tkInScreen.Value);
            }
            else if (e.Delta.Y > 0)
            {
                var currentVal = scrSamplePos.Value;
                int newVal = (int)(currentVal + scrSamplePos.Maximum / 20);

                if (newVal > scrSamplePos.Maximum)
                    newVal = (int)scrSamplePos.Maximum;

                updateSamplesInDisplay(newVal, (int)tkInScreen.Value);
            }
        }

        private void SampleViewer_PointerWheelChanged(object? sender, PointerWheelEventArgs e)
        {
            if (e.KeyModifiers == KeyModifiers.Control)
            {
                e.Handled = true;

                if (e.Delta.Y < 0)
                {
                    var currentVal = tkInScreen.Value;
                    int newVal = (int)currentVal * 2;

                    if (newVal > tkInScreen.Maximum)
                        newVal = (int)tkInScreen.Maximum;


                    updateSamplesInDisplay((int)scrSamplePos.Value, newVal);
                }
                else if (e.Delta.Y > 0)
                {
                    var currentVal = tkInScreen.Value;
                    int newVal = (int)currentVal / 2;

                    if (newVal < tkInScreen.Minimum)
                        newVal = (int)tkInScreen.Minimum;

                    updateSamplesInDisplay((int)scrSamplePos.Value, newVal);
                }
            }
            else if (e.KeyModifiers == KeyModifiers.Shift)
            {
                e.Handled = true;

                if (e.Delta.Y < 0)
                {
                    var increment = tkInScreen.Value / 4.0;
                    var currentValue = scrSamplePos.Value;
                    currentValue += (int)increment;

                    if(currentValue > scrSamplePos.Maximum)
                        currentValue = (int)scrSamplePos.Maximum;

                    updateSamplesInDisplay((int)currentValue, (int)tkInScreen.Value);
                }
                else if (e.Delta.Y > 0)
                {
                    var increment = tkInScreen.Value / 4.0;
                    var currentValue = scrSamplePos.Value;
                    currentValue -= (int)increment;

                    if (currentValue < 0)
                        currentValue = 0;

                    updateSamplesInDisplay((int)currentValue, (int)tkInScreen.Value);
                }
            }
        }

        private void SamplePreviewer_PinnedChanged(object? sender, SamplePreviewer.PinnedEventArgs e)
        {
            if (e.Pinned)
            {
                tmrHideSamples.Change(Timeout.Infinite, Timeout.Infinite);
                samplePreviewer.IsVisible = true;
                grdContent.Margin = new Thickness(0, 0, 0, samplePreviewer.Bounds.Height);

                if (samplePreviewer.Bounds.Height == 0)
                {
                    grdContent.Margin = new Thickness(0, 0, 0, samplePreviewer.Height);
                }

            }
            else
            {
                tmrHideSamples.Change(Timeout.Infinite, Timeout.Infinite);
                samplePreviewer.IsVisible = false;
                grdContent.Margin = new Thickness(0);
            }
        }

        private void SamplePreviewer_ViewChanged(object? sender, SamplePreviewer.ViewChangedEventArgs e)
        {
            updateSamplesInDisplay(e.FirstSample, (int)tkInScreen.Value);
        }

        private void ChannelViewer_ChannelVisibilityChanged(object? sender, EventArgs e)
        {
            UpdateVisibility();
        }

        private void Visibility_PointerPressed(object? sender, PointerPressedEventArgs e)
        {
            if(session?.CaptureChannels == null)
                return;

            foreach(var channel in session.CaptureChannels)
                channel.Hidden = false;

            UpdateVisibility();
        }

        private void UpdateVisibility()
        {
            channelViewer.UpdateChannelVisibility();
            sampleViewer.InvalidateVisual();
        }

        private void TkInScreen_PointerWheelChanged(object? sender, PointerWheelEventArgs e)
        {
            if (e.Delta.Y > 0)
            {
                tkInScreen.Value = Math.Min(tkInScreen.Maximum, tkInScreen.Value * 1.5);
            }
            else if(e.Delta.Y < 0)
            {
                tkInScreen.Value = Math.Max(tkInScreen.Minimum, tkInScreen.Value / 1.5);
            }
        }

        private void SgManager_DecodingComplete(object? sender, SigrokDecoderManager.DecodingEventArgs e)
        {
            annotationsViewer.BeginUpdate();

            annotationsViewer.ClearAnnotations();

            if (e.Annotations != null && e.Annotations.Any())
            {


                foreach(var grp in e.Annotations)
                {
                    annotationsViewer.AddAnnotationsGroup(grp);
                }


            }

            annotationsViewer.EndUpdate();
        }

        private async void ChannelViewer_ChannelClick(object? sender, ChannelEventArgs e)
        {

            var txt = sender as TextBlock;

            if (txt == null)
                return;

            var chan = e.Channel;

            if (chan == null)
                return;

            var picker = new ColorPickerDialog();

            if (chan.ChannelColor != null)
                picker.PickerColor = Color.FromUInt32(chan.ChannelColor.Value);
            else
                picker.PickerColor = AnalyzerColors.GetColor(chan.ChannelNumber);

            var color = await picker.ShowDialog<Color?>(this);

            if (color == null)
                return;

            chan.ChannelColor = color.Value.ToUInt32();
            txt.Foreground = GraphicObjectsCache.GetBrush(color.Value);
            samplePreviewer.UpdateSamples(channelViewer.Channels, session.TotalSamples);
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
                            var maxVal = sampleViewer.VisibleSamples;
                            int newVal = (int)currentVal - (maxVal / 10);

                            if (newVal < 0)
                                newVal = 0;

                            updateSamplesInDisplay(newVal, (int)tkInScreen.Value);
                        }
                        break;
                    case Key.Right:
                        {
                            var currentVal = scrSamplePos.Value;
                            var maxVal = sampleViewer.VisibleSamples;
                            int newVal = (int)currentVal + (maxVal / 10);

                            if (newVal > scrSamplePos.Maximum)
                                newVal = (int)scrSamplePos.Maximum;

                            updateSamplesInDisplay(newVal, (int)tkInScreen.Value);
                        }
                        break;
                    case Key.Down:
                        {
                            var currentVal = scrSamplePos.Value;
                            var maxVal = sampleViewer.VisibleSamples;
                            int newVal = (int)currentVal - maxVal;

                            if (newVal < 0)
                                newVal = 0;

                            updateSamplesInDisplay(newVal, (int)tkInScreen.Value);
                        }
                        break;
                    case Key.Up:
                        {
                            var currentVal = scrSamplePos.Value;
                            var maxVal = sampleViewer.VisibleSamples;
                            int newVal = (int)currentVal + maxVal;

                            if (newVal > scrSamplePos.Maximum)
                                newVal = (int)scrSamplePos.Maximum;

                            updateSamplesInDisplay(newVal, (int)tkInScreen.Value);
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

                            updateSamplesInDisplay(newVal, (int)tkInScreen.Value);
                        }
                        break;
                    case Key.Right:
                        {
                            var currentVal = scrSamplePos.Value;
                            int newVal = (int)currentVal + 1;

                            if (newVal > scrSamplePos.Maximum)
                                newVal = (int)scrSamplePos.Maximum;

                            updateSamplesInDisplay(newVal, (int)tkInScreen.Value);
                        }
                        break;

                }

            }
        }

        private async void SampleMarker_ShiftSamples(object? sender, EventArgs e)
        {
            var dlg = new ShiftChannelsDialog();
            dlg.Initialize(channelViewer.Channels, session.TotalSamples - 1);

            if (await dlg.ShowDialog<bool>(this))
            {
                foreach (var channel in dlg.ShiftedChannels)
                {
                    var samples = channel.Samples;

                    if(samples == null)
                        continue;

                    int idx = Array.IndexOf(channelViewer.Channels, channel);

                    List<byte> shiftedSamples = new List<byte>();

                    if (dlg.ShiftDirection == ShiftDirection.Left)
                    {
                        shiftedSamples.AddRange(samples.Skip(dlg.ShiftAmmount));

                        if (dlg.ShiftMode == ShiftMode.Low)
                            shiftedSamples.AddRange(Enumerable.Range(0, dlg.ShiftAmmount).Select(c => (byte)0));
                        else if (dlg.ShiftMode == ShiftMode.High)
                            shiftedSamples.AddRange(Enumerable.Range(0, dlg.ShiftAmmount).Select(c => (byte)1));
                        else
                            shiftedSamples.AddRange(samples.Take(dlg.ShiftAmmount));
                    }
                    else
                    {
                        if (dlg.ShiftMode == ShiftMode.Low)
                            shiftedSamples.AddRange(Enumerable.Range(0, dlg.ShiftAmmount).Select(c => (byte)0));
                        else if (dlg.ShiftMode == ShiftMode.High)
                            shiftedSamples.AddRange(Enumerable.Range(0, dlg.ShiftAmmount).Select(c => (byte)1));
                        else
                            shiftedSamples.AddRange(samples.Skip(samples.Length - dlg.ShiftAmmount));

                        shiftedSamples.AddRange(samples.Take(samples.Length - dlg.ShiftAmmount));
                    }

                    channel.Samples = shiftedSamples.ToArray();
                }

                sampleViewer.BeginUpdate();
                sampleViewer.EndUpdate();
                samplePreviewer.UpdateSamples(channelViewer.Channels, session.TotalSamples);
                samplePreviewer.ViewPosition = sampleViewer.FirstSample;
            }
        }

        private async void MnuNew_Click(object? sender, RoutedEventArgs e)
        {
            var dlg = new CaptureDialog();
            var drv = new EmulatedAnalyzerDriver(5);
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

                var samples = await dlgCreate.ShowDialog<byte[][]?>(this);

                if (samples == null)
                    return;

                session = stn;
                driver = drv;

                for (int chan = 0; chan < stn.CaptureChannels.Length; chan++)
                    stn.CaptureChannels[chan].Samples = samples[chan];

                updateChannels();

                scrSamplePos.Maximum = samples.Length - 1;
                updateSamplesInDisplay(sampleViewer.FirstSample, sampleViewer.VisibleSamples);

                mnuSave.IsEnabled = true;
                mnuExport.IsEnabled = true;

                clearRegions();

                updateSamplesInDisplay(Math.Max(session.PreTriggerSamples - 10, 0), Math.Min(100, samples.Length / 10));

                LoadInfo();
            }
        }

        private async void SampleMarker_SamplesPasted(object? sender, SampleEventArgs e)
        {
            if (e.Sample > session.TotalSamples)
            {
                await this.ShowError("Out of range", "Cannot paste samples beyond the end of the sample range.");
                return;
            }

            if(copiedSamples != null)
                await InsertSamples(e.Sample, copiedSamples);
        }

        private async void SampleMarker_SamplesInserted(object? sender, SampleEventArgs e)
        {

            if (driver == null)
                return;

            if (e.Sample > session.TotalSamples)
            {
                await this.ShowError("Out of range", "Cannot insert samples beyond the end of the sample range.");
                return;
            }

            var channels = session.CaptureChannels.Select(c => c.ChannelNumber).ToArray();
            var names = session.CaptureChannels.Select(c => c.ChannelName).ToArray();

            var dlgCreate = new CreateSamplesDialog();
            dlgCreate.InsertMode = true;
            dlgCreate.Initialize(
                channels,
                names,
                driver.GetLimits(channels).MaxTotalSamples - session.TotalSamples,
                10);

            var samples = await dlgCreate.ShowDialog<byte[][]?>(this);

            if (samples == null)
                return;

            await InsertSamples(e.Sample, samples);

        }

        private async Task InsertSamples(int sample, IEnumerable<byte[]> newSamples)
        {

            if (driver == null)
                return;

            var chans = session.CaptureChannels.Select(c => c.ChannelNumber).ToArray();
            var maxSamples = driver.GetLimits(chans).MaxTotalSamples;

            int nCount = newSamples.First().Count();

            int total = session.TotalSamples + nCount;

            if (session.TotalSamples + newSamples.First().Length > maxSamples)
            {
                await this.ShowError("Error", $"Total samples exceed the maximum permitted for this mode ({maxSamples}).");
                return;
            }

            for(int chan = 0; chan < session.CaptureChannels.Length; chan++)
            {
                var channel = session.CaptureChannels[chan];
                var cSamples = channel.Samples;

                if (cSamples == null)
                    continue;

                List<byte> nsList = new List<byte>();
                nsList.AddRange(cSamples.Take(sample));
                nsList.AddRange(newSamples.Skip(chan).First());
                nsList.AddRange(cSamples.Skip(sample));
                channel.Samples = nsList.ToArray();
            }

            var regions = sampleViewer.Regions;
            List<SampleRegion> finalRegions = new List<SampleRegion>();

            int preSamples = sample <= session.PreTriggerSamples ? session.PreTriggerSamples + nCount : session.PreTriggerSamples;

            foreach (var region in regions)
            {
                int minRegion = Math.Min(region.FirstSample, region.LastSample);
                int maxRegion = Math.Max(region.FirstSample, region.LastSample);

                if (minRegion < sample && maxRegion >= sample)
                    region.LastSample += nCount;
                else if (maxRegion > sample)
                {
                    region.FirstSample += nCount;
                    region.LastSample += nCount;
                }

                finalRegions.Add(region);
            }

            UpdateSamples(sample, total, preSamples, finalRegions);
        }

        private async void SampleMarker_SamplesCopied(object? sender, SamplesEventArgs e)
        {
            if (e.FirstSample + e.SampleCount > session.TotalSamples)
            {
                await this.ShowError("Out of range", "Selected range outside of the sample bounds.");
                return;
            }

            copiedSamples = session.CaptureChannels.Select(c => c.Samples.Skip(e.FirstSample).Take(e.SampleCount).ToArray());
        }

        private async void SampleMarker_SamplesCutted(object? sender, SamplesEventArgs e)
        {
            if (e.FirstSample + e.SampleCount > session.TotalSamples)
            {
                await this.ShowError("Out of range", "Selected range outside of the sample bounds.");
                return;
            }

            copiedSamples = session.CaptureChannels.Select(c => c.Samples.Skip(e.FirstSample).Take(e.SampleCount).ToArray());
            DeleteSamples(e);
        }

        private async void SampleMarker_SamplesDeleted(object? sender, SamplesEventArgs e)
        {
            if (e.FirstSample >= session.TotalSamples)
            {
                await this.ShowError("Out of range", "Selected range outside of the sample bounds.");
                return;
            }

            DeleteSamples(e);
        }

        void DeleteSamples(SamplesEventArgs e)
        {
            var lastSample = e.FirstSample + e.SampleCount - 1;
            var triggerSample = sampleViewer.PreSamples - 1;

            int nCount = session.TotalSamples - (e.SampleCount + 1); //+1?

            for (int chan = 0; chan < session.CaptureChannels.Length; chan++)
            {
                var channel = session.CaptureChannels[chan];
                var cSamples = channel.Samples;

                if (cSamples == null)
                    continue;

                List<byte> finalSamples = new List<byte>();
                finalSamples.AddRange(cSamples.Take(e.FirstSample));
                finalSamples.AddRange(cSamples.Skip(e.FirstSample + e.SampleCount + 1));
                channel.Samples = finalSamples.ToArray();
            }

            var finalPreSamples = e.FirstSample > triggerSample ? session.PreTriggerSamples : session.PreTriggerSamples - e.SampleCount;

            var regions = sampleViewer.Regions;
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

            UpdateSamples(e.FirstSample, nCount, finalPreSamples, finalRegions);
        }

        private void UpdateSamples(int firstSample, int totalSamples, int finalPreSamples, List<SampleRegion> finalRegions)
        {
            session.PreTriggerSamples = finalPreSamples;
            session.PostTriggerSamples = totalSamples - finalPreSamples;
            session.Bursts = null;
            session.MeasureBursts = false;

            sampleViewer.BeginUpdate();
            //sampleViewer.PreSamples = 0;
            sampleViewer.Bursts = null;
            sampleViewer.EndUpdate();

            samplePreviewer.UpdateSamples(channelViewer.Channels, session.TotalSamples);
            sampleViewer.SetChannels(channelViewer.Channels, session.Frequency);
            //samplePreviewer.ViewPosition = firstSample;

            clearRegions();

            if (finalRegions.Count > 0)
                addRegions(finalRegions);



            scrSamplePos.Maximum = totalSamples - 1;
            updateSamplesInDisplay(firstSample - 1, (int)tkInScreen.Value);

        }

        private void SampleMarker_UserMarkerSelected(object? sender, UserMarkerEventArgs e)
        {
            if (e.Position > session.TotalSamples)
                return;

            updateUserMarkers(e.Position);
        }

        private async void SampleMarker_MeasureSamples(object? sender, SamplesEventArgs e)
        {
            if (e.FirstSample + e.SampleCount > session.TotalSamples)
            {
                await this.ShowError("Out of range", "Selected range outside of the sample bounds.");
                return;
            }

            var names = channelViewer.Channels.Select(c => c.ChannelName).ToArray();

            for (int buc = 0; buc < names.Length; buc++)
                if (string.IsNullOrWhiteSpace(names[buc]))
                    names[buc] = (buc + 1).ToString();

            MeasureDialog dlg = new MeasureDialog();
            dlg.SetData(names, session.CaptureChannels.Select(c => c.Samples != null ? c.Samples.Skip(e.FirstSample).Take(e.SampleCount).ToArray() : new byte[0]), session.Frequency);
            await dlg.ShowDialog(this);

        }

        private async void MnuNetSettings_Click(object? sender, RoutedEventArgs e)
        {

            if (driver == null)
                return;

            var dlg = new NetworkSettingsDialog();

            if (await dlg.ShowDialog<bool>(this))
            {
                bool res = false;
                try
                {
                    res = driver.SendNetworkConfig(dlg.AccessPoint, dlg.Password, dlg.Address, dlg.Port);
                }
                catch { }

                if (!res)
                    await this.ShowError("Error", "Error updating network settings, restart the device and try again.");
                else
                    await this.ShowInfo("Updated", "Network settings updated successfully.");
            }
        }

        private async void MnuGeneralSettings_Click(object? sender, RoutedEventArgs e)
        {
            // some defaults when not connected to a device
            int minSamples = 1;
            int maxSamples = 10000;

            if (driver != null)
            {
                var channels = session?.CaptureChannels?.Select(c => (int)c.ChannelNumber).ToArray() ?? Enumerable.Range(0, driver.ChannelCount).ToArray();
                var limits = driver.GetLimits(channels);
                minSamples = limits.MinPreSamples + limits.MinPostSamples;
                maxSamples = limits.MaxPreSamples + limits.MaxPostSamples;
            }

            var dlg = new GeneralSettingsDialog
            {
                MinSamples = generalSettings.MinSamples,
                MaxSamples = generalSettings.MaxSamples,
                MinSamplesLimit = minSamples,
                MaxSamplesLimit = maxSamples
            };

            if (await dlg.ShowDialog<bool>(this))
            {
                generalSettings.MinSamples = dlg.MinSamples;
                generalSettings.MaxSamples = dlg.MaxSamples;
                AppSettingsManager.PersistSettings("GeneralSettings.json", generalSettings);
                tkInScreen.Minimum = generalSettings.MinSamples;
                tkInScreen.Maximum = generalSettings.MaxSamples;
                lblMinSamples.Text = generalSettings.MinSamples.ToString();
                lblMaxSamples.Text = generalSettings.MaxSamples.ToString();
                if (tkInScreen.Value < tkInScreen.Minimum)
                    tkInScreen.Value = tkInScreen.Minimum;
                if (tkInScreen.Value > tkInScreen.Maximum)
                    tkInScreen.Value = tkInScreen.Maximum;
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

                    for (int sample = 0; sample < session.TotalSamples; sample++)
                    {
                        sb.Clear();

                        for (int buc = 0; buc < session.CaptureChannels.Length; buc++)
                            sb.Append($"{session.CaptureChannels[buc].Samples[sample]},");

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
            Dispatcher.UIThread.InvokeAsync(async () =>
            {
                clearRegions();

                if (!e.Success)
                {
                    await this.ShowError("Error", "Error capturing samples, try again and if the error persist restart the application and the device.");
                }

                updateChannels();

                sampleViewer.Bursts = session.Bursts?.Select(b => b.BurstSampleStart).ToArray();
                sampleMarker.Bursts = session.Bursts;

                syncUI();

                scrSamplePos.Maximum = session.TotalSamples - 1;
                updateSamplesInDisplay(session.PreTriggerSamples - 2, (int)tkInScreen.Value);

                LoadInfo();
                GetPowerStatus();
            });
        }

        private void ExtractSamples(AnalyzerChannel channel, int ChannelIndex, UInt128[]? samples)
        {
            if (channel == null || samples == null)
                return;

            UInt128 mask = (UInt128)1 << ChannelIndex;
            channel.Samples = samples.Select(s => (s & mask) != 0 ? (byte)1 : (byte)0).ToArray();
        }

        private async void btnOpenClose_Click(object? sender, EventArgs e)
        {
            if (driver == null || driver is EmulatedAnalyzerDriver)
            {
                if (ddPorts.SelectedIndex == -1)
                {
                    await this.ShowError("Error", "Select a serial port to connect.");
                    return;
                }

                try
                {
                    var port = ddPorts.SelectedItem as PortItem;

                    if (port == null)
                        return;

                    switch(port.Port)
                    {
                        case "Autodetect":
                            driver = await BeginAutodetect();
                            break;
                        case "Network":
                            driver = await BeginNetwork();
                            break;
                        case "Multidevice":
                            driver = await BeginMultidevice();
                            break;
                        default:
                            driver = await BeginSerial(port.Port);
                            break;

                    }
                }
                catch(Exception ex)
                {
                    await this.ShowError("Error", $"Cannot connect to device: ({ex.Message}).");
                    return;
                }

                if (driver != null)
                {
                    driver.CaptureCompleted += Driver_CaptureCompleted;
                    var settingsFile = $"cpSettings{driver.DriverType}.json";
                    session = AppSettingsManager.GetSettings<CaptureSession>(settingsFile) ?? new CaptureSession();
                    updateChannels(true);
                    LoadInfo();
                    syncUI();
                }


            }
            else
            {
                driver.Dispose();
                driver = null;
                currentKnownDevice = null;
                syncUI();
            }

            GetPowerStatus();
        }

        private async Task<AnalyzerDriverBase?> BeginSerial(string port)
        {
            try
            {
                return new LogicAnalyzerDriver(port);
            }
            catch (Exception ex)
            {
                await this.ShowError("Error", $"Cannot connect to device: ({ex.Message}).");
                return null;
            }
        }

        private async Task<AnalyzerDriverBase?> BeginMultidevice()
        {
            try
            {
                MultiConnectDialog dlg = new MultiConnectDialog();

                if (!await dlg.ShowDialog<bool>(this) || dlg.ConnectionStrings == null)
                    return null;

                return new MultiAnalyzerDriver(dlg.ConnectionStrings);
            }
            catch (Exception ex)
            {
                await this.ShowError("Error", $"Cannot connect to device: ({ex.Message}).");
                return null;
            }
        }

        private async Task<AnalyzerDriverBase?> BeginNetwork()
        {
            try
            {
                NetworkDialog dlg = new NetworkDialog();
                if (!await dlg.ShowDialog<bool>(this))
                    return null;

                return new LogicAnalyzerDriver(dlg.Address + ":" + dlg.Port);
            }
            catch (Exception ex)
            {
                await this.ShowError("Error", $"Cannot connect to device: ({ex.Message}).");
                return null;
            }
        }

        private async Task<AnalyzerDriverBase?> BeginAutodetect()
        {
            var detected = DeviceDetector.Detect();

            if (detected.Length == 0)
            {
                await this.ShowError("Error", "No devices detected.");
                return null;
            }

            if (detected.Length > 0)
            {
                if (detected.Length == 1)
                {
                    return new LogicAnalyzerDriver(detected[0].PortName);
                }
                else
                {
                    KnownDevice? knownDevice = GetKnownDevice(detected);

                    if (knownDevice != null)
                    {
                        currentKnownDevice = knownDevice;
                        lblForget.IsVisible = true;
                        return new MultiAnalyzerDriver(detected
                            .OrderBy(d => knownDevice.Entries.First(e => e.SerialNumber == d.SerialNumber).Order)
                            .Select(d => d.PortName)
                            .ToArray());
                    }
                    else
                    {

                        if (await this.ShowConfirm("Multiple devices", "A new set of analyzers has been detected, do you want to register them as a multianalizer?"))
                        {
                            var dlg = new MultiComposeDialog();
                            dlg.Devices = detected;
                            var result = await dlg.ShowDialog<bool?>(this);

                            if (result == true && dlg.ComposedDevice != null)
                            {
                                var cdev = dlg.ComposedDevice;
                                StoreKnownDevice(cdev);
                                currentKnownDevice = cdev;
                                lblForget.IsVisible = true;
                                return new MultiAnalyzerDriver(detected
                                    .OrderBy(d => dlg.ComposedDevice.Entries.First(e => e.SerialNumber == d.SerialNumber).Order)
                                    .Select(d => d.PortName)
                                    .ToArray());

                            }
                            else
                                return null;
                        }
                        else
                            return null;
                    }
                }
            }
            else
            {
                await this.ShowInfo("No device", "No devices detected, try to select the device manually.");
                return null;
            }
        }

        private void StoreKnownDevice(KnownDevice cdev)
        {
            knownDevices.Add(cdev);
            AppSettingsManager.PersistSettings("knownDevices.json", knownDevices);
        }

        private KnownDevice? GetKnownDevice(DetectedDevice[] detected)
        {
            var device = knownDevices.FirstOrDefault(d => d.Entries.Length == detected.Length &&
            d.Entries.All(e =>
            detected.Any(dd => dd.SerialNumber == e.SerialNumber)));

            return device;
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

                using var str = AssetLoader.Open(new Uri(parts[1] == "1" ? "avares://LogicAnalyzer/Assets/plug.png" : "avares://LogicAnalyzer/Assets/battery.png"));
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

            var devices = DeviceDetector.Detect();
            var ports = SerialPort.GetPortNames().ToList();

            List<PortItem> portItems = new List<PortItem>();

            if (RuntimeInformation.IsOSPlatform(OSPlatform.Windows) || RuntimeInformation.IsOSPlatform(OSPlatform.Linux))
                portItems.Add(new PortItem { Port = "Autodetect", Icon = "" });

            foreach (var port in ports)
            {
                var device = devices.FirstOrDefault(d => d.PortName.ToLower() == port.ToLower());

                if (device != null)
                    portItems.Add(new PortItem { Port = port, SerialNumber = device.SerialNumber, Icon = "" });
                else
                    portItems.Add(new PortItem { Port = port, Icon = "" });
            }

            portItems.Add(new PortItem { Port = "Network", Icon = "" });
            portItems.Add(new PortItem { Port = "Multidevice", Icon = "" });

            ddPorts.ItemsSource = null;
            ddPorts.ItemsSource = portItems.ToArray();
            ddPorts.SelectedIndex = 0;

        }

        private async void btnRepeat_Click(object? sender, RoutedEventArgs e)
        {
            if (session == null)
            {
                await this.ShowError("Error", "No capture to repeat");
                return;
            }

            if (!await BeginCapture())
                return;

            this.Title = Version;

            syncUI();
        }

        private async void btnCapture_Click(object? sender, RoutedEventArgs e)
        {
            if (driver == null)
                return;

            var dialog = new CaptureDialog();

            dialog.Initialize(driver);

            if (!await dialog.ShowDialog<bool>(this))
                return;

            session = dialog.SelectedSettings;

            if(!await BeginCapture())
                return;

            this.Title = Version;

            var settingsFile = $"cpSettings{driver.DriverType}.json";
            var settings = session.Clone();

            foreach(var channel in settings.CaptureChannels)
                channel.Samples = null;

            AppSettingsManager.PersistSettings(settingsFile, settings);

            syncUI();


        }

        private void btnAbort_Click(object? sender, RoutedEventArgs e)
        {
            driver?.StopCapture();

            syncUI();
        }

        private async Task<bool> BeginCapture()
        {
            if (driver == null)
                return false;

            var error = driver.StartCapture(session);

            if (error != CaptureError.None)
            {
                await ShowError(error);
                return false;
            }

            return true;
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
            tmrHideSamples.Change(2000, Timeout.Infinite);
        }
        private void ScrSamplePos_PointerEnter(object? sender, Avalonia.Input.PointerEventArgs e)
        {
            tmrHideSamples.Change(Timeout.Infinite, Timeout.Infinite);
            samplePreviewer.IsVisible = true;
        }
        private void scrSamplePos_ValueChanged(object? sender, ScrollEventArgs e)
        {
            updateSampleDisplays();
        }

        private void tkInScreen_ValueChanged(object? sender, Avalonia.AvaloniaPropertyChangedEventArgs e)
        {
            updateSampleDisplays();

            if (e.Property == RangeBase.ValueProperty)
            {
                ToolTip.SetIsOpen(tkInScreen, true);
                tmrSliderToolTip.Stop();
                tmrSliderToolTip.Start();
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

                    var sets = session.Clone();
                    //sets.PreTriggerSamples = sampleViewer.PreSamples;
                    //sets.LoopCount = sampleViewer.Bursts?.Length ?? 0;

                    ExportedCapture ex = new ExportedCapture { Settings = sets, SelectedRegions = sampleViewer.Regions };

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
                        return;

                    string fileName = Path.GetFileName(file);
                    this.Title = Version + " - " + fileName;

                    session = ex.Settings;

                    if (ex.Samples != null)
                    {
                        for(int buc = 0; buc < session.CaptureChannels.Length; buc++)
                            ExtractSamples(session.CaptureChannels[buc], buc, ex.Samples);
                    }

                    updateChannels();

                    mnuSave.IsEnabled = true;
                    mnuExport.IsEnabled = true;

                    if (driver != null)
                    {
                        btnOpenClose_Click(this, EventArgs.Empty);
                    }

                    driver = new EmulatedAnalyzerDriver(5);

                    clearRegions();

                    if (ex.SelectedRegions != null)
                        addRegions(ex.SelectedRegions);

                    scrSamplePos.Maximum = session.TotalSamples - 1;

                    updateSamplesInDisplay(Math.Max(session.PreTriggerSamples - 10, 0), (int)tkInScreen.Value);

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

            string triggerType = session.TriggerType.ToString();

            lblFreq.Text = String.Format("{0:n0}", session.Frequency) + " Hz";
            lblPreSamples.Text = String.Format("{0:n0}", session.PreTriggerSamples);
            lblPostSamples.Text = String.Format("{0:n0}", session.PostTriggerSamples);
            lblSamples.Text = String.Format("{0:n0}", session.TotalSamples);
            lblChannels.Text = session.CaptureChannels.Length.ToString();
            lblTrigger.Text = $"{triggerType}, channel {session.TriggerChannel + 1}";
            lblValue.Text = session.TriggerType == 0 ? (session.TriggerInverted ? "Negative" : "Positive") : GenerateStringTrigger(session.TriggerPattern, session.TriggerBitCount);
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
            if (e.Region == null)
                return;

            addRegion(e.Region);
        }

        private void sampleMarker_RegionDeleted(object? sender, RegionEventArgs e)
        {
            if (e.Region == null)
                return;

            removeRegion(e.Region);
        }

        private void updateUserMarkers(int? Position)
        {
            foreach (var display in markerDisplays)
                display.SetUserMarker(Position);
        }

        private void addRegions(IEnumerable<SampleRegion> regions)
        {
            foreach (var display in regionDisplays)
                display.AddRegions(regions);
        }

        private void clearRegions()
        {
            foreach (var display in regionDisplays)
                display.ClearRegions();
        }

        private void addRegion(SampleRegion region)
        {
            foreach (var display in regionDisplays)
                display.AddRegion(region);
        }

        private void removeRegion(SampleRegion region)
        {
            foreach (var display in regionDisplays)
                display.RemoveRegion(region);
        }

        private void updateSamplesInDisplay(int FirstSample, int VisibleSamples)
        {
            scrSamplePos.Value = FirstSample;
            tkInScreen.Value = VisibleSamples;
            updateSampleDisplays();
        }
        private void updateSampleDisplays()
        {
            foreach (var display in sampleDisplays)
                display.UpdateVisibleSamples((int)scrSamplePos.Value, (int)tkInScreen.Value);
        }

        private void updateChannels(bool ignoreSamples = false)
        {
            sampleViewer.BeginUpdate();
            sampleViewer.PreSamples = session.PreTriggerSamples;
            sampleViewer.SetChannels(session.CaptureChannels, session.Frequency);
            sampleViewer.EndUpdate();

            samplePreviewer.UpdateSamples(session.CaptureChannels, ignoreSamples ? 0 : session.TotalSamples);
            samplePreviewer.ViewPosition = sampleViewer.FirstSample;

            channelViewer.Channels = session.CaptureChannels;

            sgManager.SetChannels(session.Frequency, session.CaptureChannels);
        }

        private void syncUI()
        {
            bool hasDriver = driver != null && driver is not EmulatedAnalyzerDriver;
            bool isCapturing = hasDriver && driver!.IsCapturing;
            bool canCapture = hasDriver && !isCapturing;
            bool canConfigureWiFi = hasDriver && driver.DriverType == AnalyzerDriverType.Serial && (driver.DeviceVersion?.Contains("WIFI") ?? false);
            bool hasCapture = session != null && session.CaptureChannels?.FirstOrDefault()?.Samples?.Length == session.TotalSamples;

            btnOpenClose.IsEnabled = !isCapturing;
            btnRefresh.IsEnabled = !hasDriver;
            btnCapture.IsEnabled = canCapture;
            btnRepeat.IsEnabled = canCapture;
            btnAbort.IsEnabled = isCapturing;


            mnuProfiles.IsEnabled = hasDriver && !isCapturing;
            mnuSettings.IsEnabled = true;
            mnuNetSettings.IsEnabled = canConfigureWiFi;
            mnuSave.IsEnabled = hasCapture;
            mnuExport.IsEnabled = hasCapture;

            lblBootloader.IsVisible = hasDriver && !isCapturing;
            lblInfo.IsVisible = hasDriver;
            ddPorts.IsEnabled = !hasDriver;


            lblConnectedDevice.Text = driver?.DeviceVersion ?? "< None >";
            btnOpenClose.Content = hasDriver ? "Close device" : "Open device";

            if (!hasDriver)
                RefreshPorts();

            GetPowerStatus();
        }

        class PortItem
        {
            public string? Icon { get; set; }
            public required string Port { get; set; }
            public string? SerialNumber { get; set; }
        }
    }
}
