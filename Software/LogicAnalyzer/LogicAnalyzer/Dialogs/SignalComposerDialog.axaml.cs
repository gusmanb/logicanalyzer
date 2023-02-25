using Avalonia.Animation.Animators;
using Avalonia.Controls;
using Avalonia.Input;
using Avalonia.Threading;
using AvaloniaEdit;
using AvaloniaEdit.Document;
using AvaloniaEdit.Highlighting;
using AvaloniaEdit.Highlighting.Xshd;
using AvaloniaEdit.Rendering;
using LogicAnalyzer.Classes;
using LogicAnalyzer.Controls;
using LogicAnalyzer.Extensions;
using Newtonsoft.Json;
using SignalDescriptionLanguage;
using System;
using System.Collections.Generic;
using System.IO;
using System.Linq;
using System.Reflection.PortableExecutable;
using System.Threading.Tasks;
using System.Windows.Input;
using System.Xml;
using TextMateSharp.Internal.Types;
using TextMateSharp.Registry;
using TextMateSharp.Themes;
using static SignalDescriptionLanguage.SDLParser;

namespace LogicAnalyzer.Dialogs
{
    public partial class SignalComposerDialog : PersistableWindowBase
    {
        
        const int FONT_MAX_SIZE = 64;
        const int FONT_MIN_SIZE = 7;

        public double EditorFontSize { get { return editSignal.FontSize; } set { editSignal.FontSize = value; } }

        protected override string[]? PersistProperties
        {
            get
            {
                return new string[] { nameof(EditorFontSize) };
            }
        }

        TokenizedSDL sdl;
        public TokenizedSDL SDL { get { return sdl; } set { sdl = value; editSignal.Document.Text = sdl?.Source ?? ""; } }

        bool confirmed = false;
        MenuItem cutMenu;
        MenuItem copyMenu;
        MenuItem pasteMenu;

        public SignalComposerDialog()
        {
            InitializeComponent();

            using var xr = Xshd.AsReader;
            editSignal.SyntaxHighlighting = HighlightingLoader.Load(xr, HighlightingManager.Instance);

            editSignal.Document = new AvaloniaEdit.Document.TextDocument();
            editSignal.TextArea.PointerWheelChanged += SignalComposerDialog_PointerWheelChanged;
            editSignal.WordWrap = true;
            editSignal.TextChanged += EditSignal_TextChanged;

            editSignal.ShowLineNumbers = true;
            editSignal.ContextMenu = new ContextMenu
            {
                Items = new List<MenuItem>
                {
                    (copyMenu = new MenuItem { Header = "Copy", InputGesture = new KeyGesture(Key.C, KeyModifiers.Control), IsEnabled = false }),
                    (pasteMenu = new MenuItem { Header = "Paste", InputGesture = new KeyGesture(Key.V, KeyModifiers.Control) }),
                    (cutMenu = new MenuItem { Header = "Cut", InputGesture = new KeyGesture(Key.X, KeyModifiers.Control), IsEnabled = false })
                }
            };
            editSignal.TextArea.Background = this.Background;
            editSignal.Options.ShowBoxForControlCharacters = true;
            editSignal.Options.ColumnRulerPosition = 80;
            editSignal.TextArea.IndentationStrategy = new AvaloniaEdit.Indentation.CSharp.CSharpIndentationStrategy(editSignal.Options);
            editSignal.TextArea.Caret.PositionChanged += Caret_PositionChanged;
            editSignal.TextArea.RightClickMovesCaret = true;
            editSignal.TextArea.SelectionChanged += TextArea_SelectionChanged;

            this.Opened += SignalComposerDialog_Opened;
            this.Closing += SignalComposerDialog_Closing;
            mnuNew.Click += MnuNew_Click;
            mnuOpen.Click += MnuOpen_Click;
            mnuSave.Click += MnuSave_Click;
            mnuValidate.Click += MnuValidate_Click;

            cutMenu.Click += CutMenu_Click;
            copyMenu.Click += CopyMenu_Click;
            pasteMenu.Click += PasteMenu_Click;
        }

        private void PasteMenu_Click(object? sender, Avalonia.Interactivity.RoutedEventArgs e)
        {
            editSignal.Paste();
        }

        private void CopyMenu_Click(object? sender, Avalonia.Interactivity.RoutedEventArgs e)
        {
            editSignal.Copy();
        }

        private void CutMenu_Click(object? sender, Avalonia.Interactivity.RoutedEventArgs e)
        {
            editSignal.Cut();
        }

        private void TextArea_SelectionChanged(object? sender, EventArgs e)
        {
            if (editSignal.TextArea.Selection != null && !editSignal.TextArea.Selection.IsEmpty)
            {
                copyMenu.IsEnabled = true;
                cutMenu.IsEnabled = true;
            }
            else
            {
                copyMenu.IsEnabled = false;
                cutMenu.IsEnabled = false;
            }
        }

        private void Caret_PositionChanged(object? sender, EventArgs e)
        {
            tbLine.Text = editSignal.TextArea.Caret.Line.ToString();
            tbColumn.Text = editSignal.TextArea.Caret.Column.ToString();
        }

        private async void SignalComposerDialog_Closing(object? sender, System.ComponentModel.CancelEventArgs e)
        {
            if (confirmed)
                return;

            sdl = null;
            e.Cancel = true;

            await Task.Yield();

            try 
            {
                sdl = new TokenizedSDL(editSignal.Document.Text);
                confirmed = true;
                this.Close();

            } catch 
            {
                confirmed = await this.ShowConfirm("Bad SDL", "Warning! This SDL contains errors, are you sure you want to close the editor? The content will be lost.");

                if (confirmed)
                    this.Close();
            }
        }

        private void EditSignal_TextChanged(object? sender, EventArgs e)
        {
            bool content = !string.IsNullOrWhiteSpace(editSignal.Document.Text);

            if(mnuSave.IsEnabled != content)
                mnuSave.IsEnabled = content;
        }

        private async void MnuValidate_Click(object? sender, Avalonia.Interactivity.RoutedEventArgs e)
        {
            string text = editSignal.Text;

            if (string.IsNullOrEmpty(text))
            {
                await this.ShowError("No content", "Document is empty.");
                return;
            }

            try
            {
                var sdl = new SDLParser.TokenizedSDL(text);
                await this.ShowInfo("SDL validation", $"{sdl.ToSamples().Length} samples generated.");
            }
            catch(Exception ex) 
            {
                await this.ShowError("Error", $"Error validating SDL: {ex.Message}");

            }
        }

        private async void MnuSave_Click(object? sender, Avalonia.Interactivity.RoutedEventArgs e)
        {
            var sf = new SaveFileDialog();
            {
                sf.Filters.Add(new FileDialogFilter { Name = "Signal definition file", Extensions = new System.Collections.Generic.List<string> { "sdl" } });
                
                var file = await sf.ShowAsync(this);
                
                if (string.IsNullOrWhiteSpace(file))
                    return;

                File.WriteAllText(file, editSignal.Document.Text);
            }
        }

        private async void MnuOpen_Click(object? sender, Avalonia.Interactivity.RoutedEventArgs e)
        {
            var sf = new OpenFileDialog();
            {
                sf.Filters.Add(new FileDialogFilter { Name = "Signal definition file", Extensions = new System.Collections.Generic.List<string> { "sdl" } });

                var file = (await sf.ShowAsync(this))?.FirstOrDefault();

                if (string.IsNullOrWhiteSpace(file))
                    return;

                string data = File.ReadAllText(file);
                editSignal.Document = new AvaloniaEdit.Document.TextDocument(data);

            }
        }

        private async void MnuNew_Click(object? sender, Avalonia.Interactivity.RoutedEventArgs e)
        {
            if(await this.ShowConfirm("New document", "Are you sure that you want to discard the current document and create a new empty one?"))
                editSignal.Document = new AvaloniaEdit.Document.TextDocument();
        }

        private void SignalComposerDialog_PointerWheelChanged(object? sender, Avalonia.Input.PointerWheelEventArgs e)
        {
            if (e.KeyModifiers.HasFlag(Avalonia.Input.KeyModifiers.Control))
            {
                UpdateFontSize(e.Delta.Y > 0);
                e.Handled = true;
            }

        }
        public void UpdateFontSize(bool increase)
        {
            double currentSize = editSignal.FontSize;

            if (increase)
            {
                if (currentSize < FONT_MAX_SIZE)
                {
                    double newSize = Math.Min(FONT_MAX_SIZE, currentSize + 1);
                    editSignal.FontSize = newSize;
                }
            }
            else
            {
                if (currentSize > FONT_MIN_SIZE)
                {
                    double newSize = Math.Max(FONT_MIN_SIZE, currentSize - 1);
                    editSignal.FontSize = newSize;
                }
            }
        }

        private void SignalComposerDialog_Opened(object? sender, System.EventArgs e)
        {
            editSignal.Focus();
        }

    }
}
