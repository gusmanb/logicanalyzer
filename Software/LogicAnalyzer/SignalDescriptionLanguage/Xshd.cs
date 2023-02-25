using System.Text;
using System.Xml;

namespace SignalDescriptionLanguage
{
    public static class Xshd
    {
        const string sdlDef = @"<SyntaxDefinition name=""SignalDescriptionLanguage""
        xmlns=""http://icsharpcode.net/sharpdevelop/syntaxdefinition/2008"">
    <Color name=""Group"" foreground=""#00fa9a"" />
    <Color name=""GroupName"" foreground=""#afeeee"" />
    <Color name=""ValueSignal"" foreground=""#00bfff"" />
    <Color name=""Number"" foreground=""#ff8c00"" />
    <Color name=""HexNumber"" foreground=""#ffa0cc"" />
    <Color name=""Separators"" foreground=""#ff6347"" />
    <Color name=""Comment"" foreground=""#00ef00"" />
    <Color name=""StartValue"" foreground=""Yellow"" />
    <Color name=""String"" foreground=""#d69d85"" />
    <RuleSet>
        <Keywords color=""Group"">
            <Word>{</Word>
            <Word>}</Word>
        </Keywords>
        <Keywords color=""Separators"">
            <Word>,</Word>
            <Word>;</Word>
        </Keywords>
        <Span begin=""&lt;"" end=""&gt;"" color=""GroupName"" />
        <Span begin=""\["" end=""\]"" color=""GroupName"" />
        <Span color=""Comment"">
			<Begin>//</Begin>
		</Span>
		<Span color=""Comment"" multiline=""true"">
			<Begin>/\*</Begin>
			<End>\*/</End>
		</Span>
        <Span color=""String"">
			<Begin>""</Begin>
			<End>""</End>
            <RuleSet>
				<Span begin=""\\"" end="".""/>
			</RuleSet>
		</Span>
        <Rule color=""ValueSignal"">
            (h|l|H|L|!|=|b|B|s|S)
        </Rule>
        <Rule color=""HexNumber"">
            0x[0-9a-fA-F]+
        </Rule>
        <Rule color=""Number"">
            [0-9]
        </Rule>
        <Rule color=""StartValue"">
            \$
        </Rule>
    </RuleSet>
</SyntaxDefinition>";

        public static string AsString { get { return sdlDef; } }
        public static Stream AsStream { get { return new MemoryStream(Encoding.UTF8.GetBytes(sdlDef)); } }
        public static XmlReader AsReader 
        {
            get 
            {
                var stream = AsStream;
                var reader = new XmlTextReader(stream);
                return reader;
            }
        }
    }
}