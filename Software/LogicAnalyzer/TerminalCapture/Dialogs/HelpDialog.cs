using System;
using System.Collections.Generic;
using System.Linq;
using System.Text;
using System.Threading.Tasks;
using Terminal.Gui;

namespace TerminalCapture.Dialogs
{
    public class HelpDialog : Dialog
    {
        public HelpDialog()
        {
            Title = "Help";
            Width = 70;
            Height = 15;

            var helpText = new Label()
            {
                X = 1,
                Y = 1,
                Width = Dim.Fill(1),
                Height = Dim.Fill(3),
                Text = @"Execute with no parameters to open the terminal GUI, from here you can create a configuration file and capture samples. 

Execute with
""capture {ConnectionString} {ConfigurationFile} {OutputFile}"" 
to start a capture without starting the GUI."
            };
            Add(helpText);

            var okButton = new Button()
            {
                X = Pos.Center(),
                Y = Pos.Align(Alignment.End),
                Text = "Ok"
            };
            okButton.Accepting += (o, e) =>
            {
                RequestStop();
            };
            Add(okButton);
        }
    }
}
