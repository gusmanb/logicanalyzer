using System;
using System.Collections.Generic;
using System.Linq;
using System.Text;
using System.Threading.Tasks;

namespace LogicAnalyzer.Classes
{
    using Avalonia.Media;
    using Newtonsoft.Json;
    using Newtonsoft.Json.Linq;
    using System;
    using System.Collections.Generic;
    using System.Linq;
    using System.Text;
    using System.Threading.Tasks;

    public class SelectedSampleRegion
    {
        public int FirstSample { get; set; }
        public int LastSample { get; set; }
        public int SampleCount { get { return LastSample - FirstSample; } }
        public string RegionName { get; set; } = "";
        public Color RegionColor { get; set; } = Color.FromArgb(128, 255,255,255);

        public class SelectedSampleRegionConverter : JsonConverter
        {
            public override bool CanConvert(Type objectType)
            {
                return objectType == typeof(SelectedSampleRegion);
            }

            public override object? ReadJson(JsonReader reader, Type objectType, object? existingValue, JsonSerializer serializer)
            {

                JObject jObject = JObject.Load(reader);

                if (jObject == null)
                    return null;

                return new SelectedSampleRegion { FirstSample = jObject["FirstSample"].Value<int>(), LastSample = jObject["LastSample"].Value<int>(), RegionName = jObject["RegionName"].Value<string>(), RegionColor = Color.FromArgb(jObject["A"].Value<byte>(), jObject["R"].Value<byte>(), jObject["G"].Value<byte>(), jObject["B"].Value<byte>()) };
            }

            public override void WriteJson(JsonWriter writer, object? value, JsonSerializer serializer)
            {
                var obj = value as SelectedSampleRegion;

                if (obj == null)
                    writer.WriteNull();
                else
                {
                    writer.WriteStartObject();
                    writer.WritePropertyName("FirstSample");
                    writer.WriteValue(obj.FirstSample);
                    writer.WritePropertyName("LastSample");
                    writer.WriteValue(obj.LastSample);
                    writer.WritePropertyName("RegionName");
                    writer.WriteValue(obj.RegionName);
                    writer.WritePropertyName("R");
                    writer.WriteValue(obj.RegionColor.R);
                    writer.WritePropertyName("G");
                    writer.WriteValue(obj.RegionColor.G);
                    writer.WritePropertyName("B");
                    writer.WriteValue(obj.RegionColor.B);
                    writer.WritePropertyName("A");
                    writer.WriteValue(obj.RegionColor.A);
                    writer.WriteEndObject();
                }
            }
        }
    }
}