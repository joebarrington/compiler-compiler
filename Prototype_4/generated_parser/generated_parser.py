from generated_parser.Lexer import StandardLexer, TokenType, Token

class GeneratedParser:
    def __init__(self, text: str):
        self.keywords = {'else', 'class', 'let', 'false', 'constructor', 'char', 'do', 'var', 'return', 'int', 'if', 'function', 'method', 'boolean', 'this', 'field', 'true', 'null', 'while', 'void', 'static'}
        self.symbols = {'', '<', '+', '.', '*', ']', '~', '=', '|', '{', ',', '[', '(', '-', '/', '}', '&', ')', '>', ';'}
        self.lexer = StandardLexer(text, self.keywords)
        self.current_token = None
        self.next_token()
        self.memoization_cache = {}
        self.error_recovery_points = set()
    def error(self, expected=None):
        token = self.current_token
        line = self.lexer.line
        column = self.lexer.column
        
        error_context = self.get_error_context()
        
        msg = f"Syntax error at line {line}, column {column}\n"
        msg += f"Got: {token.type}({token.value})\n"
        if expected:
            msg += f"Expected: {expected}\n"
        msg += f"Context:\n{error_context}"
        
        if self.try_error_recovery():
            msg += "\nAttempted error recovery and continued parsing."
        
        raise SyntaxError(msg)
    
    def get_error_context(self):
        lines = self.lexer.text.split('\n')
        if self.lexer.line <= len(lines):
            error_line = lines[self.lexer.line - 1]
            pointer = ' ' * (self.lexer.column - 1) + '^'
            return f"{error_line}\n{pointer}"
        return "Context not available"
        
    def try_error_recovery(self):
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
    def parse_classDeclar(self):
        pos_start = self.lexer.pos
        if self.match(TokenType.KEYWORD, "class") and self.parse_identifier() and self.match(TokenType.SYMBOL, "{") and self.repeat_parse(lambda: self.parse_memberDeclar()) and self.match(TokenType.SYMBOL, "}"):
            return True
        self.lexer.pos = pos_start
        return False

    def parse_memberDeclar(self):
        pos_start = self.lexer.pos
        if self.parse_classVarDeclar() or self.parse_subroutineDeclar():
            return True
        self.lexer.pos = pos_start
        return False

    def parse_classVarDeclar(self):
        pos_start = self.lexer.pos
        if (self.match(TokenType.KEYWORD, "static") or self.match(TokenType.KEYWORD, "field")) and self.parse_type() and self.parse_identifier() and self.repeat_parse(lambda: (self.match(TokenType.SYMBOL, ",") and self.parse_identifier())) and self.match(TokenType.SYMBOL, ";"):
            return True
        self.lexer.pos = pos_start
        return False

    def parse_type(self):
        pos_start = self.lexer.pos
        if self.match(TokenType.KEYWORD, "int") or self.match(TokenType.KEYWORD, "char") or self.match(TokenType.KEYWORD, "boolean") or self.parse_identifier():
            return True
        self.lexer.pos = pos_start
        return False

    def parse_subroutineDeclar(self):
        pos_start = self.lexer.pos
        if (self.match(TokenType.KEYWORD, "constructor") or self.match(TokenType.KEYWORD, "function") or self.match(TokenType.KEYWORD, "method")) and (self.parse_type() or self.match(TokenType.KEYWORD, "void")) and self.parse_identifier() and self.match(TokenType.SYMBOL, "(") and self.parse_paramList() and self.match(TokenType.SYMBOL, ")") and self.parse_subroutineBody():
            return True
        self.lexer.pos = pos_start
        return False

    def parse_paramList(self):
        pos_start = self.lexer.pos
        if (self.parse_type() and self.parse_identifier() and self.repeat_parse(lambda: (self.match(TokenType.SYMBOL, ",") and self.parse_type() and self.parse_identifier()))) or True:
            return True
        self.lexer.pos = pos_start
        return False

    def parse_subroutineBody(self):
        pos_start = self.lexer.pos
        if self.match(TokenType.SYMBOL, "{") and self.repeat_parse(lambda: self.parse_statement()) and self.match(TokenType.SYMBOL, "}"):
            return True
        self.lexer.pos = pos_start
        return False

    def parse_statement(self):
        pos_start = self.lexer.pos
        if self.parse_varDeclarStatement() or self.parse_letStatemnt() or self.parse_ifStatement() or self.parse_whileStatement() or self.parse_doStatement() or self.parse_returnStatemnt():
            return True
        self.lexer.pos = pos_start
        return False

    def parse_varDeclarStatement(self):
        pos_start = self.lexer.pos
        if self.match(TokenType.KEYWORD, "var") and self.parse_type() and self.parse_identifier() and self.repeat_parse(lambda: (self.match(TokenType.SYMBOL, ",") and self.parse_identifier())) and self.match(TokenType.SYMBOL, ";"):
            return True
        self.lexer.pos = pos_start
        return False

    def parse_letStatemnt(self):
        pos_start = self.lexer.pos
        if self.match(TokenType.KEYWORD, "let") and self.parse_identifier() and ((self.match(TokenType.SYMBOL, "[") and self.parse_expression() and self.match(TokenType.SYMBOL, "]")) or True) and self.match(TokenType.SYMBOL, "=") and self.parse_expression() and self.match(TokenType.SYMBOL, ";"):
            return True
        self.lexer.pos = pos_start
        return False

    def parse_ifStatement(self):
        pos_start = self.lexer.pos
        if self.match(TokenType.KEYWORD, "if") and self.match(TokenType.SYMBOL, "(") and self.parse_expression() and self.match(TokenType.SYMBOL, ")") and self.match(TokenType.SYMBOL, "{") and self.repeat_parse(lambda: self.parse_statement()) and self.match(TokenType.SYMBOL, "}") and ((self.match(TokenType.KEYWORD, "else") and self.match(TokenType.SYMBOL, "{") and self.repeat_parse(lambda: self.parse_statement()) and self.match(TokenType.SYMBOL, "}")) or True):
            return True
        self.lexer.pos = pos_start
        return False

    def parse_whileStatement(self):
        pos_start = self.lexer.pos
        if self.match(TokenType.KEYWORD, "while") and self.match(TokenType.SYMBOL, "(") and self.parse_expression() and self.match(TokenType.SYMBOL, ")") and self.match(TokenType.SYMBOL, "{") and self.repeat_parse(lambda: self.parse_statement()) and self.match(TokenType.SYMBOL, "}"):
            return True
        self.lexer.pos = pos_start
        return False

    def parse_doStatement(self):
        pos_start = self.lexer.pos
        if self.match(TokenType.KEYWORD, "do") and self.parse_subroutineCall() and self.match(TokenType.SYMBOL, ";"):
            return True
        self.lexer.pos = pos_start
        return False

    def parse_subroutineCall(self):
        pos_start = self.lexer.pos
        if self.parse_identifier() and ((self.match(TokenType.SYMBOL, ".") and self.parse_identifier()) or True) and self.match(TokenType.SYMBOL, "(") and self.parse_expressionList() and self.match(TokenType.SYMBOL, ")"):
            return True
        self.lexer.pos = pos_start
        return False

    def parse_expressionList(self):
        pos_start = self.lexer.pos
        if (self.parse_expression() and self.repeat_parse(lambda: (self.match(TokenType.SYMBOL, ",") and self.parse_expression()))) or True:
            return True
        self.lexer.pos = pos_start
        return False

    def parse_returnStatemnt(self):
        pos_start = self.lexer.pos
        if self.match(TokenType.KEYWORD, "return") and (self.parse_expression() or True) and self.match(TokenType.SYMBOL, ";"):
            return True
        self.lexer.pos = pos_start
        return False

    def parse_expression(self):
        pos_start = self.lexer.pos
        if self.parse_relationalExpression() and self.repeat_parse(lambda: ((self.match(TokenType.SYMBOL, "&") or self.match(TokenType.SYMBOL, "|")) and self.parse_relationalExpression())):
            return True
        self.lexer.pos = pos_start
        return False

    def parse_relationalExpression(self):
        pos_start = self.lexer.pos
        if self.parse_ArithmeticExpression() and self.repeat_parse(lambda: ((self.match(TokenType.SYMBOL, "=") or self.match(TokenType.SYMBOL, ">") or self.match(TokenType.SYMBOL, "<")) and self.parse_ArithmeticExpression())):
            return True
        self.lexer.pos = pos_start
        return False

    def parse_ArithmeticExpression(self):
        pos_start = self.lexer.pos
        if self.parse_term() and self.repeat_parse(lambda: ((self.match(TokenType.SYMBOL, "+") or self.match(TokenType.SYMBOL, "-")) and self.parse_term())):
            return True
        self.lexer.pos = pos_start
        return False

    def parse_term(self):
        pos_start = self.lexer.pos
        if self.parse_factor() and self.repeat_parse(lambda: ((self.match(TokenType.SYMBOL, "*") or self.match(TokenType.SYMBOL, "/")) and self.parse_factor())):
            return True
        self.lexer.pos = pos_start
        return False

    def parse_factor(self):
        pos_start = self.lexer.pos
        if (self.match(TokenType.SYMBOL, "-") or self.match(TokenType.SYMBOL, "~") or True) and self.parse_operand():
            return True
        self.lexer.pos = pos_start
        return False

    def parse_operand(self):
        pos_start = self.lexer.pos
        if self.parse_integerConstant() or self.parse_identifierTerm() or self.parse_parenExpression() or self.parse_stringLiteral() or self.parse_keywordConstant():
            return True
        self.lexer.pos = pos_start
        return False

    def parse_identifierTerm(self):
        pos_start = self.lexer.pos
        if self.parse_identifier() and (self.parse_dotIdentifier() or self.parse_arrayAccess() or self.parse_subroutineCallExpr() or True):
            return True
        self.lexer.pos = pos_start
        return False

    def parse_dotIdentifier(self):
        pos_start = self.lexer.pos
        if self.match(TokenType.SYMBOL, ".") and self.parse_identifier() and (self.parse_subroutineCallExpr() or True):
            return True
        self.lexer.pos = pos_start
        return False

    def parse_arrayAccess(self):
        pos_start = self.lexer.pos
        if self.match(TokenType.SYMBOL, "[") and self.parse_expression() and self.match(TokenType.SYMBOL, "]"):
            return True
        self.lexer.pos = pos_start
        return False

    def parse_subroutineCallExpr(self):
        pos_start = self.lexer.pos
        if self.match(TokenType.SYMBOL, "(") and self.parse_expressionList() and self.match(TokenType.SYMBOL, ")"):
            return True
        self.lexer.pos = pos_start
        return False

    def parse_parenExpression(self):
        pos_start = self.lexer.pos
        if self.match(TokenType.SYMBOL, "(") and self.parse_expression() and self.match(TokenType.SYMBOL, ")"):
            return True
        self.lexer.pos = pos_start
        return False

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
