from Lexer import StandardLexer, TokenType, Token
import functools

class GeneratedParser:
    def __init__(self, text: str):
        self.keywords = {'null', 'TEXT', 'E', 'e', 'false', 'true'}
        self.symbols = {'}', '5', '6', '1', '7', '8', '.', '{', '0', ':', '2', '[', '9', '-', '3', ',', '+', ']', '4'}
        self.lexer = StandardLexer(text, self.keywords)
        self.current_token = None
        self.next_token()
        self._memoization_cache = {}
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
        return wrapper
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
        if not self.parse_json():
            self.error("valid json")
        if self.current_token.type != TokenType.EOF:
            self.error("end of input")
        return True

    def parse_identifier(self):
        return self.match(TokenType.IDENTIFIER)
        
    def parse_integerConstant(self):
        return self.match(TokenType.INTEGER)
        
    def parse_stringLiteral(self):
        return self.match(TokenType.STRING)
    @memoize
    def parse_json(self):
        pos_start = self.lexer.pos
        if self.parse_object() or self.parse_array():
            return True
        self.lexer.pos = pos_start
        return False

    @memoize
    def parse_object(self):
        pos_start = self.lexer.pos
        if self.match(TokenType.SYMBOL, "{") and ((self.parse_pair() and self._repeat_parse(lambda: (self.match(TokenType.SYMBOL, ",") and self.parse_pair()))) or True) and self.match(TokenType.SYMBOL, "}"):
            return True
        self.lexer.pos = pos_start
        return False

    @memoize
    def parse_pair(self):
        pos_start = self.lexer.pos
        print("in pair", self.current_token)
        if self.parse_string() and self.match(TokenType.SYMBOL, ":") and self.parse_value():
            return True
        self.lexer.pos = pos_start
        return False

    @memoize
    def parse_array(self):
        pos_start = self.lexer.pos
        if self.match(TokenType.SYMBOL, "[") and ((self.parse_value() and self._repeat_parse(lambda: (self.match(TokenType.SYMBOL, ",") and self.parse_value()))) or True) and self.match(TokenType.SYMBOL, "]"):
            return True
        self.lexer.pos = pos_start
        return False

    @memoize
    def parse_value(self):
        pos_start = self.lexer.pos
        if self.parse_string() or self.parse_number() or self.parse_object() or self.parse_array() or self.match(TokenType.KEYWORD, "true") or self.match(TokenType.KEYWORD, "false") or self.match(TokenType.KEYWORD, "null"):
            return True
        self.lexer.pos = pos_start
        return False

    @memoize
    def parse_string(self):
        print("in here", self.current_token)
        pos_start = self.lexer.pos
        if self._repeat_parse(lambda: self.match(TokenType.KEYWORD, "TEXT")):
            print("in here")
            return True
        self.lexer.pos = pos_start
        return False

    @memoize
    def parse_number(self):
        pos_start = self.lexer.pos
        if (self.match(TokenType.SYMBOL, "-") or True) and self.parse_digits() and ((self.match(TokenType.SYMBOL, ".") and self.parse_digits()) or True) and (((self.match(TokenType.KEYWORD, "e") or self.match(TokenType.KEYWORD, "E")) and ((self.match(TokenType.SYMBOL, "+") or self.match(TokenType.SYMBOL, "-")) or True) and self.parse_digits()) or True):
            return True
        self.lexer.pos = pos_start
        return False

    @memoize
    def parse_digits(self):
        pos_start = self.lexer.pos
        if self.parse_digit() and self._repeat_parse(lambda: self.parse_digit()):
            return True
        self.lexer.pos = pos_start
        return False

    @memoize
    def parse_digit(self):
        pos_start = self.lexer.pos
        if self.match(TokenType.SYMBOL, "0") or self.match(TokenType.SYMBOL, "1") or self.match(TokenType.SYMBOL, "2") or self.match(TokenType.SYMBOL, "3") or self.match(TokenType.SYMBOL, "4") or self.match(TokenType.SYMBOL, "5") or self.match(TokenType.SYMBOL, "6") or self.match(TokenType.SYMBOL, "7") or self.match(TokenType.SYMBOL, "8") or self.match(TokenType.SYMBOL, "9"):
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
