using Avalonia;
using Avalonia.Controls;
using System;
using System.Collections.Generic;
using System.Linq;
using System.Text;
using System.Threading.Tasks;

namespace LogicAnalyzer.Extensions
{
    public static class WindowExtensions
    {
        public static void FixStartupPosition(this Window windowToFix)
        {
            if (OperatingSystem.IsWindows())
            {
                // Not needed for Windows
                return;
            }

            var scale = windowToFix.PlatformImpl?.DesktopScaling ?? 1.0;
            var pOwner = windowToFix.Owner?.PlatformImpl;
            if (pOwner != null)
            {
                scale = pOwner.DesktopScaling;
            }
            var rect = new PixelRect(PixelPoint.Origin,
                PixelSize.FromSize(windowToFix.ClientSize, scale));
            if (windowToFix.WindowStartupLocation == WindowStartupLocation.CenterScreen)
            {
                var screen = windowToFix.Screens.ScreenFromPoint(pOwner?.Position ?? windowToFix.Position);
                if (screen == null)
                {
                    return;
                }
                windowToFix.Position = screen.WorkingArea.CenterRect(rect).Position;
            }
            else
            {
                if (pOwner == null ||
                    windowToFix.WindowStartupLocation != WindowStartupLocation.CenterOwner)
                {
                    return;
                }
                windowToFix.Position = new PixelRect(pOwner.Position,
                    PixelSize.FromSize(pOwner.ClientSize, scale)).CenterRect(rect).Position;
            }
        }
    }
}
