using Avalonia;
using Avalonia.Controls;
using MessageBox.Avalonia.Enums;
using MessageBox.Avalonia;
using System;
using System.Collections.Generic;
using System.Linq;
using System.Reflection;
using System.Text;
using System.Threading.Tasks;
using System.IO;
using Newtonsoft.Json;
using System.Text.Json;
using static System.Environment;
using LogicAnalyzer.Classes;

namespace LogicAnalyzer.Extensions
{
    public static class WindowExtensions
    {
        static AppConfig config;
        static WindowExtensions()
        {
            var cfg = AppSettingsManager.GetSettings<AppConfig>("AppConfig.json");
            config = cfg ?? new AppConfig();
        }
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
        public static async Task ShowError(this Window Window, string Title, string Text)
        {
            var box = MessageBoxManager.GetMessageBoxStandardWindow(Title, Text, icon: MessageBox.Avalonia.Enums.Icon.Error);

            var prop = box.GetType().GetField("_window", BindingFlags.Instance | BindingFlags.NonPublic);
            var win = prop.GetValue(box) as Window;

            win.Icon = Window.Icon;
            await box.ShowDialog(Window);
        }
        public static async Task ShowInfo(this Window Window, string Title, string Text)
        {
            var box = MessageBoxManager.GetMessageBoxStandardWindow(Title, Text, icon: MessageBox.Avalonia.Enums.Icon.Info);

            var prop = box.GetType().GetField("_window", BindingFlags.Instance | BindingFlags.NonPublic);
            var win = prop.GetValue(box) as Window;

            win.Icon = Window.Icon;
            await box.ShowDialog(Window);
        }
        public static async Task<bool> ShowConfirm(this Window Window, string Title, string Text)
        {
            var box = MessageBoxManager.GetMessageBoxStandardWindow(Title, Text, @enum: MessageBox.Avalonia.Enums.ButtonEnum.YesNo, icon: MessageBox.Avalonia.Enums.Icon.Warning);

            var prop = box.GetType().GetField("_window", BindingFlags.Instance | BindingFlags.NonPublic);
            var win = prop.GetValue(box) as Window;

            win.Icon = Window.Icon;
            var result = await box.ShowDialog(Window);

            if (result == ButtonResult.No)
                return false;

            return true;
        }

        public static void SaveSettings(this Window Window, IEnumerable<string> Properties)
        {
            Dictionary<string, object> settings = new Dictionary<string, object>();

            foreach (var prop in Properties)
                settings.Add(prop, GetPropertyValue(Window, prop));

            config.WindowSettings[Window.GetType().FullName] = settings;

            AppSettingsManager.PersistSettings("AppConfig.json", config);
        }
        public static bool RestoreSettings(this Window Window, IEnumerable<string> Properties) 
        {
            string type = Window.GetType().FullName;

            if (!config.WindowSettings.ContainsKey(type))
                return false;

            var settings = config.WindowSettings[type];

            foreach (var typePair in settings)
            {
                try 
                {
                    SetPropertyValue(Window, typePair.Key, typePair.Value);
                } 
                catch { }
            }

            return true;
        }
        private static object GetPropertyValue(object Source, string PropertyName)
        {
            object obj = Source;

            var _propertyNames = PropertyName.Split('.');

            for (var i = 0; i < _propertyNames.Length; i++)
            {
                if (obj != null)
                {
                    var _propertyInfo = obj.GetType().GetProperty(_propertyNames[i]);
                    if (_propertyInfo != null)
                        obj = _propertyInfo.GetValue(obj);
                    else
                        obj = null;
                }
            }

            return obj;
        }

        private static void SetPropertyValue(object Source, string PropertyName, object Value)
        {
            object obj = Source;

            var _propertyNames = PropertyName.Split('.');

            PropertyInfo prop = null;

            for (var i = 0; i < _propertyNames.Length - 1; i++)
            {
                prop = obj.GetType().GetProperty(_propertyNames[i]);
                obj = prop.GetValue(obj);
            }
            prop = obj.GetType().GetProperty(_propertyNames.Last());

            if (prop.PropertyType.IsEnum)
            {
                var val = (int)(long)Value;
                prop.SetValue(obj, val, null);
            }
            else
                prop.SetValue(obj, Value, null);
        }

        class AppConfig
        {
            public string AppName { get; set; } = Assembly.GetEntryAssembly().FullName;
            public Dictionary<string, Dictionary<string, object>> WindowSettings { get; set; } = new Dictionary<string, Dictionary<string, object>>();
        }
    }
}
