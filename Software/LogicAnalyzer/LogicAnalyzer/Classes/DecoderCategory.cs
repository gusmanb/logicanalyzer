using SigrokDecoderBridge;
using System;
using System.Collections.Generic;
using System.Collections.ObjectModel;
using System.Linq;
using System.Text;
using System.Threading.Tasks;

namespace LogicAnalyzer.Classes
{
    public class DecoderCategory
    {
        public required string Name { get; set; }
        public ObservableCollection<SigrokDecoderBase> Decoders { get; set; } = new ObservableCollection<SigrokDecoderBase>();
    }
}
