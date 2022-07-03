using System;
using System.Collections.Generic;
using System.ComponentModel;
using System.Data;
using System.Drawing;
using System.Linq;
using System.Text;
using System.Threading.Tasks;
using System.Windows.Forms;

namespace LogicAnalyzer
{
    public partial class SampleMarker : UserControl
    {
        int firstSample;
        public int FirstSample { get { return firstSample; } set { firstSample = value; Invalidate(); } }
        int visibleSamples;
        public int VisibleSamples { get { return visibleSamples; } set { visibleSamples = value; Invalidate(); } }

        StringFormat textFormatLeft = new StringFormat { LineAlignment = StringAlignment.Center, Alignment = StringAlignment.Near };

        StringFormat textFormatRight = new StringFormat { LineAlignment = StringAlignment.Center, Alignment = StringAlignment.Far };

        StringFormat textFormatCenter = new StringFormat { LineAlignment = StringAlignment.Center, Alignment = StringAlignment.Center };

        Pen tickPen;
        Brush txtBrush;
        ToolTip overTooltip = new ToolTip();
        SelectedSampleRegion? regionUnderConstruction;

        public event EventHandler<RegionEventArgs> RegionCreated;
        public event EventHandler<RegionEventArgs> RegionDeleted;

        List<SelectedSampleRegion> regions = new List<SelectedSampleRegion>();
        public SelectedSampleRegion[] SelectedRegions { get { return regions.ToArray(); } }
        public override Color ForeColor
        {
            get
            {
                return base.ForeColor;
            }

            set
            {
                base.ForeColor = value;
                tickPen.Dispose();
                tickPen = new Pen(ForeColor);
                txtBrush.Dispose();
                txtBrush = new SolidBrush(ForeColor);
            }
        }

        public SampleMarker()
        {
            InitializeComponent();

            tickPen = new Pen(ForeColor);
            txtBrush = new SolidBrush(ForeColor);

            SetStyle(ControlStyles.AllPaintingInWmPaint | ControlStyles.OptimizedDoubleBuffer, true);
            SetStyle(ControlStyles.ResizeRedraw, true);
            SetStyle(ControlStyles.Opaque, true);

        }

        public void AddRegion(SelectedSampleRegion Region)
        {
            regions.Add(Region);
            this.Invalidate();
        }
        public void AddRegions(IEnumerable<SelectedSampleRegion> Regions)
        {
            regions.AddRange(Regions);
        }
        public bool RemoveRegion(SelectedSampleRegion Region)
        {
            var res = regions.Remove(Region);
            if (res)
                this.Invalidate();
            return res;
        }

        public void ClearRegions()
        {
            regions.Clear();
            this.Invalidate();
        }

        protected override void OnPaint(PaintEventArgs e)
        {
            e.Graphics.Clear(this.BackColor);

            if (VisibleSamples == 0)
                return;

            float sampleWidth = this.Width / (float)visibleSamples;
            float halfWidth = sampleWidth / 2;
            float halfHeight = this.Height / 2f;
            //Draw ticks
            for (int buc = 0; buc < visibleSamples; buc++)
            {
                float x = buc * sampleWidth + halfWidth;
                float y1 = halfHeight * 1.5f;
                float y2 = this.Height;

                e.Graphics.DrawLine(tickPen, x, y1, x, y2);
            }

            e.Graphics.DrawString(firstSample.ToString(), this.Font, txtBrush, new RectangleF(0, 0, 64, halfHeight * 1.5f), textFormatLeft);

            e.Graphics.DrawString((firstSample + visibleSamples - 1).ToString(), this.Font, txtBrush, new RectangleF(this.Width - 64, 0, 64, halfHeight * 1.5f), textFormatRight);

            e.Graphics.DrawString((firstSample + visibleSamples / 2).ToString(), this.Font, txtBrush, new RectangleF(this.Width / 2.0f - 32, 0, 64, halfHeight * 1.5f), textFormatCenter);

            e.Graphics.CompositingMode = System.Drawing.Drawing2D.CompositingMode.SourceOver;

            if (regionUnderConstruction != null)
            {
                
                float start = (regionUnderConstruction.FirstSample - firstSample) * sampleWidth;
                float end = sampleWidth * regionUnderConstruction.SampleCount;
                e.Graphics.FillRectangle(regionUnderConstruction.RegionColor, new RectangleF(start, 0, end, this.Height));
                
            }

            if (regions.Count > 0)
            {
                foreach (var region in regions)
                {
                    float start = (region.FirstSample - firstSample) * sampleWidth;
                    float end = sampleWidth * region.SampleCount;
                    e.Graphics.FillRectangle(region.RegionColor, new RectangleF(start, 0, end, this.Height));
                    e.Graphics.DrawString(region.RegionName, this.Font, txtBrush, new RectangleF(start, 0, end, halfHeight * 1.5f), textFormatCenter);
                }
            }

            e.Graphics.CompositingMode = System.Drawing.Drawing2D.CompositingMode.SourceCopy;
        }

        protected override void OnMouseEnter(EventArgs e)
        {
            if (visibleSamples != 0)
            {
                float sampleWidth = this.Width / (float)visibleSamples;
                var pos = PointToClient(Cursor.Position);
                int ovrSample = (int)(pos.X / sampleWidth) + firstSample;


                overTooltip.Show(ovrSample.ToString(), this, pos.X, -16, 5000);
            }
            base.OnMouseEnter(e);
        }

        protected override void OnMouseDown(MouseEventArgs e)
        {
            if (visibleSamples != 0)
            {
                if (e.Button == MouseButtons.Left)
                {
                    overTooltip.Hide(this);
                    float sampleWidth = this.Width / (float)visibleSamples;
                    var pos = PointToClient(Cursor.Position);
                    int ovrSample = (int)(pos.X / sampleWidth) + firstSample;
                    regionUnderConstruction = new SelectedSampleRegion { FirstSample = ovrSample, LastSample = ovrSample + 1 };
                    this.Invalidate();
                }
            }
            base.OnMouseDown(e);
        }

        protected override void OnMouseUp(MouseEventArgs e)
        {
            if (visibleSamples != 0)
            {
                if (regionUnderConstruction != null)
                {
                    float sampleWidth = this.Width / (float)visibleSamples;
                    var pos = PointToClient(Cursor.Position);
                    int ovrSample = (int)(pos.X / sampleWidth) + firstSample;
                    regionUnderConstruction.LastSample = ovrSample + 1;
                    var rgn = regionUnderConstruction;
                    regionUnderConstruction = null;

                    if (rgn.SampleCount > 0)
                    {
                        using (var dlg = new SelectedRegionDialog())
                        {
                            dlg.SelectedRegion = rgn;

                            if (dlg.ShowDialog() != DialogResult.OK)
                                rgn.Dispose();
                            else
                            {
                                if (this.RegionCreated != null)
                                    this.RegionCreated(this, new RegionEventArgs { Region = rgn });

                                AddRegion(rgn);
                            }
                        }
                    }

                    this.Invalidate();
                }
                else if (e.Button == MouseButtons.Right)
                {
                    float sampleWidth = this.Width / (float)visibleSamples;
                    var pos = PointToClient(Cursor.Position);
                    int ovrSample = (int)(pos.X / sampleWidth) + firstSample;

                    var toDelete = regions.Where(r => ovrSample >= r.FirstSample && ovrSample < r.LastSample).ToArray();

                    foreach (var region in toDelete)
                    {
                        if (ovrSample >= region.FirstSample && ovrSample < region.LastSample)
                        {
                            if(RegionDeleted != null)
                                RegionDeleted(this, new RegionEventArgs { Region = region});

                            RemoveRegion(region);
                        }
                    }
                }
            }
            base.OnMouseUp(e);
        }

        protected override void OnMouseMove(MouseEventArgs e)
        {
            if (visibleSamples != 0)
            {
                float sampleWidth = this.Width / (float)visibleSamples;
                var pos = PointToClient(Cursor.Position);
                int ovrSample = (int)(pos.X / sampleWidth) + firstSample;

                if (regionUnderConstruction != null)
                {
                    regionUnderConstruction.LastSample = ovrSample + 1;
                    this.Invalidate();
                }
                else
                    overTooltip.Show(ovrSample.ToString(), this, pos.X, -16, 5000);
            }
            base.OnMouseMove(e);
        }

        protected override void OnMouseLeave(EventArgs e)
        {
            overTooltip.Hide(this);
            base.OnMouseLeave(e);
        }
    }

    public class RegionEventArgs : EventArgs
    { 
        public SelectedSampleRegion Region { get; set; }
    }
}
