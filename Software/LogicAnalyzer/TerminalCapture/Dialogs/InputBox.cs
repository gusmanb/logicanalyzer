using System;
using System.Collections.Generic;
using System.Linq;
using System.Text;
using System.Threading.Tasks;
using Terminal.Gui;

namespace TerminalCapture.Dialogs
{
    public class InputBox : Dialog
    {
        public string? Value { get; set; }

        public InputBox(string title, string prompt, int? width = null, int? height = null, string? value = null)
        {
            Title = title;
            Width = width ?? Dim.Percent(50);
            Height = height ?? Dim.Percent(50);

            var label = new Label()
            {
                X = 1,
                Y = 1,
                Width = Dim.Fill(2),
                Height = 1,
                Text = prompt
            };
            Add(label);

            var textField = new TextField()
            {
                X = 1,
                Y = 2,
                Width = Dim.Fill(2),
                Height = 1,
                Text = value ?? "",
                ColorScheme = Colors.ColorSchemes["EditableControl"]
            };

            Add(textField);

            var okButton = new Button()
            {
                X = Pos.Align(Alignment.End),
                Y = Pos.Percent(75),
                Text = "Ok"
            };
            okButton.Accepting += (o, args) =>
            {
                Value = textField.Text.ToString();
                Running = false;
            };
            Add(okButton);

            var cancelButton = new Button()
            {
                X = Pos.Left(okButton) - 10,
                Y = Pos.Top(okButton),
                Text = "Cancel"
            };
            cancelButton.Accepting += (o, args) =>
            {
                Value = null;
                Running = false;
            };
            Add(cancelButton);
        }
    }
}
