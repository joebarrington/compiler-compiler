from GrammarParser import GrammarParser, Terminal, NonTerminal, Sequence, Alternative, Repetition, Optional, Rule
from typing import Dict, Set, List, Tuple, Optional as OptionalType
from dataclasses import dataclass

@dataclass
class TokenConfig:
    name: str
    token_type: str
    parser_method: str

class ParserGenerator:
    def __init__(self, grammar: str, token_config: Dict[str, Tuple[str, str]] = None):
        parser = GrammarParser(grammar)
        self.ast = parser.parse_grammar()
        self.keywords: Set[str] = set()
        self.symbols: Set[str] = set()
        
        self.token_config = {
            'special_tokens': {
                'identifier': ('IDENTIFIER', 'parse_identifier'),
                'integerConstant': ('INTEGER', 'parse_integerConstant'),
                'stringLiteral': ('STRING', 'parse_stringLiteral'),
            },
            'keyword_type': 'KEYWORD',
            'symbol_type': 'SYMBOL'
        } if token_config is None else token_config

        self.precedence_rules = self._generate_precedence_rules(self.ast)
        self._collect_terminals()

    def _collect_terminals(self):
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

def main():
    # JACK_GRAMMAR = """
    #     classDeclar = "class" , identifier , "{" , { memberDeclar } , "}" ;
    #     memberDeclar = classVarDeclar | subroutineDeclar ;
    #     classVarDeclar = ("static" | "field") , type , identifier , { "," , identifier } , ";" ;
    #     type = "int" | "char" | "boolean" | identifier ;
    #     subroutineDeclar = ("constructor" | "function" | "method") , (type | "void") , identifier , "(" , paramList , ")" , subroutineBody ;
    #     paramList = (type , identifier , { "," , type , identifier }) | "" ;
    #     subroutineBody = "{" , { statement } , "}" ;
    #     statement = varDeclarStatement | letStatemnt | ifStatement | whileStatement | doStatement | returnStatemnt ;
    #     varDeclarStatement = "var" , type , identifier , { "," , identifier } , ";" ;
    #     letStatemnt = "let" , identifier , [ "[" , expression , "]" ] , "=" , expression , ";" ;
    #     ifStatement = "if" , "(" , expression , ")" , "{" , { statement } , "}" , [ "else" , "{" , { statement } , "}" ] ;
    #     whileStatement = "while" , "(" , expression , ")" , "{" , { statement } , "}" ;
    #     doStatement = "do" , subroutineCall , ";" ;
    #     subroutineCall = identifier , [ "." , identifier ] , "(" , expressionList , ")" ;
    #     expressionList = (expression , { "," , expression }) | "" ;
    #     returnStatemnt = "return" , [ expression ] , ";" ;
    #     expression = relationalExpression , { ("&" | "|") , relationalExpression } ;
    #     relationalExpression = ArithmeticExpression , { ("=" | ">" | "<") , ArithmeticExpression } ;
    #     ArithmeticExpression = term , { ("+" | "-") , term } ;
    #     term = factor , { ("*" | "/") , factor } ;
    #     factor = ("-" | "~" | "") , operand ;
    #     operand = integerConstant | 
    #             identifier , [ "." , identifier ] , [ "[" , expression , "]" ] |
    #             identifier , [ "." , identifier ] , "(" , expressionList , ")" |
    #             "(" , expression , ")" |
    #             stringLiteral |
    #             "true" | "false" | "null" | "this" ;
    # """
    JSON_GRAMMAR = """
    json = object | array ;
    
    object = "{" , [ pair , { "," , pair } ] , "}" ;
    pair = string , ":" , value ;

    array = "[" , [ value , { "," , value } ] , "]" ;

    value = string | number | object | array | "true" | "false" | "null" ;

    string =  { "TEXT" } ;
    number = [ "-" ] , digits , [ "." , digits ] , [ ("e" | "E") , [ "+" | "-" ] , digits ] ;

    digits = digit , { digit } ;
    digit = "0" | "1" | "2" | "3" | "4" | "5" | "6" | "7" | "8" | "9" ;
"""

    jack_config = {
        'special_tokens': {
            'identifier': ('IDENTIFIER', 'parse_identifier'),
            'integerConstant': ('INTEGER', 'parse_integerConstant'),
            'stringLiteral': ('STRING', 'parse_stringLiteral'),
        },
        'keyword_type': 'KEYWORD',
        'symbol_type': 'SYMBOL'
    }
    
    generator = ParserGenerator(JSON_GRAMMAR, jack_config)
    parser_code = generator.generate_parser_code()
    
    with open('generated_parser.py', 'w') as f:
        f.write(parser_code)
        
    print("Parser generated successfully!")

if __name__ == "__main__":
    main()