from typing import Dict, Set, List, Tuple, Union
from dataclasses import dataclass
from grammar_types import Terminal, NonTerminal, Sequence, Alternative, Repetition, Optional, Rule
from bnf_parser import BNFParser
from GrammarParser import GrammarParser
from bnfConverter import BNFtoEBNFConverter

@dataclass
class TokenConfig:
    name: str
    token_type: str
    parser_method: str

class ParserGenerator:
    def __init__(self, grammar: str, token_config: Dict[str, Tuple[str, str]] = None):
        print("Input Grammar:")
        print(grammar)
        print("\nDetecting grammar format...")
        
        # Detect if the grammar is BNF
        if self._is_bnf_grammar(grammar):
            print("Grammar detected as: BNF")
            try:
                print("Converting BNF to EBNF format...")
                converter = BNFParser(grammar)
                self.ast = converter.parse_grammar()
                print(grammar)
                print("BNF successfully converted to EBNF.")
            except Exception as e:
                raise ValueError(f"Error parsing BNF: {e}")
        else:
            print("Grammar detected as: EBNF")
            # Always use the EBNF parser
            print("Using EBNF Parser with final grammar.")
            parser = GrammarParser(grammar)

            print("\nParsing grammar...")
            self.ast = parser.parse_grammar()

        print(f"Parsing complete. Found {len(self.ast)} rules.")
        
        self.keywords: Set[str] = set()
        self.symbols: Set[str] = set()
        
        self.token_config = token_config if token_config else {
            'special_tokens': {
                'identifier': ('IDENTIFIER', 'parse_identifier'),
                'integerConstant': ('INTEGER', 'parse_integerConstant'),
                'stringLiteral': ('STRING', 'parse_stringLiteral'),
            },
            'keyword_type': 'KEYWORD',
            'symbol_type': 'SYMBOL'
        }

        self.precedence_rules = self._generate_precedence_rules(self.ast)
        self._collect_terminals()


    def _is_bnf_grammar(self, grammar: str) -> bool:
        """
        Detect if the grammar is in BNF format by looking for BNF-specific markers
        """
        # Check for characteristic BNF syntax
        has_angle_brackets = '<' in grammar and '>' in grammar
        has_bnf_assignment = '::=' in grammar
        
        # Check for characteristic EBNF syntax
        has_ebnf_markers = ';' in grammar and '=' in grammar and '::=' not in grammar
        has_ebnf_repetition = '{' in grammar and '}' in grammar and '}*' not in grammar
        
        # If we see clear BNF syntax and don't see exclusive EBNF syntax, it's BNF
        return (has_angle_brackets and has_bnf_assignment) or (
            has_angle_brackets and not has_ebnf_markers and not has_ebnf_repetition
        )

    def _collect_terminals(self):
        """Collect terminal symbols and keywords from the grammar"""
        def visit(node):
            if isinstance(node, Terminal):
                if node.value.isalpha():
                    self.keywords.add(node.value)
                else:
                    self.symbols.add(node.value)
            elif isinstance(node, (Sequence, Alternative)):
                for child in (node.items if isinstance(node, Sequence) else node.options):
                    visit(child)
            elif isinstance(node, (Repetition, Optional)):
                visit(node.item)
            elif isinstance(node, Rule):
                visit(node.definition)

        for rule in self.ast:
            visit(rule)

    def _generate_precedence_rules(self, rules: List[Rule]) -> Dict[str, int]:
        """Generate operator precedence rules from the grammar"""
        precedence = {}
        current_level = 0
        
        for rule in rules:
            if rule.name.endswith('Expression'):
                operators = self._extract_operators(rule.definition)
                for op in operators:
                    precedence[op] = current_level
                current_level += 1
        
        return precedence

    def _extract_operators(self, node) -> List[str]:
        """Extract operators from expression rules"""
        operators = []
        if isinstance(node, Alternative):
            for option in node.options:
                if isinstance(option, Terminal) and not option.value.isalpha():
                    operators.append(option.value)
            for option in node.options:
                operators.extend(self._extract_operators(option))
        elif isinstance(node, Sequence):
            for item in node.items:
                operators.extend(self._extract_operators(item))
        return operators

    # Rest of the ParserGenerator implementation remains the same...
    # (This includes _generate_node_code, _generate_parser_header,
    #  _generate_error_handling, _generate_parser_methods, etc.)

    def _generate_precedence_rules(self, rules: List[Rule]) -> Dict[str, int]:
        precedence = {}
        current_level = 0
        
        for rule in rules:
            if rule.name.endswith('Expression'):
                operators = self._extract_operators(rule.definition)
                for op in operators:
                    precedence[op] = current_level
                current_level += 1
        
        return precedence

    def _extract_operators(self, node) -> List[str]:
        operators = []
        if isinstance(node, Alternative):
            for option in node.options:
                if isinstance(option, Terminal) and not option.value.isalpha():
                    operators.append(option.value)
            for option in node.options:
                operators.extend(self._extract_operators(option))
        elif isinstance(node, Sequence):
            for item in node.items:
                operators.extend(self._extract_operators(item))
        return operators

    def _generate_node_code(self, node) -> str:
        if isinstance(node, Terminal):
            if node.value == "":
                return 'True'
            if 'special_tokens' in self.token_config:
                for token_name, (token_type, parser_method) in self.token_config['special_tokens'].items():
                    if node.value == token_name:
                        return f'self.{parser_method}()'
            if node.value.isalpha():
                return f'self.match(TokenType.{self.token_config["keyword_type"]}, "{node.value}")'
            else:
                return f'self.match(TokenType.{self.token_config["symbol_type"]}, "{node.value}")'
                
        elif isinstance(node, NonTerminal):
            return f'self.parse_{node.name}()'
            
        elif isinstance(node, Sequence):
            parts = []
            for item in node.items:
                part = self._generate_node_code(item)
                if isinstance(item, Alternative):
                    part = f'({part})'
                parts.append(part)
            return ' and '.join(parts)
            
        elif isinstance(node, Alternative):
            parts = []
            for option in node.options:
                part = self._generate_node_code(option)
                if isinstance(option, Sequence):
                    part = f'({part})'
                parts.append(part)
            return ' or '.join(parts)
            
        elif isinstance(node, Repetition):
            inner = self._generate_node_code(node.item)
            if isinstance(node.item, (Alternative, Sequence)):
                inner = f'({inner})'
            return f'self._repeat_parse(lambda: {inner})'
            
        elif isinstance(node, Optional):
            inner = self._generate_node_code(node.item)
            if isinstance(node.item, (Alternative, Sequence)):
                inner = f'({inner})'
            return f'({inner} or True)'
            
        else:
            raise Exception(f'Unknown node type: {type(node)}')

    def _generate_parser_header(self) -> str:
        return f'''from Lexer import StandardLexer, TokenType, Token
import functools

class GeneratedParser:
    def __init__(self, text: str):
        self.keywords = {self.keywords}
        self.symbols = {self.symbols}
        self.lexer = StandardLexer(text, self.keywords)
        self.current_token = None
        self.next_token()
        self._memoization_cache = {{}}
        self.error_recovery_points = set()  # Store sync points for error recovery
    
    @staticmethod
    def memoize(func):
        """Decorator for memoizing parser methods"""
        @functools.wraps(func)
        def wrapper(self, *args, **kwargs):
            cache_key = (func.__name__, self.lexer.pos)
            if cache_key in self._memoization_cache:
                result, new_pos = self._memoization_cache[cache_key]
                self.lexer.pos = new_pos
                return result
            
            start_pos = self.lexer.pos
            result = func(self, *args, **kwargs)
            self._memoization_cache[cache_key] = (result, self.lexer.pos)
            return result
        return wrapper'''

    def _generate_error_handling(self) -> str:
        return '''
    def error(self, expected=None):
        token = self.current_token
        line = self.lexer.line
        column = self.lexer.column
        
        error_context = self._get_error_context()
        
        msg = f"Syntax error at line {line}, column {column}\\n"
        msg += f"Got: {token.type}({token.value})\\n"
        if expected:
            msg += f"Expected: {expected}\\n"
        msg += f"Context:\\n{error_context}"
        
        if self._try_error_recovery():
            msg += "\\nAttempted error recovery and continued parsing."
        
        raise SyntaxError(msg)
    
    def _get_error_context(self):
        lines = self.lexer.text.split('\\n')
        if self.lexer.line <= len(lines):
            error_line = lines[self.lexer.line - 1]
            pointer = ' ' * (self.lexer.column - 1) + '^'
            return f"{error_line}\\n{pointer}"
        return "Context not available"
        
    def _try_error_recovery(self):
        """Attempt to recover from syntax errors by finding synchronization points"""
        while self.current_token.type != TokenType.EOF:
            if self.current_token.value in self.error_recovery_points:
                self.next_token()
                return True
            self.next_token()
        return False'''

    def _generate_parser_methods(self) -> str:
        return '''
    def next_token(self):
        self.current_token = self.lexer.get_next_token()
        
    def match(self, expected_type, expected_value=None):
        if self.current_token.type == expected_type:
            if expected_value is None or self.current_token.value == expected_value:
                token = self.current_token
                self.next_token()
                return True
        return False
        
    def _repeat_parse(self, parse_fn):
        parsed_at_least_once = False
        while True:
            pos = self.lexer.pos
            if not parse_fn():
                self.lexer.pos = pos
                break
            parsed_at_least_once = True
        return True
        
    def parse(self):
        if not self.parse_{0}():
            self.error("valid {0}")
        if self.current_token.type != TokenType.EOF:
            self.error("end of input")
        return True

    def parse_identifier(self):
        return self.match(TokenType.IDENTIFIER)
        
    def parse_integerConstant(self):
        return self.match(TokenType.INTEGER)
        
    def parse_stringLiteral(self):
        return self.match(TokenType.STRING)'''.format(self.ast[0].name)
    
    def _sanitize_rule_name(self, name: str) -> str:
        sanitized = name.replace('-', '_')
        
        if not sanitized[0].isalpha():
            sanitized = 'rule_' + sanitized
        
        return sanitized

    def generate_parser_code(self) -> str:
        parser_code = self._generate_parser_header()
        
        parser_code += self._generate_error_handling()
        
        parser_code += self._generate_parser_methods()

        for rule in self.ast:
            method = f'''
    @memoize
    def parse_{rule.name}(self):
        pos_start = self.lexer.pos
        if {self._generate_node_code(rule.definition)}:
            return True
        self.lexer.pos = pos_start
        return False
'''
            parser_code += method

        parser_code += '''
def test_parser(file_path=None):
    if file_path:
        try:
            with open(file_path, 'r') as file:
                code = file.read()
            print(f"Testing file: {file_path}")
            parser = GeneratedParser(code)
            result = parser.parse()
            print("Successfully parsed file")
            return True
        except FileNotFoundError:
            print(f"File not found: {file_path}")
            return False
        except SyntaxError as e:
            print(f"Syntax error in file: {e}")
            return False
        except Exception as e:
            print(f"Error parsing file: {e}")
            return False

if __name__ == "__main__":
    import sys
    if len(sys.argv) > 1:
        test_parser(sys.argv[1])
    else:
        print("Please provide a file path as an argument")
'''
    
        return parser_code
    


# def main():
#     JACK_GRAMMAR = """
#         classDeclar = "class" , identifier , "{" , { memberDeclar } , "}" ;
#         memberDeclar = classVarDeclar | subroutineDeclar ;
#         classVarDeclar = ("static" | "field") , type , identifier , { "," , identifier } , ";" ;
#         type = "int" | "char" | "boolean" | identifier ;
#         subroutineDeclar = ("constructor" | "function" | "method") , (type | "void") , identifier , "(" , paramList , ")" , subroutineBody ;
#         paramList = (type , identifier , { "," , type , identifier }) | "" ;
#         subroutineBody = "{" , { statement } , "}" ;
#         statement = varDeclarStatement | letStatemnt | ifStatement | whileStatement | doStatement | returnStatemnt ;
#         varDeclarStatement = "var" , type , identifier , { "," , identifier } , ";" ;
#         letStatemnt = "let" , identifier , [ "[" , expression , "]" ] , "=" , expression , ";" ;
#         ifStatement = "if" , "(" , expression , ")" , "{" , { statement } , "}" , [ "else" , "{" , { statement } , "}" ] ;
#         whileStatement = "while" , "(" , expression , ")" , "{" , { statement } , "}" ;
#         doStatement = "do" , subroutineCall , ";" ;
#         subroutineCall = identifier , [ "." , identifier ] , "(" , expressionList , ")" ;
#         expressionList = (expression , { "," , expression }) | "" ;
#         returnStatemnt = "return" , [ expression ] , ";" ;
#         expression = relationalExpression , { ("&" | "|") , relationalExpression } ;
#         relationalExpression = ArithmeticExpression , { ("=" | ">" | "<") , ArithmeticExpression } ;
#         ArithmeticExpression = term , { ("+" | "-") , term } ;
#         term = factor , { ("*" | "/") , factor } ;
#         factor = ("-" | "~" | "") , operand ;
#         operand = integerConstant | 
#                 identifier , [ "." , identifier ] , [ "[" , expression , "]" ] |
#                 identifier , [ "." , identifier ] , "(" , expressionList , ")" |
#                 "(" , expression , ")" |
#                 stringLiteral |
#                 "true" | "false" | "null" | "this" ;
#     """
    
#     jack_config = {
#         'special_tokens': {
#             'identifier': ('IDENTIFIER', 'parse_identifier'),
#             'integerConstant': ('INTEGER', 'parse_integerConstant'),
#             'stringLiteral': ('STRING', 'parse_stringLiteral'),
#         },
#         'keyword_type': 'KEYWORD',
#         'symbol_type': 'SYMBOL'
#     }
    
#     generator = ParserGenerator(JACK_GRAMMAR, jack_config)
#     parser_code = generator.generate_parser_code()
    
#     with open('generated_parser.py', 'w') as f:
#         f.write(parser_code)
        
#     print("Parser generated successfully!")

# if __name__ == "__main__":
#     main()

# def main():
#     # Test with BNF Grammar (C Grammar)
#     C_GRAMMAR = """
#     <translation-unit> ::= {<external-declaration>}*
#     <external-declaration> ::= <function-definition> | <declaration>
#     """
    
#     # Test with EBNF Grammar (JACK Grammar)
#     JACK_GRAMMAR = """
#     classDeclar = "class" , identifier , "{" , { memberDeclar } , "}" ;
#     memberDeclar = classVarDeclar | subroutineDeclar ;
#     """
    
#     # Configuration for C Grammar
#     c_config = {
#         'special_tokens': {
#             'identifier': ('IDENTIFIER', 'parse_identifier'),
#             'integer-constant': ('INTEGER', 'parse_integerConstant'),
#             'string-literal': ('STRING', 'parse_stringLiteral'),
#             'character-constant': ('CHAR', 'parse_characterConstant'),
#             'floating-constant': ('FLOAT', 'parse_floatConstant'),
#         },
#         'keyword_type': 'KEYWORD',
#         'symbol_type': 'SYMBOL'
#     }
    
#     try:
#         # Generate parser from BNF grammar
#         generator = ParserGenerator(C_GRAMMAR, c_config)
#         parser_code = generator.generate_parser_code()
        
#         with open('generated_c_parser.py', 'w') as f:
#             f.write(parser_code)
            
#         print("C Parser generated successfully!")
        
#         # Generate parser from EBNF grammar
#         generator = ParserGenerator(JACK_GRAMMAR)
#         parser_code = generator.generate_parser_code()
        
#         with open('generated_jack_parser.py', 'w') as f:
#             f.write(parser_code)
            
#         print("JACK Parser generated successfully!")
        
#     except Exception as e:
#         print(f"Error generating parser: {e}")

# if __name__ == "__main__":
#     main()

def main():
#     C_GRAMMAR = """
# <translation-unit> ::= {<external-declaration>}*

# <external-declaration> ::= <function-definition>
#                          | <declaration>

# <function-definition> ::= {<declaration-specifier>}* <declarator> {<declaration>}* <compound-statement>

# <declaration-specifier> ::= <storage-class-specifier>
#                           | <type-specifier>
#                           | <type-qualifier>

# <storage-class-specifier> ::= auto
#                             | register
#                             | static
#                             | extern
#                             | typedef

# <type-specifier> ::= void
#                    | char
#                    | short
#                    | int
#                    | long
#                    | float
#                    | double
#                    | signed
#                    | unsigned
#                    | <struct-or-union-specifier>
#                    | <enum-specifier>
#                    | <typedef-name>

# <struct-or-union-specifier> ::= <struct-or-union> <identifier> { {<struct-declaration>}+ }
#                               | <struct-or-union> { {<struct-declaration>}+ }
#                               | <struct-or-union> <identifier>

# <struct-or-union> ::= struct
#                     | union

# <struct-declaration> ::= {<specifier-qualifier>}* <struct-declarator-list>

# <specifier-qualifier> ::= <type-specifier>
#                         | <type-qualifier>

# <struct-declarator-list> ::= <struct-declarator>
#                            | <struct-declarator-list> , <struct-declarator>

# <struct-declarator> ::= <declarator>
#                       | <declarator> : <constant-expression>
#                       | : <constant-expression>

# <declarator> ::= {<pointer>}? <direct-declarator>

# <pointer> ::= * {<type-qualifier>}* {<pointer>}?

# # <type-qualifier> ::= const
# #                    | volatile

# # <direct-declarator> ::= <identifier>
# #                       | ( <declarator> )
# #                       | <direct-declarator> [ {<constant-expression>}? ]
# #                       | <direct-declarator> ( <parameter-type-list> )
# #                       | <direct-declarator> ( {<identifier>}* )

# # <constant-expression> ::= <conditional-expression>

# # <conditional-expression> ::= <logical-or-expression>
# #                            | <logical-or-expression> ? <expression> : <conditional-expression>

# # <logical-or-expression> ::= <logical-and-expression>
# #                           | <logical-or-expression> || <logical-and-expression>

# # <logical-and-expression> ::= <inclusive-or-expression>
# #                            | <logical-and-expression> && <inclusive-or-expression>

# # <inclusive-or-expression> ::= <exclusive-or-expression>
# #                             | <inclusive-or-expression> | <exclusive-or-expression>

# # <exclusive-or-expression> ::= <and-expression>
# #                             | <exclusive-or-expression> ^ <and-expression>

# # <and-expression> ::= <equality-expression>
# #                    | <and-expression> & <equality-expression>

# # <equality-expression> ::= <relational-expression>
# #                         | <equality-expression> == <relational-expression>
# #                         | <equality-expression> != <relational-expression>

# # <relational-expression> ::= <shift-expression>
# #                           | <relational-expression> < <shift-expression>
# #                           | <relational-expression> > <shift-expression>
# #                           | <relational-expression> <= <shift-expression>
# #                           | <relational-expression> >= <shift-expression>

# # <shift-expression> ::= <additive-expression>
# #                      | <shift-expression> << <additive-expression>
# #                      | <shift-expression> >> <additive-expression>

# # <additive-expression> ::= <multiplicative-expression>
# #                         | <additive-expression> + <multiplicative-expression>
# #                         | <additive-expression> - <multiplicative-expression>

# # <multiplicative-expression> ::= <cast-expression>
# #                               | <multiplicative-expression> * <cast-expression>
# #                               | <multiplicative-expression> / <cast-expression>
# #                               | <multiplicative-expression> % <cast-expression>

# # <cast-expression> ::= <unary-expression>
# #                     | ( <type-name> ) <cast-expression>

# # <unary-expression> ::= <postfix-expression>
# #                      | ++ <unary-expression>
# #                      | -- <unary-expression>
# #                      | <unary-operator> <cast-expression>
# #                      | sizeof <unary-expression>
# #                      | sizeof <type-name>

# # <postfix-expression> ::= <primary-expression>
# #                        | <postfix-expression> [ <expression> ]
# #                        | <postfix-expression> ( {<assignment-expression>}* )
# #                        | <postfix-expression> . <identifier>
# #                        | <postfix-expression> -> <identifier>
# #                        | <postfix-expression> ++
# #                        | <postfix-expression> --

# # <primary-expression> ::= <identifier>
# #                        | <constant>
# #                        | <string>
# #                        | ( <expression> )

# # <constant> ::= <integer-constant>
# #              | <character-constant>
# #              | <floating-constant>
# #              | <enumeration-constant>

# # <expression> ::= <assignment-expression>
# #                | <expression> , <assignment-expression>

# # <assignment-expression> ::= <conditional-expression>
# #                           | <unary-expression> <assignment-operator> <assignment-expression>

# # <assignment-operator> ::= =
# #                         | *=
# #                         | /=
# #                         | %=
# #                         | +=
# #                         | -=
# #                         | <<=
# #                         | >>=
# #                         | &=
# #                         | ^=
# #                         | |=

# # <unary-operator> ::= &
# #                    | *
# #                    | +
# #                    | -
# #                    | ~
# #                    | !

# # <type-name> ::= {<specifier-qualifier>}+ {<abstract-declarator>}?

# # <parameter-type-list> ::= <parameter-list>
# #                         | <parameter-list> , ...

# # <parameter-list> ::= <parameter-declaration>
# #                    | <parameter-list> , <parameter-declaration>

# # <parameter-declaration> ::= {<declaration-specifier>}+ <declarator>
# #                           | {<declaration-specifier>}+ <abstract-declarator>
# #                           | {<declaration-specifier>}+

# # <abstract-declarator> ::= <pointer>
# #                         | <pointer> <direct-abstract-declarator>
# #                         | <direct-abstract-declarator>

# # <direct-abstract-declarator> ::=  ( <abstract-declarator> )
# #                                | {<direct-abstract-declarator>}? [ {<constant-expression>}? ]
# #                                | {<direct-abstract-declarator>}? ( {<parameter-type-list>}? )

# # <enum-specifier> ::= enum <identifier> { <enumerator-list> }
# #                    | enum { <enumerator-list> }
# #                    | enum <identifier>

# # <enumerator-list> ::= <enumerator>
# #                     | <enumerator-list> , <enumerator>

# # <enumerator> ::= <identifier>
# #                | <identifier> = <constant-expression>

# # <typedef-name> ::= <identifier>

# # <declaration> ::=  {<declaration-specifier>}+ {<init-declarator>}* ;

# # <init-declarator> ::= <declarator>
# #                     | <declarator> = <initializer>

# # <initializer> ::= <assignment-expression>
# #                 | { <initializer-list> }
# #                 | { <initializer-list> , }

# # <initializer-list> ::= <initializer>
# #                      | <initializer-list> , <initializer>

# # <compound-statement> ::= { {<declaration>}* {<statement>}* }

# # <statement> ::= <labeled-statement>
# #               | <expression-statement>
# #               | <compound-statement>
# #               | <selection-statement>
# #               | <iteration-statement>
# #               | <jump-statement>

# # <labeled-statement> ::= <identifier> : <statement>
# #                       | case <constant-expression> : <statement>
# #                       | default : <statement>

# # <expression-statement> ::= {<expression>}? ;

# # <selection-statement> ::= if ( <expression> ) <statement>
# #                         | if ( <expression> ) <statement> else <statement>
# #                         | switch ( <expression> ) <statement>

# # <iteration-statement> ::= while ( <expression> ) <statement>
# #                         | do <statement> while ( <expression> ) ;
# #                         | for ( {<expression>}? ; {<expression>}? ; {<expression>}? ) <statement>

# # <jump-statement> ::= goto <identifier> ;
# #                    | continue ;
# #                    | break ;
# #                    | return {<expression>}? ;
# #     """  
    
    C_GRAMMAR = """
translationunit = { externaldeclaration } ;

externaldeclaration = functiondefinition | declaration ;

functiondefinition = { declarationspecifier } , declarator , { declaration } , compoundstatement ;

declarationspecifier = storageclassspecifier 
                    | typespecifier 
                    | typequalifier ;

storageclassspecifier = "auto" 
                     | "register" 
                     | "static" 
                     | "extern" 
                     | "typedef" ;

typespecifier = "void" 
              | "char" 
              | "short" 
              | "int" 
              | "long" 
              | "float" 
              | "double" 
              | "signed" 
              | "unsigned" 
              | structorunionspecifier 
              | enumspecifier 
              | typedefname ;

structorunionspecifier = structorunion , identifier , "{" , { structdeclaration } , "}" 
                      | structorunion , "{" , { structdeclaration } , "}" 
                      | structorunion , identifier ;

structorunion = "struct" | "union" ;

structdeclaration = { specifierqualifier } , structdeclaratorlist ;

specifierqualifier = typespecifier 
                  | typequalifier ;

structdeclaratorlist = structdeclarator 
                    | structdeclaratorlist , "," , structdeclarator ;

structdeclarator = declarator 
                | declarator , ":" , constantexpression 
                | ":" , constantexpression ;

declarator = [ pointer ] , directdeclarator ;

pointer = "*" , { typequalifier } , [ pointer ] ;

typequalifier = "const" | "volatile" ;
"""
    

    # C-specific token configuration
    c_config = {
        'special_tokens': {
            'identifier': ('IDENTIFIER', 'parse_identifier'),
            'integer-constant': ('INTEGER', 'parse_integerConstant'),
            'character-constant': ('CHAR', 'parse_characterConstant'),
            'floating-constant': ('FLOAT', 'parse_floatConstant'),
            'string': ('STRING', 'parse_stringLiteral'),
            'enumeration-constant': ('ENUM', 'parse_enumeration_constant')
        },
        'keyword_type': 'KEYWORD',
        'symbol_type': 'SYMBOL'
    }
    
    generator = ParserGenerator(C_GRAMMAR, c_config)
    parser_code = generator.generate_parser_code()
    
    with open('generated_c_parser.py', 'w') as f:
        f.write(parser_code)
        
    print("C Parser generated successfully!")

if __name__ == "__main__":
    main()
