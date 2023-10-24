using Newtonsoft.Json;
using System;
using System.Collections.Generic;
using System.IO;
using System.Linq;
using System.Text;
using System.Threading.Tasks;
using static System.Environment;

namespace LogicAnalyzer.Classes
{
    public static class AppSettingsManager
    {
        static JsonSerializerSettings jSettings = new JsonSerializerSettings { TypeNameHandling = TypeNameHandling.All, Formatting = Formatting.Indented };

        public static T? GetSettings<T>(string FileName) where T : class
        {
            try
            {
                string path = GetFilePath(FileName);

                if(!File.Exists(path))
                    return null;

                string content = File.ReadAllText(path);
                var settings = JsonConvert.DeserializeObject<T>(content, jSettings);
                return settings;
            }
            catch { return null; }
        }
        public static bool PersistSettings(string FileName, object Settings)
        {
            try
            {
                string path = GetFilePath(FileName);
                var data = JsonConvert.SerializeObject(Settings, jSettings);
                File.WriteAllText(path, data);
                return true;
            }
            catch { return false; }
        }

        private static string GetFilePath(string FileName)
        {
            string appData = Path.Combine(Environment.GetFolderPath(SpecialFolder.ApplicationData, SpecialFolderOption.DoNotVerify), "LogicAnalyzer");
            Directory.CreateDirectory(appData);
            return Path.Combine(appData, FileName);
        }
    }
}
