from generated_parser.Lexer import StandardLexer, TokenType, Token

class GeneratedParser:
    def __init__(self, text: str):
        self.keywords = {'catches', 'cat', 'dog', 'chases', 'the', 'bird', 'a', 'watches'}
        self.symbols = set()
        self.lexer = StandardLexer(text, self.keywords)
        self.current_token = None
        self.next_token()
        self._memoization_cache = {}
        self.error_recovery_points = set()  # Store sync points for error recovery
    

    def error(self, expected=None):
        token = self.current_token
        line = self.lexer.line
        column = self.lexer.column
        
        error_context = self._get_error_context()
        
        msg = f"Syntax error at line {line}, column {column}\n"
        msg += f"Got: {token.type}({token.value})\n"
        if expected:
            msg += f"Expected: {expected}\n"
        msg += f"Context:\n{error_context}"
        
        if self._try_error_recovery():
            msg += "\nAttempted error recovery and continued parsing."
        
        raise SyntaxError(msg)
    
    def _get_error_context(self):
        lines = self.lexer.text.split('\n')
        if self.lexer.line <= len(lines):
            error_line = lines[self.lexer.line - 1]
            pointer = ' ' * (self.lexer.column - 1) + '^'
            return f"{error_line}\n{pointer}"
        return "Context not available"
        
    def _try_error_recovery(self):
        """Attempt to recover from syntax errors by finding synchronization points"""
        while self.current_token.type != TokenType.EOF:
            if self.current_token.value in self.error_recovery_points:
                self.next_token()
                return True
            self.next_token()
        return False
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
        if not self.parse_sentence():
            self.error("valid sentence")
        if self.current_token.type != TokenType.EOF:
            self.error("end of input")
        return True

    def parse_identifier(self):
        return self.match(TokenType.IDENTIFIER)
        
    def parse_integerConstant(self):
        return self.match(TokenType.INTEGER)
        
    def parse_stringLiteral(self):
        return self.match(TokenType.STRING)
    
    def parse_sentence(self):
        pos_start = self.lexer.pos
        if self.parse_subject() and self.parse_verb() and self.parse_object():
            return True
        self.lexer.pos = pos_start
        return False

    
    def parse_subject(self):
        pos_start = self.lexer.pos
        if self.parse_article() and self.parse_noun():
            return True
        self.lexer.pos = pos_start
        return False

    
    def parse_object(self):
        pos_start = self.lexer.pos
        if self.parse_article() and self.parse_noun():
            return True
        self.lexer.pos = pos_start
        return False

    
    def parse_article(self):
        pos_start = self.lexer.pos
        if self.match(TokenType.KEYWORD, "the") or self.match(TokenType.KEYWORD, "a"):
            return True
        self.lexer.pos = pos_start
        return False

    
    def parse_noun(self):
        pos_start = self.lexer.pos
        if self.match(TokenType.KEYWORD, "cat") or self.match(TokenType.KEYWORD, "dog") or self.match(TokenType.KEYWORD, "bird"):
            return True
        self.lexer.pos = pos_start
        return False

    
    def parse_verb(self):
        pos_start = self.lexer.pos
        if self.match(TokenType.KEYWORD, "chases") or self.match(TokenType.KEYWORD, "catches") or self.match(TokenType.KEYWORD, "watches"):
            return True
        self.lexer.pos = pos_start
        return False

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
