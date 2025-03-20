from grammar_parser import GrammarParser, Terminal, NonTerminal, Sequence, Alternative, Repetition, Optional, Rule
from typing import Dict, Set, List, Tuple, Optional as OptionalType
from dataclasses import dataclass
from lexer_generator import lexer_code
import os

@dataclass
class TokenConfig:
    name: str
    token_type: str
    parser_method: str

class ParserGenerator:
    def __init__(self, grammar: str, token_config: Dict[str, Dict[str, Tuple[str, str]]] = None):
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

        # Before we collect terminals, preprocess grammar to replace number/digit rules with integerConstant
        self._preprocess_grammar()
        
        self.precedence_rules = self._generate_precedence_rules(self.ast)
        self._collect_terminals()

    def _preprocess_grammar(self):
        """
        Preprocess the grammar to detect and handle number/digit patterns,
        replacing them with integerConstant where appropriate
        """
        # First identify if we have number and digit rules
        number_rule = None
        digit_rule = None
        
        for rule in self.ast:
            if rule.name == 'number':
                number_rule = rule
            elif rule.name == 'digit':
                digit_rule = rule
                
        # If we have both number and digit rules, check their pattern
        if number_rule and digit_rule:
            # Check if number rule matches the pattern: digit, {digit}
            if self._is_digit_sequence_pattern(number_rule, digit_rule):
                # Find all references to 'number' and replace with 'integerConstant'
                self._replace_number_with_integer_constant()
                
    def _is_digit_sequence_pattern(self, number_rule, digit_rule):
        """Check if number rule follows the pattern: digit, {digit}"""
        try:
            # Check if number_rule definition is a sequence
            if isinstance(number_rule.definition, Sequence):
                items = number_rule.definition.items
                # Check if first item is a reference to digit
                if len(items) >= 1 and isinstance(items[0], NonTerminal) and items[0].name == 'digit':
                    # Check if second item is a repetition of digit (if it exists)
                    if len(items) >= 2:
                        return (isinstance(items[1], Repetition) and 
                                isinstance(items[1].item, NonTerminal) and 
                                items[1].item.name == 'digit')
                    return True  # Just a single digit is also fine
            return False
        except:
            return False  # If any exception occurs, just return False
            
    def _replace_number_with_integer_constant(self):
        """Replace all references to 'number' with 'integerConstant'"""
        # We'll modify rules that reference 'number'
        for rule in self.ast:
            self._replace_number_in_node(rule.definition)
            
    def _replace_number_in_node(self, node):
        """Recursively replace NonTerminal('number') with Terminal('integerConstant')"""
        if isinstance(node, NonTerminal) and node.name == 'number':
            # This is a direct replacement - may need to preserve attributes
            node.name = 'integerConstant'
            # Convert NonTerminal to Terminal
            return Terminal('integerConstant')
            
        # Recursively process other node types
        elif isinstance(node, Sequence):
            for i, item in enumerate(node.items):
                replacement = self._replace_number_in_node(item)
                if replacement:
                    node.items[i] = replacement
        elif isinstance(node, Alternative):
            for i, option in enumerate(node.options):
                replacement = self._replace_number_in_node(option)
                if replacement:
                    node.options[i] = replacement
        elif isinstance(node, Repetition):
            replacement = self._replace_number_in_node(node.item)
            if replacement:
                node.item = replacement
        elif isinstance(node, Optional):
            replacement = self._replace_number_in_node(node.item)
            if replacement:
                node.item = replacement
                
        return None  # No replacement needed

    def _collect_terminals(self):
        """Collect all terminal symbols and keywords from the grammar"""
        def visit(node):
            if isinstance(node, Terminal):
                # Check if the terminal is a special token
                special_tokens = self.token_config.get('special_tokens', {}).keys()
                if node.value in special_tokens:
                    return  # Skip adding special tokens to keywords or symbols
                
                # Add normal terminals appropriately
                if node.value.isalpha():
                    self.keywords.add(node.value)
                else:
                    # Don't add digit characters as symbols
                    if not node.value.isdigit():
                        self.symbols.add(node.value)
            elif isinstance(node, (Sequence, Alternative)):
                for child in node.items if isinstance(node, Sequence) else node.options:
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
            # Handle any NonTerminal that was changed to 'integerConstant' but not yet converted to Terminal
            if node.name == 'integerConstant':
                token_type, parser_method = self.token_config['special_tokens']['integerConstant']
                return f'self.{parser_method}()'
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
        return f'''from generated_parser.Lexer import StandardLexer, TokenType, Token
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

        # Skip generating code for 'digit' rule if we've converted number to integerConstant
        skip_rules = set()
        if any(rule.name == 'integerConstant' for rule in self.ast) or any(
            isinstance(node, NonTerminal) and node.name == 'integerConstant' 
            for rule in self.ast 
            for node in self._get_all_nodes(rule.definition)):
            skip_rules.add('digit')
            
        for rule in self.ast:
            if rule.name in skip_rules:
                continue
                
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
        
    def _get_all_nodes(self, node):
        """Helper to get all nodes recursively from a grammar node"""
        nodes = [node]
        if isinstance(node, (Sequence, Alternative)):
            for child in node.items if isinstance(node, Sequence) else node.options:
                nodes.extend(self._get_all_nodes(child))
        elif isinstance(node, (Repetition, Optional)):
            nodes.extend(self._get_all_nodes(node.item))
        return nodes

def main():
    with open('../tests/sentence_tests/sentence_grammar.txt', 'r') as f:
        jack_grammar = f.read()
    print(jack_grammar)
    jack_config = {
        'special_tokens': {
            'identifier': ('IDENTIFIER', 'parse_identifier'),
            'integerConstant': ('INTEGER', 'parse_integerConstant'),
            'stringLiteral': ('STRING', 'parse_stringLiteral'),
        },
        'keyword_type': 'KEYWORD',
        'symbol_type': 'SYMBOL'
    }
    
    generator = ParserGenerator(jack_grammar, jack_config)
    parser_code = generator.generate_parser_code()
    
    try:
        os.mkdir("generated_parser")
    except FileExistsError:
        print(f"Directory 'generated_parser' already exists.")

    with open('generated_parser/generated_parser.py', 'w') as f:
        f.write(parser_code)

    with open('generated_parser/Lexer.py', 'w') as f:
        f.write(lexer_code)
        
    print("Parser generated successfully!")

if __name__ == "__main__":
    main()