from grammar_parser import GrammarParser, Terminal, NonTerminal, Sequence, Alternative, Repetition, Optional, Rule
from typing import Dict, Set, List, Tuple, Optional as OptionalType
from dataclasses import dataclass
from lexer_generator import lexer_code
import os
import time

@dataclass
class TokenConfig:
    name: str
    token_type: str
    parser_method: str

#initializing the ParserGenerator class, using GrammarParser class to parse the input grammar.
#Running this program will automatically generate a parser for the JACK language.
class ParserGenerator:
    def __init__(self, grammar: str, token_config: Dict[str, Dict[str, Tuple[str, str]]] = None):
        parser = GrammarParser(grammar)
        self.ast = parser.parse_grammar()
        print(self.ast)
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

        self.preprocess_grammar()
        
        self.collect_terminals()

    # Preprocess the grammar to rename 'number' to 'integerConstant'
    def preprocess_grammar(self):
        rule_map = {rule.name: rule for rule in self.ast}
        number_rule = rule_map.get('number')
        digit_rule = rule_map.get('digit')

        if number_rule and digit_rule:
            if self._is_digit_sequence(number_rule.definition):
                self._rename_nonterminal('number', 'integerConstant')

    def _is_digit_sequence(self, definition):
        if isinstance(definition, Sequence):
            items = definition.items
            return (
                len(items) >= 1 and 
                isinstance(items[0], NonTerminal) and items[0].name == 'digit' and
                (len(items) == 1 or (
                    isinstance(items[1], Repetition) and 
                    isinstance(items[1].item, NonTerminal) and 
                    items[1].item.name == 'digit'))
            )
        return False

    def _rename_nonterminal(self, old_name: str, new_name: str):
        def rename(node):
            if isinstance(node, NonTerminal) and node.name == old_name:
                node.name = new_name
                return Terminal(new_name)
            return None  

        #function used to traverse the AST 
        def traverse(node):
            if isinstance(node, (Sequence, Alternative)):
                children = node.items if isinstance(node, Sequence) else node.options
                for i, child in enumerate(children):
                    replacement = traverse(child)
                    if replacement:
                        children[i] = replacement
            elif isinstance(node, (Repetition, Optional)):
                replacement = traverse(node.item)
                if replacement:
                    node.item = replacement
            return rename(node)

        for rule in self.ast:
            traverse(rule.definition)

    # Collect terminals and keywords from the grammar
    def collect_terminals(self):
        #visits each node collecting the terminal
        def visit(node):
            if isinstance(node, Terminal):
                special_tokens = self.token_config.get('special_tokens', {}).keys()
                if node.value in special_tokens:
                    return
                
                if node.value.isalpha():
                    self.keywords.add(node.value)
                else:
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

    #collects all operators and stores them
    def extract_operators(self, node) -> List[str]:
        operators = []
        if isinstance(node, Alternative):
            for option in node.options:
                if isinstance(option, Terminal) and not option.value.isalpha():
                    operators.append(option.value)
            for option in node.options:
                operators.extend(self.extract_operators(option))
        elif isinstance(node, Sequence):
            for item in node.items:
                operators.extend(self.extract_operators(item))
        return operators

    #This is the main code that generates the parser code. It uses the AST generated from the grammar to create specialized functions.
    def generate_node_code(self, node) -> str:
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
            if node.name == 'integerConstant':
                token_type, parser_method = self.token_config['special_tokens']['integerConstant']
                return f'self.{parser_method}()'
            return f'self.parse_{node.name}()'
            
        elif isinstance(node, Sequence):
            parts = []
            for item in node.items:
                part = self.generate_node_code(item)
                if isinstance(item, Alternative):
                    part = f'({part})'
                parts.append(part)
            return ' and '.join(parts)
            
        elif isinstance(node, Alternative):
            parts = []
            for option in node.options:
                part = self.generate_node_code(option)
                if isinstance(option, Sequence):
                    part = f'({part})'
                parts.append(part)
            return ' or '.join(parts)
            
        elif isinstance(node, Repetition):
            inner = self.generate_node_code(node.item)
            if isinstance(node.item, (Alternative, Sequence)):
                inner = f'({inner})'
            return f'self.repeat_parse(lambda: {inner})'
            
        elif isinstance(node, Optional):
            inner = self.generate_node_code(node.item)
            if isinstance(node.item, (Alternative, Sequence)):
                inner = f'({inner})'
            return f'({inner} or True)'
            
        else:
            raise Exception(f'Unknown node type: {type(node)}')

    # This function generates the header for the parser class, including the initialization of keywords and symbols.
    def generate_parser_header(self) -> str:
        return f'''from generated_parser.Lexer import StandardLexer, TokenType, Token

class GeneratedParser:
    def __init__(self, text: str):
        self.keywords = {self.keywords}
        self.symbols = {self.symbols}
        self.lexer = StandardLexer(text, self.keywords)
        self.current_token = None
        self.next_token()
        self.memoization_cache = {{}}
        self.error_recovery_points = set()'''

    #seperate function for generating the error handling code
    def generate_error_handling(self) -> str:
        return '''
    def error(self, expected=None):
        token = self.current_token
        line = self.lexer.line
        column = self.lexer.column
        
        error_context = self.get_error_context()
        
        msg = f"Syntax error at line {line}, column {column}\\n"
        msg += f"Got: {token.type}({token.value})\\n"
        if expected:
            msg += f"Expected: {expected}\\n"
        msg += f"Context:\\n{error_context}"
        
        if self.try_error_recovery():
            msg += "\\nAttempted error recovery and continued parsing."
        
        raise SyntaxError(msg)
    
    def get_error_context(self):
        lines = self.lexer.text.split('\\n')
        if self.lexer.line <= len(lines):
            error_line = lines[self.lexer.line - 1]
            pointer = ' ' * (self.lexer.column - 1) + '^'
            return f"{error_line}\\n{pointer}"
        return "Context not available"
        
    def try_error_recovery(self):
        while self.current_token.type != TokenType.EOF:
            if self.current_token.value in self.error_recovery_points:
                self.next_token()
                return True
            self.next_token()
        return False'''

    # This function generates the parser methods for matching and parsing tokens.
    def generate_parser_methods(self) -> str:
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
        
    def repeat_parse(self, parse_fn):
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
        parser_code = self.generate_parser_header()
        
        parser_code += self.generate_error_handling()
        
        parser_code += self.generate_parser_methods()

        skip_rules = set()
        #skip rules that have been preprocessed
        if any(rule.name == 'integerConstant' for rule in self.ast) or any(
            isinstance(node, NonTerminal) and node.name == 'integerConstant' 
            for rule in self.ast 
            for node in self.get_all_nodes(rule.definition)):
            skip_rules.add('digit')
            
        #creates the specialised functions. Each function is called parse_<rule_name>.
        for rule in self.ast:
            if rule.name in skip_rules:
                continue
                
            method = f'''
    def parse_{rule.name}(self):
        pos_start = self.lexer.pos
        if {self.generate_node_code(rule.definition)}:
            return True
        self.lexer.pos = pos_start
        return False
'''
            parser_code += method

        #This is the code that will be used to test the generated parser.
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
        
    def get_all_nodes(self, node):
        nodes = [node]
        if isinstance(node, (Sequence, Alternative)):
            for child in node.items if isinstance(node, Sequence) else node.options:
                nodes.extend(self.get_all_nodes(child))
        elif isinstance(node, (Repetition, Optional)):
            nodes.extend(self.get_all_nodes(node.item))
        return nodes

def main():
    with open('../tests/jack_language_tests/jack_grammar.txt', 'r') as f:
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
    start_time = time.time()
    
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
    final_time = time.time()
    print(f"Parser generated in {final_time - start_time:.8f} seconds")

if __name__ == "__main__":
    main()