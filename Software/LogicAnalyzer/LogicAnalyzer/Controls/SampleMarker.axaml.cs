using Avalonia;
using Avalonia.Controls;
using Avalonia.Input;
using Avalonia.Markup.Xaml;
using Avalonia.Media;
using Avalonia.Threading;
using LogicAnalyzer.Classes;
using LogicAnalyzer.Dialogs;
using LogicAnalyzer.Protocols;
using System;
using System.Collections.Generic;
using System.Globalization;
using System.Linq;

namespace LogicAnalyzer.Controls
{
    public partial class SampleMarker : UserControl
    {

        public static readonly StyledProperty<int> FirstSampleProperty = AvaloniaProperty.Register<SampleMarker, int>(nameof(FirstSample));

        public static readonly StyledProperty<int> VisibleSamplesProperty = AvaloniaProperty.Register<SampleMarker, int>(nameof(VisibleSamples));

        public static readonly StyledProperty<IBrush> ForegroundProperty = AvaloniaProperty.Register<SampleMarker, IBrush>(nameof(Foreground));

        public static readonly StyledProperty<IBrush> BackgroundProperty = AvaloniaProperty.Register<SampleMarker, IBrush>(nameof(Background));

        public int FirstSample 
        { 
            get { return GetValue(FirstSampleProperty); } 
            set { SetValue(FirstSampleProperty, value); UpdateValues(); InvalidateVisual(); } 
        }

        public int VisibleSamples 
        { 
            get { return GetValue(VisibleSamplesProperty); } 
            set { SetValue(VisibleSamplesProperty, value); UpdateValues(); InvalidateVisual(); } 
        }

        public new IBrush Foreground
        {
            get { return GetValue<IBrush>(ForegroundProperty); }
            set { SetValue<IBrush>(ForegroundProperty, value); UpdateTextColors(); InvalidateVisual(); }
        }

        public new IBrush Background
        {
            get { return GetValue<IBrush>(BackgroundProperty); }
            set { SetValue<IBrush>(BackgroundProperty, value); InvalidateVisual(); }
        }

        public event EventHandler<RegionEventArgs> RegionCreated;
        public event EventHandler<RegionEventArgs> RegionDeleted;

        public event EventHandler<SamplesEventArgs> SamplesCutted;
        public event EventHandler<SamplesEventArgs> SamplesCopied;
        public event EventHandler<SampleEventArgs> SamplesPasted;
        public event EventHandler<SampleEventArgs> SamplesInserted;
        public event EventHandler<SamplesEventArgs> SamplesDeleted;
        public event EventHandler<SamplesEventArgs> MeasureSamples;
        public event EventHandler<UserMarkerEventArgs> UserMarkerSelected;
        public event EventHandler ShiftSamples;


        List<SampleRegion> regions = new List<SampleRegion>();
        List<ProtocolAnalyzedChannel> analysisData = new List<ProtocolAnalyzedChannel>();

        SelectedSamples? selectedSamples = null;
        SampleRegion? selectedRegion = null;

        int? userMarker = null;
        int mnuSample = 0;
        bool samplesCopied = false;
        bool updating = false;

        public SampleMarker()
        {
            InitializeComponent();
            mnuCut.Click += MnuCut_Click;
            mnuCopy.Click += MnuCopy_Click;
            mnuPaste.Click += MnuPaste_Click;
            mnuInsert.Click += MnuInsert_Click;
            mnuDelete.Click += MnuDelete_Click;
            mnuShift.Click += MnuShift_Click;
            mnuMeasure.Click += MnuMeasure_Click;
            mnuCreateRegion.Click += MnuCreateRegion_Click;
            mnuDeleteRegion.Click += MnuDeleteRegion_Click;
        }

        private void MnuShift_Click(object? sender, Avalonia.Interactivity.RoutedEventArgs e)
        {
            if(ShiftSamples != null) 
                ShiftSamples(sender, EventArgs.Empty);
        }

        private void MnuDeleteRegion_Click(object? sender, Avalonia.Interactivity.RoutedEventArgs e)
        {
            if (selectedRegion != null && RegionDeleted != null)
            {
                RegionDeleted(this, new RegionEventArgs { Region = selectedRegion });
                RemoveRegion(selectedRegion);
            }
        }

        private void MnuCreateRegion_Click(object? sender, Avalonia.Interactivity.RoutedEventArgs e)
        {
            if (selectedSamples != null && RegionCreated != null)
                CreateRegion();
        }

        private void MnuMeasure_Click(object? sender, Avalonia.Interactivity.RoutedEventArgs e)
        {
            if (MeasureSamples != null && selectedSamples != null)
                MeasureSamples(this, new SamplesEventArgs { FirstSample = selectedSamples.Start, SampleCount = selectedSamples.SampleCount });
        }

        private void MnuDelete_Click(object? sender, Avalonia.Interactivity.RoutedEventArgs e)
        {
            if (selectedSamples != null && SamplesDeleted != null)
            {
                SamplesDeleted(this, new SamplesEventArgs { FirstSample = selectedSamples.Start, SampleCount = selectedSamples.SampleCount });
                selectedSamples = null;
                this.InvalidateVisual();
            }
        }

        private void MnuInsert_Click(object? sender, Avalonia.Interactivity.RoutedEventArgs e)
        {
            if (SamplesInserted != null)
            {
                SamplesInserted(this, new SampleEventArgs { Sample = mnuSample });
                selectedSamples = null;
                this.InvalidateVisual();
            }
        }

        private void MnuPaste_Click(object? sender, Avalonia.Interactivity.RoutedEventArgs e)
        {
            if (samplesCopied && SamplesPasted != null)
            {
                SamplesPasted(this, new SampleEventArgs { Sample = mnuSample });
                selectedSamples = null;
                this.InvalidateVisual();
            }
        }

        private void MnuCopy_Click(object? sender, Avalonia.Interactivity.RoutedEventArgs e)
        {
            if (selectedSamples != null && SamplesCopied != null)
            {
                SamplesCopied(this, new SamplesEventArgs { FirstSample = selectedSamples.Start, SampleCount = selectedSamples.SampleCount });
                samplesCopied = true;
                selectedSamples= null;
                this.InvalidateVisual();
            }
        }

        private void MnuCut_Click(object? sender, Avalonia.Interactivity.RoutedEventArgs e)
        {
            if (selectedSamples != null && SamplesCutted != null)
            {
                SamplesCutted(this, new SamplesEventArgs { FirstSample = selectedSamples.Start, SampleCount = selectedSamples.SampleCount });
                samplesCopied = true;
                selectedSamples = null;
                this.InvalidateVisual();
            }
        }

        public void BeginUpdate()
        {
            updating = true;
        }

        public void EndUpdate()
        {
            updating = false;
            InvalidateVisual();
        }
        public void AddAnalyzedChannel(ProtocolAnalyzedChannel Data)
        {
            analysisData.Add(Data);
        }
        public void AddAnalyzedChannels(IEnumerable<ProtocolAnalyzedChannel> Data)
        {
            analysisData.AddRange(Data);
        }
        public bool RemoveAnalyzedChannel(ProtocolAnalyzedChannel Data)
        {
            return analysisData.Remove(Data);
        }

        public void ClearAnalyzedChannels()
        {
            foreach (var data in analysisData)
                data.Dispose();

            analysisData.Clear();
        }

        public void AddRegion(SampleRegion Region)
        {
            regions.Add(Region);
            this.InvalidateVisual();
        }
        public void AddRegions(IEnumerable<SampleRegion> Regions)
        {
            regions.AddRange(Regions);
        }
        public bool RemoveRegion(SampleRegion Region)
        {
            var res = regions.Remove(Region);
            if (res)
                this.InvalidateVisual();
            return res;
        }

        public void ClearRegions()
        {
            regions.Clear();
            this.InvalidateVisual();
        }

        void UpdateValues()
        {
            lblLeft.Text = FirstSample.ToString();
            lblCenter.Text = (FirstSample + VisibleSamples / 2).ToString();
            lblRight.Text = (FirstSample + VisibleSamples - 1).ToString();
        }

        void UpdateTextColors()
        {
            lblLeft.Foreground = Foreground;
            lblCenter.Foreground = Foreground;
            lblRight.Foreground = Foreground;
        }

        public override void Render(DrawingContext context)
        {

            var bounds = new Rect(0, 0, Bounds.Width, Bounds.Height);

            using (context.PushClip(bounds))
            {

                if(updating) 
                    return;

                context.FillRectangle(Background, bounds);

                if (VisibleSamples == 0)
                    return;

                double sampleWidth = this.Bounds.Width / VisibleSamples;
                double halfWidth = sampleWidth / 2;
                double halfHeight = this.Bounds.Height / 2f;


                if (selectedSamples != null)
                {
                    int first = selectedSamples.Start;
                    double start = (first - FirstSample) * sampleWidth;
                    double end = sampleWidth * selectedSamples.SampleCount;
                    context.FillRectangle(GraphicObjectsCache.GetBrush(Color.FromArgb(128, 255, 255, 255)), new Rect(start, 0, end, this.Bounds.Height));

                }

                if (regions.Count > 0)
                {
                    foreach (var region in regions)
                    {
                        int first = region.FirstSample;
                        double start = (first - FirstSample) * sampleWidth;
                        double end = sampleWidth * region.SampleCount;
                        context.FillRectangle(GraphicObjectsCache.GetBrush(region.RegionColor), new Rect(start, 0, end, this.Bounds.Height));
                        FormattedText text = new FormattedText(region.RegionName, Typeface.Default, 12, TextAlignment.Left, TextWrapping.NoWrap, Size.Infinity);
                        context.DrawText(GraphicObjectsCache.GetBrush(Colors.White), new Point(start + (end / 2) - (text.Bounds.Width / 2), 5), text);
                    }
                }

                int increment;

                if (VisibleSamples < 101)
                    increment = 1;
                else if (VisibleSamples < 501)
                    increment = 5;
                else if (VisibleSamples < 1001)
                    increment = 10;
                else
                    increment = 20;

                //Draw ticks
                for (int buc = 0; buc < VisibleSamples; buc += increment)
                {
                    double x = buc * sampleWidth;
                    double y1 = halfHeight * 1.5f;
                    double y2 = this.Bounds.Height;

                    context.DrawLine(GraphicObjectsCache.GetPen(Foreground, 1), new Point(x, y1), new Point(x, y2));

                    if (increment == 1)
                    {
                        x = buc * sampleWidth + halfWidth;
                        y1 = halfHeight * 1.75f;

                        context.DrawLine(GraphicObjectsCache.GetPen(Foreground, 1), new Point(x, y1), new Point(x, y2));

                    }

                }

                if (analysisData.Count > 0)
                {
                    foreach (var chan in analysisData)
                    {
                        foreach (var evt in chan.Segments)
                        {
                            double x1 = (evt.FirstSample - FirstSample) * sampleWidth;
                            double x2 = (evt.LastSample + 1 - FirstSample) * sampleWidth;
                            double y1 = 0;
                            double y2 = this.Bounds.Height;

                            Rect r = new Rect(new Point(x1, y1), new Point(x2, y2));
                            context.FillRectangle(GraphicObjectsCache.GetBrush(chan.BackColor), r);
                        }
                    }
                }

                base.Render(context);
            }
        }

        protected override void OnPointerMoved(PointerEventArgs e)
        {

            if (VisibleSamples == 0)
                ToolTip.SetIsOpen(this, false);
            else
            {
                double sampleWidth = this.Bounds.Width / (float)VisibleSamples;
                var pos = e.GetCurrentPoint(this);
                
                int ovrSample = (int)(pos.Position.X / sampleWidth) + FirstSample;

                if (pos.Properties.IsLeftButtonPressed && selectedSamples != null)
                {
                    selectedSamples.LastSample = ovrSample;
                    this.InvalidateVisual();
                }
                else
                {
                    if (ToolTip.GetTip(this)?.ToString() != ovrSample.ToString())
                    {
                        ToolTip.SetTip(this, ovrSample.ToString());
                        ToolTip.SetIsOpen(this, false);
                        ToolTip.SetShowDelay(this, 0);
                        ToolTip.SetIsOpen(this, true);
                    }
                }
            }

            base.OnPointerMoved(e);
        }
        protected override void OnPointerPressed(PointerPressedEventArgs e)
        {
            base.OnPointerPressed(e);

            if (VisibleSamples != 0)
            {
                var point = e.GetCurrentPoint(this);

                if (point.Properties.IsLeftButtonPressed)
                {
                    ToolTip.SetIsOpen(this, false);
                    double sampleWidth = this.Bounds.Width / (float)VisibleSamples;
                    var pos = e.GetCurrentPoint(this);

                    int ovrSample = (int)(pos.Position.X / sampleWidth) + FirstSample;

                    if(selectedSamples != null && e.KeyModifiers.HasFlag(KeyModifiers.Shift))
                        selectedSamples.LastSample = ovrSample;
                    else
                        selectedSamples = new SelectedSamples { FirstSample = ovrSample, LastSample = ovrSample };
                    this.InvalidateVisual();
                }
            }


        }

        protected override void OnPointerReleased(PointerReleasedEventArgs e)
        {
            base.OnPointerReleased(e);

            if (VisibleSamples != 0)
            {
                double sampleWidth = this.Bounds.Width / (float)VisibleSamples;
                var pos = e.GetCurrentPoint(this);

                int ovrSample = (int)(pos.Position.X / sampleWidth) + FirstSample;

                if (e.InitialPressMouseButton == MouseButton.Left)
                {
                    if (selectedSamples != null)
                    {
                        selectedSamples.LastSample = ovrSample;

                        if (selectedSamples.SampleCount == 0)
                        {
                            selectedSamples = null;

                            if (userMarker != null && userMarker == ovrSample)
                            {
                                userMarker = null;
                                if (this.UserMarkerSelected != null)
                                    this.UserMarkerSelected(this, new UserMarkerEventArgs { Position = null });
                                this.InvalidateVisual();
                                return;
                            }

                            if (e.KeyModifiers.HasFlag(KeyModifiers.Shift) && userMarker != null)
                            {
                                selectedSamples = new SelectedSamples { FirstSample = userMarker.Value, LastSample = ovrSample };
                                userMarker = null;
                                if (this.UserMarkerSelected != null)
                                    this.UserMarkerSelected(this, new UserMarkerEventArgs { Position = null });
                                this.InvalidateVisual();
                                return;
                            }

                            if (this.UserMarkerSelected != null)
                            {
                                this.UserMarkerSelected(this, new UserMarkerEventArgs { Position = ovrSample });
                                userMarker = ovrSample;
                                this.InvalidateVisual();
                                return;
                            }
                        }
                        else
                        {
                            if (userMarker != null)
                            {
                                userMarker = null;
                                if (this.UserMarkerSelected != null)
                                    this.UserMarkerSelected(this, new UserMarkerEventArgs { Position = null });
                                this.InvalidateVisual();
                                return;
                            }
                        }
                    }
                }
                else if(e.InitialPressMouseButton == MouseButton.Right) 
                {
                    selectedRegion = regions.FirstOrDefault(r => r.FirstSample <= ovrSample && r.LastSample >= ovrSample);
                    mnuSample = ovrSample;
                    ShowSampleMenu(pos);
                }
            }
        }

        private void ShowSampleMenu(PointerPoint pos)
        {
            if (selectedRegion != null)
                mnuDeleteRegion.IsEnabled = true;
            else
                mnuDeleteRegion.IsEnabled = false;

            if (selectedSamples != null && selectedSamples.Start <= mnuSample && selectedSamples.End >= mnuSample)
            {
                mnuCopy.IsEnabled = true;
                mnuCut.IsEnabled = true;
                mnuDelete.IsEnabled = true;
                mnuMeasure.IsEnabled = true;
                mnuCreateRegion.IsEnabled = true;
            }
            else
            {
                mnuCopy.IsEnabled = false;
                mnuCut.IsEnabled = false;
                mnuDelete.IsEnabled = false;
                mnuMeasure.IsEnabled = false;
                mnuCreateRegion.IsEnabled = true;
            }

            if(samplesCopied)
                mnuPaste.IsEnabled = true;
            else
                mnuPaste.IsEnabled = false;

            smplMenu.PlacementRect = new Rect(pos.Position.X, pos.Position.Y, 1, 1);
            smplMenu.Open();
        }

        async void CreateRegion()
        {
            if (selectedSamples == null || RegionCreated == null)
                return;

            var dlg = new SelectedRegionDialog();

            dlg.NewRegion.FirstSample = selectedSamples.Start;
            dlg.NewRegion.LastSample = selectedSamples.End;

            if (await dlg.ShowDialog<bool>(MainWindow.Instance))
            {
                if (RegionCreated != null)
                    RegionCreated(this, new RegionEventArgs { Region = dlg.NewRegion });

                AddRegion(dlg.NewRegion);
            }

            selectedSamples = null;

            InvalidateVisual();
        }

    }
}
