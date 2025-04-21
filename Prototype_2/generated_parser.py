from Lexer import StandardLexer, TokenType, Token
import functools

class GeneratedParser:
    def __init__(self, text: str):
        self.keywords = {'return', 'int', 'this', 'var', 'boolean', 'char', 'function', 'false', 'void', 'method', 'true', 'do', 'field', 'else', 'null', 'static', 'constructor', 'let', 'class', 'if', 'while'}
        self.symbols = {'', '&', '=', '/', '}', ',', '{', ']', ';', '<', ')', '~', '+', '|', '-', '(', '[', '>', '*', '.'}
        self.lexer = StandardLexer(text, self.keywords)
        self.current_token = None
        self.next_token()
        self._memoization_cache = {}
        self.error_recovery_points = set() 
    
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
        if not self.parse_classDeclar():
            self.error("valid classDeclar")
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
    def parse_classDeclar(self):
        pos_start = self.lexer.pos
        if self.match(TokenType.KEYWORD, "class") and self.parse_identifier() and self.match(TokenType.SYMBOL, "{") and self._repeat_parse(lambda: self.parse_memberDeclar()) and self.match(TokenType.SYMBOL, "}"):
            return True
        self.lexer.pos = pos_start
        return False

    @memoize
    def parse_memberDeclar(self):
        pos_start = self.lexer.pos
        if self.parse_classVarDeclar() or self.parse_subroutineDeclar():
            return True
        self.lexer.pos = pos_start
        return False

    @memoize
    def parse_classVarDeclar(self):
        pos_start = self.lexer.pos
        if (self.match(TokenType.KEYWORD, "static") or self.match(TokenType.KEYWORD, "field")) and self.parse_type() and self.parse_identifier() and self._repeat_parse(lambda: (self.match(TokenType.SYMBOL, ",") and self.parse_identifier())) and self.match(TokenType.SYMBOL, ";"):
            return True
        self.lexer.pos = pos_start
        return False

    @memoize
    def parse_type(self):
        pos_start = self.lexer.pos
        if self.match(TokenType.KEYWORD, "int") or self.match(TokenType.KEYWORD, "char") or self.match(TokenType.KEYWORD, "boolean") or self.parse_identifier():
            return True
        self.lexer.pos = pos_start
        return False

    @memoize
    def parse_subroutineDeclar(self):
        pos_start = self.lexer.pos
        if (self.match(TokenType.KEYWORD, "constructor") or self.match(TokenType.KEYWORD, "function") or self.match(TokenType.KEYWORD, "method")) and (self.parse_type() or self.match(TokenType.KEYWORD, "void")) and self.parse_identifier() and self.match(TokenType.SYMBOL, "(") and self.parse_paramList() and self.match(TokenType.SYMBOL, ")") and self.parse_subroutineBody():
            return True
        self.lexer.pos = pos_start
        return False

    @memoize
    def parse_paramList(self):
        pos_start = self.lexer.pos
        if (self.parse_type() and self.parse_identifier() and self._repeat_parse(lambda: (self.match(TokenType.SYMBOL, ",") and self.parse_type() and self.parse_identifier()))) or True:
            return True
        self.lexer.pos = pos_start
        return False

    @memoize
    def parse_subroutineBody(self):
        pos_start = self.lexer.pos
        if self.match(TokenType.SYMBOL, "{") and self._repeat_parse(lambda: self.parse_statement()) and self.match(TokenType.SYMBOL, "}"):
            return True
        self.lexer.pos = pos_start
        return False

    @memoize
    def parse_statement(self):
        pos_start = self.lexer.pos
        if self.parse_varDeclarStatement() or self.parse_letStatemnt() or self.parse_ifStatement() or self.parse_whileStatement() or self.parse_doStatement() or self.parse_returnStatemnt():
            return True
        self.lexer.pos = pos_start
        return False

    @memoize
    def parse_varDeclarStatement(self):
        pos_start = self.lexer.pos
        if self.match(TokenType.KEYWORD, "var") and self.parse_type() and self.parse_identifier() and self._repeat_parse(lambda: (self.match(TokenType.SYMBOL, ",") and self.parse_identifier())) and self.match(TokenType.SYMBOL, ";"):
            return True
        self.lexer.pos = pos_start
        return False

    @memoize
    def parse_letStatemnt(self):
        pos_start = self.lexer.pos
        if self.match(TokenType.KEYWORD, "let") and self.parse_identifier() and ((self.match(TokenType.SYMBOL, "[") and self.parse_expression() and self.match(TokenType.SYMBOL, "]")) or True) and self.match(TokenType.SYMBOL, "=") and self.parse_expression() and self.match(TokenType.SYMBOL, ";"):
            return True
        self.lexer.pos = pos_start
        return False

    @memoize
    def parse_ifStatement(self):
        pos_start = self.lexer.pos
        if self.match(TokenType.KEYWORD, "if") and self.match(TokenType.SYMBOL, "(") and self.parse_expression() and self.match(TokenType.SYMBOL, ")") and self.match(TokenType.SYMBOL, "{") and self._repeat_parse(lambda: self.parse_statement()) and self.match(TokenType.SYMBOL, "}") and ((self.match(TokenType.KEYWORD, "else") and self.match(TokenType.SYMBOL, "{") and self._repeat_parse(lambda: self.parse_statement()) and self.match(TokenType.SYMBOL, "}")) or True):
            return True
        self.lexer.pos = pos_start
        return False

    @memoize
    def parse_whileStatement(self):
        pos_start = self.lexer.pos
        if self.match(TokenType.KEYWORD, "while") and self.match(TokenType.SYMBOL, "(") and self.parse_expression() and self.match(TokenType.SYMBOL, ")") and self.match(TokenType.SYMBOL, "{") and self._repeat_parse(lambda: self.parse_statement()) and self.match(TokenType.SYMBOL, "}"):
            return True
        self.lexer.pos = pos_start
        return False

    @memoize
    def parse_doStatement(self):
        pos_start = self.lexer.pos
        if self.match(TokenType.KEYWORD, "do") and self.parse_subroutineCall() and self.match(TokenType.SYMBOL, ";"):
            return True
        self.lexer.pos = pos_start
        return False

    @memoize
    def parse_subroutineCall(self):
        pos_start = self.lexer.pos
        if self.parse_identifier() and ((self.match(TokenType.SYMBOL, ".") and self.parse_identifier()) or True) and self.match(TokenType.SYMBOL, "(") and self.parse_expressionList() and self.match(TokenType.SYMBOL, ")"):
            return True
        self.lexer.pos = pos_start
        return False

    @memoize
    def parse_expressionList(self):
        pos_start = self.lexer.pos
        if (self.parse_expression() and self._repeat_parse(lambda: (self.match(TokenType.SYMBOL, ",") and self.parse_expression()))) or True:
            return True
        self.lexer.pos = pos_start
        return False

    @memoize
    def parse_returnStatemnt(self):
        pos_start = self.lexer.pos
        if self.match(TokenType.KEYWORD, "return") and (self.parse_expression() or True) and self.match(TokenType.SYMBOL, ";"):
            return True
        self.lexer.pos = pos_start
        return False

    @memoize
    def parse_expression(self):
        pos_start = self.lexer.pos
        if self.parse_relationalExpression() and self._repeat_parse(lambda: ((self.match(TokenType.SYMBOL, "&") or self.match(TokenType.SYMBOL, "|")) and self.parse_relationalExpression())):
            return True
        self.lexer.pos = pos_start
        return False

    @memoize
    def parse_relationalExpression(self):
        pos_start = self.lexer.pos
        if self.parse_ArithmeticExpression() and self._repeat_parse(lambda: ((self.match(TokenType.SYMBOL, "=") or self.match(TokenType.SYMBOL, ">") or self.match(TokenType.SYMBOL, "<")) and self.parse_ArithmeticExpression())):
            return True
        self.lexer.pos = pos_start
        return False

    @memoize
    def parse_ArithmeticExpression(self):
        pos_start = self.lexer.pos
        if self.parse_term() and self._repeat_parse(lambda: ((self.match(TokenType.SYMBOL, "+") or self.match(TokenType.SYMBOL, "-")) and self.parse_term())):
            return True
        self.lexer.pos = pos_start
        return False

    @memoize
    def parse_term(self):
        pos_start = self.lexer.pos
        if self.parse_factor() and self._repeat_parse(lambda: ((self.match(TokenType.SYMBOL, "*") or self.match(TokenType.SYMBOL, "/")) and self.parse_factor())):
            return True
        self.lexer.pos = pos_start
        return False

    @memoize
    def parse_factor(self):
        pos_start = self.lexer.pos
        if (self.match(TokenType.SYMBOL, "-") or self.match(TokenType.SYMBOL, "~") or True) and self.parse_operand():
            return True
        self.lexer.pos = pos_start
        return False

    @memoize
    def parse_operand(self):
        pos_start = self.lexer.pos
        if self.parse_integerConstant() or self.parse_identifierTerm() or self.parse_parenExpression() or self.parse_stringLiteral() or self.parse_keywordConstant():
            return True
        self.lexer.pos = pos_start
        return False

    @memoize
    def parse_identifierTerm(self):
        pos_start = self.lexer.pos
        if self.parse_identifier() and (self.parse_dotIdentifier() or self.parse_arrayAccess() or self.parse_subroutineCallExpr() or True):
            return True
        self.lexer.pos = pos_start
        return False

    @memoize
    def parse_dotIdentifier(self):
        pos_start = self.lexer.pos
        if self.match(TokenType.SYMBOL, ".") and self.parse_identifier() and (self.parse_subroutineCallExpr() or True):
            return True
        self.lexer.pos = pos_start
        return False

    @memoize
    def parse_arrayAccess(self):
        pos_start = self.lexer.pos
        if self.match(TokenType.SYMBOL, "[") and self.parse_expression() and self.match(TokenType.SYMBOL, "]"):
            return True
        self.lexer.pos = pos_start
        return False

    @memoize
    def parse_subroutineCallExpr(self):
        pos_start = self.lexer.pos
        if self.match(TokenType.SYMBOL, "(") and self.parse_expressionList() and self.match(TokenType.SYMBOL, ")"):
            return True
        self.lexer.pos = pos_start
        return False

    @memoize
    def parse_parenExpression(self):
        pos_start = self.lexer.pos
        if self.match(TokenType.SYMBOL, "(") and self.parse_expression() and self.match(TokenType.SYMBOL, ")"):
            return True
        self.lexer.pos = pos_start
        return False

    @memoize
    def parse_keywordConstant(self):
        pos_start = self.lexer.pos
        if self.match(TokenType.KEYWORD, "true") or self.match(TokenType.KEYWORD, "false") or self.match(TokenType.KEYWORD, "null") or self.match(TokenType.KEYWORD, "this"):
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
