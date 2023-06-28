using System;
using System.Collections.Generic;
using System.Linq;
using System.Text;
using System.Threading.Tasks;

namespace CLCapture
{
    public class CLChannel
    {
        public CLChannel(string Definition) 
        {
            if(string.IsNullOrWhiteSpace(Definition)) 
                throw new ArgumentNullException("Missing channel definition.");

            var inputParts = Definition.Trim().Split(":");

            if (inputParts.Length < 1)
                throw new ArgumentException("Invalid channel definition");

            if (inputParts.Length == 1)
            {
                int value;

                if (!int.TryParse(inputParts[0], out value))
                    throw new ArgumentException("Invalid channel definition, channel must be defined in decimal form.");

                ChannelNumber = value;
                ChannelName = $"Channel {value}";
            }
            else if (inputParts.Length == 2)
            {
                int value;

                if (!int.TryParse(inputParts[0], out value))
                    throw new ArgumentException("Invalid channel definition, channel must be defined in decimal form.");

                ChannelNumber = value;
                ChannelName = inputParts[1];
            }
            else
            {
                throw new ArgumentException("Invalid channel definition, too many parts.");
            }
        }
        public int ChannelNumber { get; set; }
        public string ChannelName { get; set; }
    }
}
