using Avalonia.Controls;
using LogicAnalyzer.Extensions;
using System;
using System.Collections.Generic;
using System.ComponentModel;
using System.Linq;
using System.Runtime.CompilerServices;
using System.Text;
using System.Threading.Tasks;

namespace LogicAnalyzer.Classes
{
    public class PersistableWindowBase : Window
    {
        static string[] defaultWindowProperties = new string[]
        {
            nameof(Window.Width),
            nameof(Window.Height),
            nameof(Window.Position),
            nameof(Window.WindowState)
        };

        protected virtual bool SkipDefaultProperties { get { return false; } }

        protected virtual string[]? PersistProperties { get { return null; } }

        protected override void OnOpened(EventArgs e)
        {
            var userProps = PersistProperties;

            if (userProps != null)
            {
                List<string> props = new List<string>();
                props.AddRange(userProps);

                if (!SkipDefaultProperties)
                    props.AddRange(defaultWindowProperties);

                if (!this.RestoreSettings(props))
                    this.FixStartupPosition();
            }
            else
            {
                if(!this.RestoreSettings(defaultWindowProperties))
                    this.FixStartupPosition();
            }

        }

        protected override void OnClosing(CancelEventArgs e)
        {
            var userProps = PersistProperties;

            if (userProps != null)
            {
                List<string> props = new List<string>();
                props.AddRange(userProps);

                if(!SkipDefaultProperties)
                    props.AddRange(defaultWindowProperties);

                this.SaveSettings(props);
            }
            else
                this.SaveSettings(defaultWindowProperties);

            base.OnClosing(e);
        }
    }
}
