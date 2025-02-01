using System;
using System.Collections.Generic;
using System.Linq;
using System.Text;
using System.Threading.Tasks;
using Terminal.Gui;

namespace TerminalCapture
{
    public interface IStepValidate
    {
        public void OnValidate(StepValidateArgs Arguments);
    }

    public class StepValidateArgs
    {
        public bool IsValid { get; set; }
        public WizardStep[]? Sequence { get; set; }
        public object? Args { get; set; }
    }
}
