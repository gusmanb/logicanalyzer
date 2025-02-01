using System;
using System.Collections.Generic;
using System.Linq;
using System.Text;
using System.Threading.Tasks;

namespace SharedDriver
{
    public class DeviceConnectionException : Exception
    {
        public DeviceConnectionException(string message) : base(message) { }
        public DeviceConnectionException(string message, Exception innerException) : base(message, innerException) { }
    }
}
