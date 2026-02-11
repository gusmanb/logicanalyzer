using LogicAnalyzer.SigrokDecoderBridge;
using SharedDriver;
using System;
using System.Collections.Generic;
using System.Linq;
using System.Text;
using System.Threading.Tasks;

namespace LogicAnalyzer.Classes
{
    public class ProfilesSet
    {
        public List<Profile> Profiles { get; } = new List<Profile>();
    }

    public class Profile
    {
        public required string Name { get; set; }
        public CaptureSession? CaptureSettings { get; set; }
        public SerializableDecodingTree? DecoderConfiguration { get; set; }
    }
}
