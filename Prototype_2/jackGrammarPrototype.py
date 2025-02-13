from GrammarParser import GrammarParser, Terminal, NonTerminal, Sequence, Alternative, Repetition, Optional, Rule
from typing import Dict, Set, List

class ParserGenerator:
    def __init__(self, grammar: str):
        parser = GrammarParser(grammar)
        self.ast = parser.parse_grammar()
        self.keywords: Set[str] = set()
        self.symbols: Set[str] = set()
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

    def _generate_node_code(self, node) -> str:
        if isinstance(node, Terminal):
            if node.value == "":
                return 'True'
            elif node.value == "identifier":
                return 'self.parse_identifier()'
            elif node.value == "integerConstant":
                return 'self.parse_integerConstant()'
            elif node.value == "stringLiteral":
                return 'self.parse_stringLiteral()'
            elif node.value.isalpha():
                return f'self.match(TokenType.KEYWORD, "{node.value}")'
            else:
                return f'self.match(TokenType.SYMBOL, "{node.value}")'
                
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

    def generate_parser_code(self) -> str:
        parser_code = f'''from Lexer import StandardLexer, TokenType, Token

class GeneratedParser:
    def __init__(self, text: str):
        self.keywords = {self.keywords}
        self.symbols = {self.symbols}
        self.lexer = StandardLexer(text, self.keywords)
        self.current_token = None
        self.next_token()
        
    def error(self, expected=None):
        msg = f"Syntax error at line {{self.lexer.line}}, column {{self.lexer.column}}"
        if expected:
            msg += f". Expected {{expected}}"
        if self.current_token:
            msg += f". Got {{self.current_token}}"
        raise SyntaxError(msg)
        
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
        if not self.parse_{self.ast[0].name}():
            self.error("valid class declaration")
        if self.current_token.type != TokenType.EOF:
            self.error("end of input")
        return True

    def parse_identifier(self):
        return self.match(TokenType.IDENTIFIER)
        
    def parse_integerConstant(self):
        return self.match(TokenType.INTEGER)
        
    def parse_stringLiteral(self):
        return self.match(TokenType.STRING)
'''

        # Generate methods for each rule
        for rule in self.ast:
            method = f'''
    def parse_{rule.name}(self):
        pos_start = self.lexer.pos
        if {self._generate_node_code(rule.definition)}:
            return True
        self.lexer.pos = pos_start
        return False
'''
            parser_code += method

        parser_code += self._generate_test_code()
    
        return parser_code

    def _generate_test_code(self) -> str:
        return '''
def test_parser():
    test_program = """class Example {
        field int x;
        
        constructor Example new() {
            let x = 0;
            return this;
        }
        
        method void setX(int val) {
            let x = val;
            return;
        }
    }"""
    
    try:
        parser = GeneratedParser(test_program)
        result = parser.parse()
        print("Parsing successful!")
        return True
    except SyntaxError as e:
        print(f"Parsing failed: {e}")
        return False

if __name__ == "__main__":
    test_parser()
'''

def main():
    JACK_GRAMMAR = """
        classDeclar = "class" , identifier , "{" , { memberDeclar } , "}" ;
        memberDeclar = classVarDeclar | subroutineDeclar ;
        classVarDeclar = ("static" | "field") , type , identifier , { "," , identifier } , ";" ;
        type = "int" | "char" | "boolean" | identifier ;
        subroutineDeclar = ("constructor" | "function" | "method") , (type | "void") , identifier , "(" , paramList , ")" , subroutineBody ;
        paramList = (type , identifier , { "," , type , identifier }) | "" ;
        subroutineBody = "{" , { statement } , "}" ;
        statement = varDeclarStatement | letStatemnt | ifStatement | whileStatement | doStatement | returnStatemnt ;
        varDeclarStatement = "var" , type , identifier , { "," , identifier } , ";" ;
        letStatemnt = "let" , identifier , [ "[" , expression , "]" ] , "=" , expression , ";" ;
        ifStatement = "if" , "(" , expression , ")" , "{" , { statement } , "}" , [ "else" , "{" , { statement } , "}" ] ;
        whileStatement = "while" , "(" , expression , ")" , "{" , { statement } , "}" ;
        doStatement = "do" , subroutineCall , ";" ;
        subroutineCall = identifier , [ "." , identifier ] , "(" , expressionList , ")" ;
        expressionList = (expression , { "," , expression }) | "" ;
        returnStatemnt = "return" , [ expression ] , ";" ;
        expression = relationalExpression , { ("&" | "|") , relationalExpression } ;
        relationalExpression = ArithmeticExpression , { ("=" | ">" | "<") , ArithmeticExpression } ;
        ArithmeticExpression = term , { ("+" | "-") , term } ;
        term = factor , { ("*" | "/") , factor } ;
        factor = ("-" | "~" | "") , operand ;
        operand = integerConstant | 
                identifier , [ "." , identifier ] , [ "[" , expression , "]" ] |
                identifier , [ "." , identifier ] , "(" , expressionList , ")" |
                "(" , expression , ")" |
                stringLiteral |
                "true" | "false" | "null" | "this" ;
    """
    
    generator = ParserGenerator(JACK_GRAMMAR)
    parser_code = generator.generate_parser_code()
    
    with open('generated_parser.py', 'w') as f:
        f.write(parser_code)
        
    print("Parser generated successfully!")

if __name__ == "__main__":
    main()