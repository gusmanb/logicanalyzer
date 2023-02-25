using System;
using System.Collections.Generic;
using System.Diagnostics.SymbolStore;
using System.Globalization;
using System.IO;
using System.Linq;
using System.Net.Http.Headers;
using System.Text;
using System.Text.RegularExpressions;
using System.Threading.Tasks;
using static SignalDescriptionLanguage.SDLParser;

namespace SignalDescriptionLanguage
{
    public static class SDLParser
    {
        const string numExpr = "(0x)?[0-9a-fA-F]+";
        const string valExpr = $"([hlHL!=]{numExpr})";
        const string byteExpr = $"([bB]{numExpr})";
        const string strExpr = "([sS]\"([^\"\\\\]|\\\\.)+\")";
        const string nameExpr = "(\\[[0-9a-zA-Z]+\\])";

        static Regex initialReg = new Regex("^\\$[01]$");
        static Regex valueReg = new Regex($"^{valExpr}$");
        static Regex byteReg = new Regex($"^{byteExpr}$");
        static Regex strReg = new Regex($"^{strExpr}$");
        static Regex nameReg = new Regex($"^{nameExpr}$");

        static Regex groupReg = new($"^{{((<[0-9a-zA-Z]+>,)?((\\s*({nameExpr}|{valExpr}|{byteExpr}|{strExpr})\\s*[,}}])+))(?<=}})({numExpr})$");
        
        static Regex commentReg = new Regex("//.*$", RegexOptions.Multiline);
        static Regex commentBlockReg = new Regex("/\\*.*?\\*/");

        public static IToken[] GetTokens(string Input)
        {

            string clean = commentReg.Replace(Input, "");
            clean = clean.Replace("\r", "").Replace("\n", "");
            clean = commentBlockReg.Replace(clean, "");

            string semicolonScape = Guid.NewGuid().ToString();

            var escaped = clean.Replace("\\;", semicolonScape);

            string[] sTokens = escaped.Split(';', StringSplitOptions.RemoveEmptyEntries);

            for (int buc = 0; buc < sTokens.Length; buc++)
                sTokens[buc] = sTokens[buc].Trim().Replace(semicolonScape, "\\;");

            List<IToken> tokens = new List<IToken>();

            foreach(var token in sTokens) 
            {
                var type = GetTokenType(token);

                switch(type) 
                {
                    case TokenType.InitialValue:
                        tokens.Add(new InitialToken(token));
                        break;
                    case TokenType.Value:
                        tokens.Add(new ValueToken(token));
                        break;
                    case TokenType.Byte:
                        tokens.Add(new ByteToken(token));
                        break;
                    case TokenType.String:
                        tokens.Add(new StringToken(token));
                        break;
                    case TokenType.Group:
                        tokens.Add(new GroupToken(token));
                        break;
                    case TokenType.GroupName: 
                        tokens.Add(new GroupNameToken(token));
                        break;
                    default:
                        throw new InvalidTokenException($"Invalid token found (\"{token}\").");
                }
            }

            return tokens.ToArray();

        }

        public static TokenType GetTokenType(string Token)
        {
            if(initialReg.IsMatch(Token))
                return TokenType.InitialValue;

            if (valueReg.IsMatch(Token))
                return TokenType.Value;

            if (byteReg.IsMatch(Token))
                return TokenType.Byte;

            if (strReg.IsMatch(Token))
                return TokenType.String;

            if (nameReg.IsMatch(Token))
                return TokenType.GroupName;

            if(groupReg.IsMatch(Token))
                return TokenType.Group;

            return TokenType.None;
        }

        public static bool[] GetSamples(ValueToken Token, ref bool SignalState)
        {
            bool[] samples = new bool[Token.Value];
            switch (Token.ValueType)
            {
                case ValueTokenType.High:
                    SignalState = true;
                    break;
                case ValueTokenType.Low:
                    SignalState = false;
                    break;
                case ValueTokenType.Equal:
                    break;
                case ValueTokenType.Invert:
                    SignalState = !SignalState;
                    break;
                default:

                    throw new InvalidTokenException($"Invalid value token type: {Token.ValueType}");
            }

            Array.Fill(samples, SignalState);
            return samples;
        }

        public static bool[] GetSamples(ByteToken Token, IEnumerable<GroupToken> NamedGroups, ref bool SignalState)
        {
            return GetByteSamples(Token.Value, Token.ByteType == ByteTokenType.ByteLM, NamedGroups, ref SignalState);
        }

        public static bool[] GetSamples(StringToken Token, IEnumerable<GroupToken> NamedGroups, ref bool SignalState)
        {
            string unEscaped = UnescapeString(Token.Value);

            byte[] bytes = Encoding.ASCII.GetBytes(unEscaped);

            List<bool> samples = new List<bool>();

            foreach (byte b in bytes)
                samples.AddRange(GetByteSamples(b, Token.StringType == StringTokenType.StringLM, NamedGroups, ref SignalState));

            return samples.ToArray();
        }

        private static string UnescapeString(string Value)
        {
            return Value.Replace("\\a", "\a")
                .Replace("\\b", "\b")
                .Replace("\\f", "\f")
                .Replace("\\n", "\n")
                .Replace("\\r", "\r")
                .Replace("\\t", "\t")
                .Replace("\\v", "\v")
                .Replace("\\\\", "\\")
                .Replace("\\\"", "\"")
                .Replace("\\;", ";")
                .Replace("\\,", ",");
        }

        private static bool[] GetByteSamples(byte Value, bool LSBtoMSB, IEnumerable<GroupToken> NamedGroups, ref bool SignalState)
        {
            List<bool> byteSamples = new List<bool>();

            var zeroGroup = NamedGroups.FirstOrDefault(g => g.GroupName == "0");
            var oneGroup = NamedGroups.FirstOrDefault(g => g.GroupName == "1");

            if (zeroGroup == null || oneGroup == null)
                throw new MissingGroupException("Found byte/string value but groups \"0\"/\"1\" are missing.");

            for (int buc = 0; buc < 8; buc++)
            {
                if ((Value & (LSBtoMSB ? (1 << buc) : (128 >> buc))) == 0)
                    byteSamples.AddRange(GetSamples(zeroGroup, NamedGroups, ref SignalState));
                else
                    byteSamples.AddRange(GetSamples(oneGroup, NamedGroups, ref SignalState));
            }

            return byteSamples.ToArray();
        }

        public static bool[] GetSamples(GroupNameToken Token, IEnumerable<GroupToken> NamedGroups, ref bool SignalState)
        {
            var group = NamedGroups.FirstOrDefault(g => g.GroupName == Token.Name);

            if (group == null)
                throw new MissingGroupException($"Cannot find a group named \"{Token.Name}\".");

            return GetSamples(group, NamedGroups, ref SignalState);
        }

        public static bool[] GetSamples(GroupToken Group, IEnumerable<GroupToken> NamedGroups, ref bool SignalState)
        {
            List<bool> samples = new List<bool>();

            for (int buc = 0; buc < Group.Repeats; buc++)
            {
                foreach (var token in Group.Tokens)
                {
                    switch (token.TokenType)
                    {
                        case TokenType.Value:
                            samples.AddRange(GetSamples((ValueToken)token, ref SignalState));
                            break;
                        case TokenType.Byte:
                            samples.AddRange(GetSamples((ByteToken)token, NamedGroups, ref SignalState));
                            break;
                        case TokenType.String:
                            samples.AddRange(GetSamples((StringToken)token, NamedGroups, ref SignalState));
                            break;
                        case TokenType.GroupName:
                            samples.AddRange(GetSamples((GroupNameToken)token, NamedGroups, ref SignalState));
                            break;
                        default:
                            throw new InvalidTokenException($"Found invalid token in group: \"{token.Source}\"");
                    }
                }
            }

            return samples.ToArray();
        }

        private static int NumberParse(string Input)
        {
            if (string.IsNullOrWhiteSpace(Input))
                throw new InvalidNumberException($"Number has an incorrect value: {Input}");

            if (Input.Length > 2 && Input.Substring(0, 2).ToLower() == "0x")
            {
                if (Input.Length < 3)
                    throw new InvalidNumberException($"Number has an incorrect value: {Input}");

                string hexNum = Input.Substring(2, Input.Length - 2);
                int res;

                if (!int.TryParse(hexNum, System.Globalization.NumberStyles.HexNumber, CultureInfo.InvariantCulture, out res))
                    throw new InvalidNumberException($"Cannot parse hex number: {Input}");

                return res;
            }
            else
            {
                int res;

                if (!int.TryParse(Input, out res))
                    throw new InvalidNumberException($"Cannot parse decimal number: {Input}");

                return res;
            }
        }

        #region Enumerations
        public enum TokenType
        {
            None,
            InitialValue,
            Group,
            GroupName,
            Value,
            Byte,
            String
        }
        public enum ValueTokenType
        { 
            None,
            High,
            Low,
            Invert,
            Equal
        }
        public enum ByteTokenType
        {
            ByteLM,
            ByteML
        }
        public enum StringTokenType
        {
            StringLM,
            StringML
        }
        #endregion

        #region Token definitions
        public interface IToken
        {
            public string Source { get; }
            public TokenType TokenType { get; }
        }
        public class InitialToken : IToken
        {
            public string Source { get; private set; }
            public InitialToken(string Input)
            {
                if (string.IsNullOrWhiteSpace(Input) || Input.Length < 2 || GetTokenType(Input) != TokenType.InitialValue)
                    throw new InvalidTokenException($"Token is not an initial token (\"{Input}\").");

                int val = NumberParse(Input.Substring(1));

                if (val < 0 || val > 1)
                    throw new InvalidTokenException("Start condition must be \"0\" or \"1\".");

                Value = val == 0 ? false : true;
                Source = Input;
            }
            public TokenType TokenType { get { return TokenType.InitialValue; } }
            public bool Value { get; set; }
        }
        public class ValueToken : IToken
        {
            public string Source { get; private set; }
            public ValueToken(string Input) 
            {
                if (string.IsNullOrWhiteSpace(Input) || Input.Length < 2 || GetTokenType(Input) != TokenType.Value)
                    throw new InvalidTokenException($"Token is not a value (\"{Input}\").");

                string valType = Input.Substring(0, 1);
                int val = NumberParse(Input.Substring(1));

                if (val < 0)
                    throw new InvalidTokenException($"Value out of range (\"{Input}\")");

                switch (valType)
                {
                    case "h":
                    case "H":
                        ValueType = ValueTokenType.High;
                        break;
                    case "l":
                    case "L":
                        ValueType = ValueTokenType.Low;
                        break;
                    case "!":
                        ValueType = ValueTokenType.Invert;
                        break;
                    case "=":
                        ValueType = ValueTokenType.Equal;
                        break;

                    default:
                        throw new InvalidTokenException("Token is not a value.");

                }

                Value = val;
                Source = Input;
                
            }
            public TokenType TokenType { get { return TokenType.Value; } }
            public ValueTokenType ValueType { get; set; }
            public int Value { get; set; }
        }
        public class ByteToken : IToken
        {
            public string Source { get; private set; }
            public ByteToken(string Input)
            {
                if (string.IsNullOrWhiteSpace(Input) || Input.Length < 2 || GetTokenType(Input) != TokenType.Byte)
                    throw new InvalidTokenException($"Token is not a byte (\"{Input}\").");

                string valType = Input.Substring(0, 1);
                int val = NumberParse(Input.Substring(1));
                if (val < 0 || val > 255)
                    throw new InvalidTokenException($"Byte value out of range (\"{Input}\")");

                if (valType == "b")
                    ByteType = ByteTokenType.ByteLM;
                else
                    ByteType = ByteTokenType.ByteML;

                Value = (byte)val;
                Source = Input;

            }
            public TokenType TokenType { get { return TokenType.Byte; } }
            public ByteTokenType ByteType { get; set; }
            public byte Value { get; set; }
        }
        public class StringToken : IToken
        {
            public string Source { get; private set; }
            public StringToken(string Input)
            {
                if (string.IsNullOrWhiteSpace(Input) || Input.Length < 4 || GetTokenType(Input) != TokenType.String)
                    throw new InvalidTokenException($"Token is not a string (\"{Input}\").");

                string valType = Input.Substring(0, 1);
                string val = Input.Substring(2,Input.Length - 3);

                if (valType == "s")
                    StringType = StringTokenType.StringLM;
                else
                    StringType = StringTokenType.StringML;

                Value = val;
                Source = Input;

            }
            public TokenType TokenType { get { return TokenType.String; } }
            public StringTokenType StringType { get; set; }
            public string Value { get; set; }
        }
        public class GroupNameToken : IToken
        {
            public string Source { get; private set; }
            public GroupNameToken(string Input)
            {
                if (string.IsNullOrWhiteSpace(Input) || Input.Length < 3 || GetTokenType(Input) != TokenType.GroupName)
                    throw new InvalidTokenException($"Token is not a group name (\"{Input}\").");

                Name = Input.Substring(1, Input.Length - 2);
                Source = Input;
            }
            public TokenType TokenType { get { return TokenType.GroupName; } }
            public string Name { get; set; }
        }
        public class GroupToken : IToken
        {
            public string Source { get; private set; }
            public GroupToken(string Input)
            {
                if (string.IsNullOrWhiteSpace(Input) || Input.Length < 3 || GetTokenType(Input) != TokenType.Group)
                    throw new InvalidTokenException($"Token is not a group (\"{Input}\").");

                var match = groupReg.Match(Input);

                string commaScape = Guid.NewGuid().ToString();
                string escaped = match.Groups[3].Value.Replace("\\,", commaScape);

                string[] internalTokens = escaped.Replace("}", "").Split(',');

                for(int buc = 0; buc < internalTokens.Length;buc++)
                    internalTokens[buc] = internalTokens[buc].Trim().Replace(commaScape, "\\,");

                if (!string.IsNullOrWhiteSpace(match.Groups[2].Value))
                    GroupName = match.Groups[2].Value.Replace("<", "").Replace(">", "").Replace(",", "");

                List<IToken> tokens = new List<IToken>();

                foreach (var token in internalTokens)
                {
                    switch (GetTokenType(token))
                    {
                        case TokenType.Value:
                            tokens.Add(new ValueToken(token));
                            break;
                        case TokenType.Byte:
                            tokens.Add(new ByteToken(token));
                            break;
                        case TokenType.String:
                            tokens.Add(new StringToken(token));
                            break;
                        case TokenType.GroupName:
                            tokens.Add(new GroupNameToken(token));
                            break;

                        default:
                            throw new InvalidTokenException($"Invalid token in group (\"{token}\").");
                    }
                }

                if(tokens.Count == 0)
                    throw new InvalidGroupException($"Group contains no tokens (\"{Input}\").");

                Repeats = int.Parse(match.Groups[13].Value);
                Tokens = tokens.ToArray();
                Source = Input;
            }
            public TokenType TokenType { get { return TokenType.Group; } }
            public string? GroupName { get; set; }
            public IToken[] Tokens { get; set; }
            public int Repeats { get; set; }
        }
        #endregion
        /// <summary>
        /// Tokenized SDL class, used to parse and convert a text source to tokens and samples
        /// </summary>
        public class TokenizedSDL
        {
            string source;
            IToken[] tokens;
            public string Source { get { return source; } }
            public IToken[] Tokens
            {
                get
                {
                    return tokens;
                }
            }
            public bool? InitialValue
            {
                get
                {
                    return (tokens.FirstOrDefault(t => t.TokenType == TokenType.InitialValue)
                        as InitialToken)?.Value;
                }
            }
            public ValueToken[] Values
            {
                get
                {
                    return tokens.Where(t => t.TokenType == TokenType.Value)
                        .Cast<ValueToken>().ToArray();
                }
            }
            public ByteToken[] Bytes
            {
                get
                {
                    return tokens.Where(t => t.TokenType == TokenType.Byte)
                        .Cast<ByteToken>().ToArray();
                }
            }
            public StringToken[] Strings
            {
                get
                {
                    return tokens.Where(t => t.TokenType == TokenType.String)
                        .Cast<StringToken>().ToArray();
                }
            }
            public GroupNameToken[] GroupNames
            {
                get
                {
                    return tokens.Where(t => t.TokenType == TokenType.GroupName)
                        .Cast<GroupNameToken>().ToArray();
                }
            }
            public GroupToken[] Groups
            {
                get
                {
                    return tokens.Where(t => t.TokenType == TokenType.Group)
                        .Cast<GroupToken>().ToArray();
                }
            }
            public GroupToken[] NamedGroups
            {
                get
                {
                    return tokens.Where(t => t.TokenType == TokenType.Group &&
                    (!string.IsNullOrWhiteSpace((t as GroupToken).GroupName)))
                        .Cast<GroupToken>().ToArray();
                }
            }
            public TokenizedSDL(string Input)
            {
                source = Input;
                tokens = GetTokens(Input);

                var values = Values;
                var names = GroupNames;
                var groups = Groups;
                var namedGroups = NamedGroups;

                var missingNames = names.Where(n => !namedGroups.Any(ng => ng.GroupName == n.Name)).Select(n => n.Name).ToArray();
                var missingNamesInGroups = groups.SelectMany(g => g.Tokens
                    .Where(t => t.TokenType == TokenType.GroupName)
                    .Cast<GroupNameToken>()
                    .Where(n => !namedGroups.Any(ng => ng.GroupName == n.Name))
                    .Select(n => n.Name))
                    .ToArray();

                List<string> missing = new List<string>();
                if (missingNames != null)
                    missing.AddRange(missingNames);
                if (missingNamesInGroups != null)
                    missing.AddRange(missingNamesInGroups);

                if (missing.Count > 0)
                {
                    string missingString = string.Join(", ", missing.Distinct());
                    throw new MissingGroupException($"Missing named groups: {missingString}");
                }

                var needsBitGroups = (Bytes != null && Bytes.Length > 0) || (Strings != null && Strings.Length > 0);

                if (needsBitGroups)
                {
                    if (!NamedGroups.Any(g => g.GroupName == "0") || !NamedGroups.Any(g => g.GroupName == "1"))
                        throw new MissingGroupException($"Definition contains bytes/strings but groups \"0\"/\"1\" are not defined.");
                }

                var duplicatedNames = namedGroups.GroupBy(g => g.GroupName)
                    .Where(gg => gg.Count() > 1)
                    .Select(gg => gg.Key)
                    .ToArray();

                if (duplicatedNames != null && duplicatedNames.Length > 0)
                    throw new DuplicatedGroupException($"Found duplicated named groups: {string.Join(", ", duplicatedNames)}");
            }
            public bool[] ToSamples(bool? InitialValue = null)
            {
                bool currentState = InitialValue ?? (this.InitialValue ?? false);
                var namedGroups = NamedGroups;
                List<bool> samples = new List<bool>();

                foreach (var token in Tokens)
                {
                    switch(token.TokenType) 
                    {
                        case TokenType.Value:
                            samples.AddRange(GetSamples((ValueToken)token, ref currentState));
                            break;
                        case TokenType.Byte:
                            samples.AddRange(GetSamples((ByteToken)token, namedGroups, ref currentState));
                            break;
                        case TokenType.String:
                            samples.AddRange(GetSamples((StringToken)token, namedGroups, ref currentState));
                            break;
                        case TokenType.GroupName:
                            samples.AddRange(GetSamples((GroupNameToken)token, namedGroups, ref currentState));
                            break;
                        case TokenType.Group:

                            var group = (GroupToken)token;

                            if (!string.IsNullOrWhiteSpace(group.GroupName))
                                continue;

                            samples.AddRange(GetSamples(group, namedGroups, ref currentState));
                            break;

                    }
                }

                return samples.ToArray();
            }
        }

        #region Exceptions
        public class MissingGroupException : Exception 
        {
            public MissingGroupException(string message) : base(message) { }
        }
        public class DuplicatedGroupException : Exception
        {
            public DuplicatedGroupException(string message) : base(message) { }
        }
        public class InvalidTokenException : Exception 
        {
            public InvalidTokenException(string message) : base(message) { }
        }
        public class InvalidGroupException : Exception
        {
            public InvalidGroupException(string message) : base(message) { }
        }
        public class InvalidNumberException : Exception
        {
            public InvalidNumberException(string message) : base(message) { }
        }
        #endregion
    }
}
