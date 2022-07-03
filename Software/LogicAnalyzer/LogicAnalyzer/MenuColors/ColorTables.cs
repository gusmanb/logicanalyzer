using System;
using System.Collections.Generic;
using System.Linq;
using System.Text;
using System.Threading.Tasks;

namespace LogicAnalyzer.MenuColors
{
    public class SubmenuColorTable : ProfessionalColorTable
    {
        public override Color MenuItemSelected
        {
            get { return ColorTranslator.FromHtml("#302E2D"); }
        }

        public override Color MenuItemBorder
        {
            get { return Color.Silver; }
        }

        public override Color ToolStripDropDownBackground
        {
            get { return ColorTranslator.FromHtml("#21201F"); }
        }

        public override Color ToolStripContentPanelGradientBegin
        {
            get { return ColorTranslator.FromHtml("#21201F"); }
        }
    }

    public class LeftMenuColorTable : ProfessionalColorTable
    {
        public override Color MenuItemBorder
        {
            get { return ColorTranslator.FromHtml("#BAB9B9"); }
        }

        public override Color MenuBorder  //added for changing the menu border
        {
            get { return Color.Silver; }
        }

        public override Color MenuItemPressedGradientBegin
        {
            get { return ColorTranslator.FromHtml("#4C4A48"); }
        }
        public override Color MenuItemPressedGradientEnd
        {
            get { return ColorTranslator.FromHtml("#5F5D5B"); }
        }

        public override Color ToolStripBorder
        {
            get { return ColorTranslator.FromHtml("#4C4A48"); }
        }

        public override Color MenuItemSelectedGradientBegin
        {
            get { return ColorTranslator.FromHtml("#4C4A48"); }
        }

        public override Color MenuItemSelectedGradientEnd
        {
            get { return ColorTranslator.FromHtml("#5F5D5B"); }
        }

        public override Color ToolStripDropDownBackground
        {
            get { return ColorTranslator.FromHtml("#404040"); }
        }

        public override Color ToolStripGradientBegin
        {
            get { return ColorTranslator.FromHtml("#404040"); }
        }

        public override Color ToolStripGradientEnd
        {
            get { return ColorTranslator.FromHtml("#404040"); }
        }

        public override Color ToolStripGradientMiddle
        {
            get { return ColorTranslator.FromHtml("#404040"); }
        }

    }

    public class MyColorTable : ProfessionalColorTable
    {
        /// <summary>
        /// Gets the starting color of the gradient used when 
        /// a top-level System.Windows.Forms.ToolStripMenuItem is pressed.
        /// </summary>
        public override Color MenuItemPressedGradientBegin => Color.DarkGray;

        /// <summary>
        /// Gets the end color of the gradient used when a top-level 
        /// System.Windows.Forms.ToolStripMenuItem is pressed.
        /// </summary>
        public override Color MenuItemPressedGradientEnd => Color.DarkGray;

        /// <summary>
        /// Gets the border color to use with a 
        /// System.Windows.Forms.ToolStripMenuItem.
        /// </summary>
        public override Color MenuItemBorder => Color.DarkGray;

        /// <summary>
        /// Gets the starting color of the gradient used when the 
        /// System.Windows.Forms.ToolStripMenuItem is selected.
        /// </summary>
        public override Color MenuItemSelectedGradientBegin => Color.Silver;

        /// <summary>
        /// Gets the end color of the gradient used when the 
        /// System.Windows.Forms.ToolStripMenuItem is selected.
        /// </summary>
        public override Color MenuItemSelectedGradientEnd => Color.DarkGray;

        /// <summary>
        /// Gets the solid background color of the 
        /// System.Windows.Forms.ToolStripDropDown.
        /// </summary>
        public override Color ToolStripDropDownBackground => Color.DarkGray;

        /// <summary>
        /// Gets the starting color of the gradient used in the image 
        /// margin of a System.Windows.Forms.ToolStripDropDownMenu.
        /// </summary>
        public override Color ImageMarginGradientBegin => Color.DarkGray;

        /// <summary>
        /// Gets the middle color of the gradient used in the image 
        /// margin of a System.Windows.Forms.ToolStripDropDownMenu.
        /// </summary>
        public override Color ImageMarginGradientMiddle => Color.DarkGray;

        /// <summary>
        /// Gets the end color of the gradient used in the image 
        /// margin of a System.Windows.Forms.ToolStripDropDownMenu.
        /// </summary>
        public override Color ImageMarginGradientEnd => Color.DarkGray;

        /// <summary>
        /// Gets the color to use to for shadow effects on 
        /// the System.Windows.Forms.ToolStripSeparator.
        /// </summary>
        public override Color SeparatorDark => Color.Black;

        /// <summary>
        /// Gets the color that is the border color to use 
        /// on a System.Windows.Forms.MenuStrip.
        /// </summary>
        public override Color MenuBorder => Color.DarkGray;

    }
}
