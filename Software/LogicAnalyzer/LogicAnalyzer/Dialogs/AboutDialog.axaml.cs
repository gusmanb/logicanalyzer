using Avalonia.Controls;
using LogicAnalyzer.Extensions;
using System.Diagnostics;
using System.IO.Packaging;
using System.Reflection;
using System.Runtime.InteropServices;

namespace LogicAnalyzer.Dialogs
{
    public partial class AboutDialog : Window
    {
        public AboutDialog()
        {
            InitializeComponent();
            txtVersion.Text = $"Version {GetAppVersion()}";
            btnLicense.Click += BtnLicense_Click;
            lnkWebSite.Click += LnkWebSite_Click;
        }
        private async void LnkWebSite_Click(object? sender, Avalonia.Interactivity.RoutedEventArgs e)
        {
            try
            {
                OpenUrl("https://github.com/gusmanb/logicanalyzer");
            }
            catch
            {
                await this.ShowError("Cannot open page.", "Cannot start the default browser. You can access the online documentation in https://github.com/gusmanb/logicanalyzer");
            }
        }
        private async void BtnLicense_Click(object? sender, Avalonia.Interactivity.RoutedEventArgs e)
        {
            try
            {
                OpenUrl("https://github.com/gusmanb/logicanalyzer/blob/master/LICENSE");
            }
            catch
            {
                await this.ShowError("Cannot open page.", "Cannot start the default browser. You can access the online documentation in https://github.com/gusmanb/logicanalyzer/blob/master/LICENSE");
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
                    //Process.Start("xdg-open", url);
                    Process.Start("x-www-browser", url);
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

        static string GetAppVersion()
        {
            return Assembly.GetEntryAssembly().GetCustomAttribute<AssemblyInformationalVersionAttribute>().InformationalVersion;
        }
    }
}
