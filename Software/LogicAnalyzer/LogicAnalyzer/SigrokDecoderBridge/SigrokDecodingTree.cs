using SigrokDecoderBridge;
using System;
using System.Collections.Generic;
using System.Linq;
using System.Text;
using System.Threading.Tasks;

namespace LogicAnalyzer.SigrokDecoderBridge
{
    public class SigrokDecodingTree
    {
        public List<SigrokDecodingBranch> Branches { get; } = new List<SigrokDecodingBranch>();

        public SerializableDecodingTree ToSerializable()
        {
            var serializable = new SerializableDecodingTree();
            foreach (var branch in Branches)
            {
                serializable.Branches.Add(branch.ToSerializable());
            }
            return serializable;
        }
    }

    public class SigrokDecodingBranch
    {
        public required string Name { get; set; }
        public required SigrokDecoderBase Decoder { get; set; }
        public required SigrokOptionValue[] Options { get; set; }
        public required SigrokSelectedChannel[] Channels { get; set; }
        public List<SigrokDecodingBranch> Children { get; } = new List<SigrokDecodingBranch>();

        public SerializableDecodingBranch ToSerializable()
        {
            var serializable = new SerializableDecodingBranch
            {
                Name = Name,
                DecoderId = Decoder.Id,
                Options = Options.ToArray(),
                Channels = Channels.ToArray()
            };

            foreach (var child in Children)
            {
                serializable.Children.Add(child.ToSerializable());
            }

            return serializable;
        }

    }

    public class SerializableDecodingTree
    {
        public List<SerializableDecodingBranch> Branches { get; } = new List<SerializableDecodingBranch>();
    }

    public class SerializableDecodingBranch
    {
        public required string Name { get; set; }
        public required string DecoderId { get; set; }
        public required SigrokOptionValue[] Options { get; set; }
        public required SigrokSelectedChannel[] Channels { get; set; }
        public List<SerializableDecodingBranch> Children { get; } = new List<SerializableDecodingBranch>();
    }
}
