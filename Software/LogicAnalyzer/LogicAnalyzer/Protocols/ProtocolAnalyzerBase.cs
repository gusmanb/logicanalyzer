using System;
using System.Collections.Generic;
using System.Linq;
using System.Text;
using System.Threading.Tasks;

namespace LogicAnalyzer.Protocols
{
    public abstract class ProtocolAnalyzerBase : IDisposable
    {
        /// <summary>
        /// Categorization of the analyzer
        /// </summary>
        public virtual string[] Categories => new string[0];

        /// <summary>
        /// Type of analyzer. Depending on the type the analyzer result will be shown in the channels or the annotation band.
        /// Also this will determine the analyziz call to execute
        /// </summary>
        public abstract ProtocolAnalyzerType AnalyzerType { get; }
        /// <summary>
        /// Protocol name to show in the menu
        /// </summary>
        public abstract string ProtocolName { get; }
        /// <summary>
        /// List of settings needed by the analyzer
        /// </summary>
        public abstract ProtocolAnalyzerSetting[] Settings { get; }
        /// <summary>
        /// List of signals used by the protocol analyzer
        /// </summary>
        public abstract ProtocolAnalyzerSignal[] Signals { get; }
        /// <summary>
        /// Validates if settings are correct
        /// </summary>
        /// <param name="SelectedSettings">Settings to validate</param>
        /// <param name="SelectedChannels">Selected channels</param>
        /// <returns>True if the settins and signals are correct, false in other case</returns>
        public abstract bool ValidateSettings(ProtocolAnalyzerSettingValue[] SelectedSettings, ProtocolAnalyzerSelectedChannel[] SelectedChannels);
        /// <summary>
        /// Analyzes a set of samples
        /// </summary>
        /// <param name="SelectedSettings">Settings to use to analyze the protocol</param>
        /// <param name="SelectedChannels">Channels to analyze</param>
        /// <returns>An array of analyzed channels</returns>
        public virtual ProtocolAnalyzedChannel[] AnalyzeChannels(int SamplingRate, int TriggerSample, ProtocolAnalyzerSettingValue[] SelectedSettings, ProtocolAnalyzerSelectedChannel[] SelectedChannels) 
        {
            throw new NotImplementedException("Analyze method not implemented");
        }

        public virtual ProtocolAnalyzedAnnotation[] AnalyzeAnnotations(int SamplingRate, int TriggerSample, ProtocolAnalyzerSettingValue[] SelectedSettings, ProtocolAnalyzerSelectedChannel[] SelectedChannels)
        {
            throw new NotImplementedException("Analyze method not implemented");
        }

        /// <summary>
        /// Informs the analyzer of the size of a bus. By default returns 0 (bus not used).
        /// </summary>
        /// <param name="Signal">The bus to get the size for</param>
        /// <param name="SelectedSettings">The settings the user selected</param>
        /// <returns>The size of the bus</returns>
        public virtual int GetBusWidth(ProtocolAnalyzerSignal Signal, ProtocolAnalyzerSettingValue[] SelectedSettings)
        {
            return 0;
        }

        public virtual void Dispose()
        {
        }
    }

    public enum ProtocolAnalyzerType
    {
        ChannelAnalyzer,
        AnnotationAnalyzer
    }
}
