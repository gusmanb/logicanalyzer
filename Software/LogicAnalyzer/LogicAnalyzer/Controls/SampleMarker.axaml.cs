using Avalonia;
using Avalonia.Controls;
using Avalonia.Input;
using Avalonia.Markup.Xaml;
using Avalonia.Media;
using Avalonia.Threading;
using LogicAnalyzer.Classes;
using LogicAnalyzer.Dialogs;
using System;
using System.Collections.Generic;
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

        public event EventHandler<SamplesEventArgs> SamplesDeleted;
        public event EventHandler<UserMarkerEventArgs> UserMarkerSelected;

        List<SelectedSampleRegion> regions = new List<SelectedSampleRegion>();

        SelectedSampleRegion? regionUnderConstruction;
        SelectedSampleRegion[] regionsToDelete = null; 

        int? userMarker = null;
        public SelectedSampleRegion[] SelectedRegions { get { return regions.ToArray(); } }

        public SampleMarker()
        {
            InitializeComponent();
            mnuDeleteRegions.Click += MnuDeleteRegions_Click;
            mnuDeleteRegionsSamples.Click += MnuDeleteRegionsSamples_Click;
        }

        private void MnuDeleteRegionsSamples_Click(object? sender, Avalonia.Interactivity.RoutedEventArgs e)
        {
            var minDelete = regionsToDelete.Select(r => Math.Min(r.FirstSample, r.LastSample)).Min();
            var maxDelete = regionsToDelete.Select(r => Math.Max(r.LastSample, r.FirstSample)).Max();

            int len = maxDelete - minDelete;

            if (RegionDeleted != null)
            {
                foreach (var region in regionsToDelete)
                {
                    RegionDeleted(this, new RegionEventArgs { Region = region });
                    RemoveRegion(region);
                }
            }

            if (SamplesDeleted != null)
                SamplesDeleted(this, new SamplesEventArgs { FirstSample = minDelete, SampleCount = len });
        }

        private void MnuDeleteRegions_Click(object? sender, Avalonia.Interactivity.RoutedEventArgs e)
        {
            var minDelete = regionsToDelete.Select(r => Math.Min(r.FirstSample, r.LastSample)).Min();
            var maxDelete = regionsToDelete.Select(r => Math.Max(r.LastSample, r.FirstSample)).Max();

            int len = maxDelete - minDelete;

            if (RegionDeleted != null)
            {
                foreach (var region in regionsToDelete)
                {
                    RegionDeleted(this, new RegionEventArgs { Region = region });
                    RemoveRegion(region);
                }
            }
        }

        public void AddRegion(SelectedSampleRegion Region)
        {
            regions.Add(Region);
            this.InvalidateVisual();
        }
        public void AddRegions(IEnumerable<SelectedSampleRegion> Regions)
        {
            regions.AddRange(Regions);
        }
        public bool RemoveRegion(SelectedSampleRegion Region)
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
            context.FillRectangle(Background, new Rect(0, 0, Bounds.Width, Bounds.Height));

            if (VisibleSamples == 0)
                return;

            double sampleWidth = this.Bounds.Width / VisibleSamples;
            double halfWidth = sampleWidth / 2;
            double halfHeight = this.Bounds.Height / 2f;


            if (regionUnderConstruction != null)
            {
                int first = Math.Min(regionUnderConstruction.FirstSample, regionUnderConstruction.LastSample);
                double start = (first - FirstSample) * sampleWidth;
                double end = sampleWidth * regionUnderConstruction.SampleCount;
                context.FillRectangle(GraphicObjectsCache.GetBrush(regionUnderConstruction.RegionColor), new Rect(start, 0, end, this.Bounds.Height));

            }

            if (regions.Count > 0)
            {
                foreach (var region in regions)
                {
                    int first = Math.Min(region.FirstSample, region.LastSample);
                    double start = (first - FirstSample) * sampleWidth;
                    double end = sampleWidth * region.SampleCount;
                    context.FillRectangle(GraphicObjectsCache.GetBrush(region.RegionColor), new Rect(start, 0, end, this.Bounds.Height));
                    FormattedText text = new FormattedText(region.RegionName, Typeface.Default, 12, TextAlignment.Left, TextWrapping.NoWrap, Size.Infinity);
                    context.DrawText(GraphicObjectsCache.GetBrush(Colors.White), new Point(start + (end / 2) - (text.Bounds.Width / 2), 5), text);
                }
            }

            //Draw ticks
            for (int buc = 0; buc < VisibleSamples; buc++)
            {
                double x = buc * sampleWidth + halfWidth;
                double y1 = halfHeight * 1.5f;
                double y2 = this.Bounds.Height;

                context.DrawLine(GraphicObjectsCache.GetPen(Foreground, 1), new Point(x, y1), new Point(x, y2));

                x = buc * sampleWidth;
                y1 = halfHeight * 1.75f;

                context.DrawLine(GraphicObjectsCache.GetPen(Foreground, 1), new Point(x, y1), new Point(x, y2));
            }

            base.Render(context);
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

                if (regionUnderConstruction != null)
                {
                    regionUnderConstruction.LastSample = ovrSample + 1;
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

                    regionUnderConstruction = new SelectedSampleRegion { FirstSample = ovrSample, LastSample = ovrSample };
                    this.InvalidateVisual();
                }
            }


        }

        async void ShowDialog(SelectedSampleRegion rgn)
        {
            var dlg = new SelectedRegionDialog();

            dlg.SelectedRegion = rgn;

            if (await dlg.ShowDialog<bool>(MainWindow.Instance))
            {
                if (this.RegionCreated != null)
                    this.RegionCreated(this, new RegionEventArgs { Region = rgn });

                AddRegion(rgn);
            }

            InvalidateVisual();
        }

        protected override void OnPointerReleased(PointerReleasedEventArgs e)
        {
            base.OnPointerReleased(e);

            if (VisibleSamples != 0)
            {
                var pos = e.GetCurrentPoint(this);

                if (regionUnderConstruction != null)
                {
                    double sampleWidth = this.Bounds.Width / (float)VisibleSamples;
                    int ovrSample = (int)(pos.Position.X / sampleWidth) + FirstSample;
                    regionUnderConstruction.LastSample = ovrSample + 1;

                    if (regionUnderConstruction.LastSample < regionUnderConstruction.FirstSample)
                    {
                        int val = regionUnderConstruction.FirstSample;
                        regionUnderConstruction.FirstSample = regionUnderConstruction.LastSample;
                        regionUnderConstruction.LastSample = val;
                    }

                    var rgn = regionUnderConstruction;
                    regionUnderConstruction = null;

                    if (rgn.SampleCount > 0)
                    {
                        if (rgn.SampleCount == 1)
                        {

                            if(userMarker != null && userMarker == rgn.FirstSample)
                                userMarker = null;

                            if (e.InputModifiers.HasFlag(InputModifiers.Shift) && userMarker != null)
                            {

                                if (this.UserMarkerSelected != null)
                                    this.UserMarkerSelected(this, new UserMarkerEventArgs { Position = userMarker.Value });

                                rgn.FirstSample = userMarker.Value;

                                userMarker = null;

                                ShowDialog(rgn);
                                return;
                            }

                            userMarker = rgn.FirstSample;

                            if (this.UserMarkerSelected != null)
                                this.UserMarkerSelected(this, new UserMarkerEventArgs { Position = rgn.FirstSample });

                            this.InvalidateVisual();
                        }
                        else
                            ShowDialog(rgn);
                        
                    }
                    else
                        this.InvalidateVisual();
                }
                else if (pos.Properties.PointerUpdateKind == PointerUpdateKind.RightButtonReleased)
                {
                    double sampleWidth = this.Bounds.Width / (float)VisibleSamples;
                    int ovrSample = (int)(pos.Position.X / sampleWidth) + FirstSample;

                    var toDelete = regions.Where(r => ovrSample >= Math.Min(r.FirstSample , r.LastSample) && ovrSample < Math.Max(r.FirstSample, r.LastSample)).ToArray();

                    if (toDelete != null && toDelete.Length > 0)
                    {
                        regionsToDelete= toDelete;
                        rgnDeleteMenu.PlacementRect = new Rect(pos.Position.X, pos.Position.Y, 1, 1);
                        rgnDeleteMenu.Open();
                    }

                    //foreach (var region in toDelete)
                    //{
                    //    if (ovrSample >= region.FirstSample && ovrSample < region.LastSample)
                    //    {

                    //        if (RegionDeleted != null)
                    //            RegionDeleted(this, new RegionEventArgs { Region = region });

                    //        RemoveRegion(region);
                    //    }
                    //}
                }
            }
        }
    }
}
