using Newtonsoft.Json;
using SharedDriver;
using System;
using System.Collections.Generic;
using System.Linq;
using System.Text;
using System.Threading.Tasks;
using Terminal.Gui;

namespace TerminalCapture.Classes
{
    public static class FileOperations
    {
        public static CaptureSession? LoadSession(string FileName)
        {
            try
            {
                string json = File.ReadAllText(FileName);
                if (FileName.ToLower().EndsWith(".tcs"))
                {
                    return JsonConvert.DeserializeObject<CaptureSession>(json);
                }
                else if (FileName.EndsWith(".lac"))
                {
                    var envelope = JsonConvert.DeserializeObject<LACEnvelope>(json);
                    return envelope?.Settings;
                }
                else
                    return null;
            }
            catch { return null; }
        }
        public static bool SaveLAC(CaptureSession Session, string FileName)
        {
            try
            {
                string json = JsonConvert.SerializeObject(new LACEnvelope { Settings = Session });
                File.WriteAllText(FileName, json);
                return true;
            }
            catch { return false; }
        }

        public static bool SaveCSV(CaptureSession Session, string FileName)
        {
            try
            {

                StreamWriter sw = new StreamWriter(File.Create(FileName));

                StringBuilder sb = new StringBuilder();

                for (int buc = 0; buc < Session.CaptureChannels.Length; buc++)
                {
                    sb.Append(string.IsNullOrWhiteSpace(Session.CaptureChannels[buc].ChannelName) ? $"Channel {buc + 1}" : Session.CaptureChannels[buc].ChannelName);

                    if (buc < Session.CaptureChannels.Length - 1)
                        sb.Append(",");
                }

                sw.WriteLine(sb.ToString());

                for (int sample = 0; sample < Session.TotalSamples; sample++)
                {
                    sb.Clear();

                    for (int buc = 0; buc < Session.CaptureChannels.Length; buc++)
                        sb.Append($"{Session.CaptureChannels[buc].Samples![sample]},");

                    sb.Remove(sb.Length - 1, 1);

                    sw.WriteLine(sb.ToString());
                }

                sw.Close();
                sw.Dispose();
                return true;
            }
            catch { return false; }
        }
    }
}
