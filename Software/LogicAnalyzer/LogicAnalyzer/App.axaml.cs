using Avalonia;
using Avalonia.Controls.ApplicationLifetimes;
using Avalonia.Markup.Xaml;
using LogicAnalyzer.Dialogs;
using System.Threading.Tasks;

namespace LogicAnalyzer
{
    public partial class App : Application
    {
        public override void Initialize()
        {
            AvaloniaXamlLoader.Load(this);
        }

        public override async void OnFrameworkInitializationCompleted()
        {
            if (ApplicationLifetime is IClassicDesktopStyleApplicationLifetime desktop)
            {
                var splash = new SplashScreen();
                desktop.MainWindow = splash;
                splash.Show();

                var main = new MainWindow();
                await Task.Delay(2000);
                desktop.MainWindow = main;
                main.Show();
                splash.Close();
            }

            base.OnFrameworkInitializationCompleted();
        }
    }
}
