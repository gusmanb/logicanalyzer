using System;
using System.Collections.Generic;
using System.Linq;
using System.Text;
using System.Threading.Tasks;

namespace LogicAnalyzer.Protocols
{
    public abstract class ProtocolAnalyzerProviderBase : IDisposable
    {
        private bool sessionStarted = false;
        public abstract ProtocolAnalyzerBase[] GetAnalyzers();

        public void BeginAnalysisSession()
        {
            if (sessionStarted)
                return;

            sessionStarted = true;
            BeginSession();
        }

        protected virtual void BeginSession() { }

        public void EndAnalysisSession()
        {
            if (!sessionStarted)
                return;

            sessionStarted = false;
            EndSession();
        }

        protected virtual void EndSession() { }

        public virtual void Dispose()
        {
        }
    }
}
