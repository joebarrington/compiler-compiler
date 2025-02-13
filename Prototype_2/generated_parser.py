from Lexer import StandardLexer, TokenType, Token

class GeneratedParser:
    def __init__(self, text: str):
        self.keywords = {'true', 'int', 'constructor', 'if', 'static', 'void', 'return', 'do', 'this', 'field', 'function', 'boolean', 'class', 'method', 'else', 'char', 'null', 'while', 'var', 'let', 'false'}
        self.symbols = {'', '=', ')', '*', '<', '.', '~', '-', '&', '+', '{', '>', ']', '(', '/', ',', '[', '|', '}', ';'}
        self.lexer = StandardLexer(text, self.keywords)
        self.current_token = None
        self.next_token()
        
    def error(self, expected=None):
        msg = f"Syntax error at line {self.lexer.line}, column {self.lexer.column}"
        if expected:
            msg += f". Expected {expected}"
        if self.current_token:
            msg += f". Got {self.current_token}"
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
        if not self.parse_classDeclar():
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

    def parse_classDeclar(self):
        pos_start = self.lexer.pos
        if self.match(TokenType.KEYWORD, "class") and self.parse_identifier() and self.match(TokenType.SYMBOL, "{") and self._repeat_parse(lambda: self.parse_memberDeclar()) and self.match(TokenType.SYMBOL, "}"):
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
        if (self.match(TokenType.KEYWORD, "static") or self.match(TokenType.KEYWORD, "field")) and self.parse_type() and self.parse_identifier() and self._repeat_parse(lambda: (self.match(TokenType.SYMBOL, ",") and self.parse_identifier())) and self.match(TokenType.SYMBOL, ";"):
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
        if (self.parse_type() and self.parse_identifier() and self._repeat_parse(lambda: (self.match(TokenType.SYMBOL, ",") and self.parse_type() and self.parse_identifier()))) or True:
            return True
        self.lexer.pos = pos_start
        return False

    def parse_subroutineBody(self):
        pos_start = self.lexer.pos
        if self.match(TokenType.SYMBOL, "{") and self._repeat_parse(lambda: self.parse_statement()) and self.match(TokenType.SYMBOL, "}"):
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
        if self.match(TokenType.KEYWORD, "var") and self.parse_type() and self.parse_identifier() and self._repeat_parse(lambda: (self.match(TokenType.SYMBOL, ",") and self.parse_identifier())) and self.match(TokenType.SYMBOL, ";"):
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
        if self.match(TokenType.KEYWORD, "if") and self.match(TokenType.SYMBOL, "(") and self.parse_expression() and self.match(TokenType.SYMBOL, ")") and self.match(TokenType.SYMBOL, "{") and self._repeat_parse(lambda: self.parse_statement()) and self.match(TokenType.SYMBOL, "}") and ((self.match(TokenType.KEYWORD, "else") and self.match(TokenType.SYMBOL, "{") and self._repeat_parse(lambda: self.parse_statement()) and self.match(TokenType.SYMBOL, "}")) or True):
            return True
        self.lexer.pos = pos_start
        return False

    def parse_whileStatement(self):
        pos_start = self.lexer.pos
        if self.match(TokenType.KEYWORD, "while") and self.match(TokenType.SYMBOL, "(") and self.parse_expression() and self.match(TokenType.SYMBOL, ")") and self.match(TokenType.SYMBOL, "{") and self._repeat_parse(lambda: self.parse_statement()) and self.match(TokenType.SYMBOL, "}"):
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
        if (self.parse_expression() and self._repeat_parse(lambda: (self.match(TokenType.SYMBOL, ",") and self.parse_expression()))) or True:
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
        if self.parse_relationalExpression() and self._repeat_parse(lambda: ((self.match(TokenType.SYMBOL, "&") or self.match(TokenType.SYMBOL, "|")) and self.parse_relationalExpression())):
            return True
        self.lexer.pos = pos_start
        return False

    def parse_relationalExpression(self):
        pos_start = self.lexer.pos
        if self.parse_ArithmeticExpression() and self._repeat_parse(lambda: ((self.match(TokenType.SYMBOL, "=") or self.match(TokenType.SYMBOL, ">") or self.match(TokenType.SYMBOL, "<")) and self.parse_ArithmeticExpression())):
            return True
        self.lexer.pos = pos_start
        return False

    def parse_ArithmeticExpression(self):
        pos_start = self.lexer.pos
        if self.parse_term() and self._repeat_parse(lambda: ((self.match(TokenType.SYMBOL, "+") or self.match(TokenType.SYMBOL, "-")) and self.parse_term())):
            return True
        self.lexer.pos = pos_start
        return False

    def parse_term(self):
        pos_start = self.lexer.pos
        if self.parse_factor() and self._repeat_parse(lambda: ((self.match(TokenType.SYMBOL, "*") or self.match(TokenType.SYMBOL, "/")) and self.parse_factor())):
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
        if self.parse_integerConstant() or (self.parse_identifier() and ((self.match(TokenType.SYMBOL, ".") and self.parse_identifier()) or True) and ((self.match(TokenType.SYMBOL, "[") and self.parse_expression() and self.match(TokenType.SYMBOL, "]")) or True)) or (self.parse_identifier() and ((self.match(TokenType.SYMBOL, ".") and self.parse_identifier()) or True) and self.match(TokenType.SYMBOL, "(") and self.parse_expressionList() and self.match(TokenType.SYMBOL, ")")) or (self.match(TokenType.SYMBOL, "(") and self.parse_expression() and self.match(TokenType.SYMBOL, ")")) or self.parse_stringLiteral() or self.match(TokenType.KEYWORD, "true") or self.match(TokenType.KEYWORD, "false") or self.match(TokenType.KEYWORD, "null") or self.match(TokenType.KEYWORD, "this"):
            return True
        self.lexer.pos = pos_start
        return False
    

def test_parser(file_path=None):
    if file_path:
        try:
            with open(file_path, 'r') as file:
                jack_code = file.read()
            print(f"\nTesting JACK file: {file_path}")
            parser = GeneratedParser(jack_code)
            result = parser.parse()
            print("✓ Successfully parsed JACK file")
            return True
        except FileNotFoundError:
            print(f"✗ File not found: {file_path}")
            return False
        except SyntaxError as e:
            print(f"✗ Syntax error in JACK file: {e}")
            return False
        except Exception as e:
            print(f"✗ Error parsing JACK file: {e}")
            return False

if __name__ == "__main__":
    test_parser("square.jack")

# def test_parser():
#     test_cases = [
#         {
#             "name": "Basic class with field",
#             "code": """
# class Simple {
#     field int x;
# }""",
#             "should_pass": True
#         },
#         {
#             "name": "Class with method",
#             "code": """
# class WithMethod {
#     method void doSomething() {
#         return;
#     }
# }""",
#             "should_pass": True
#         },
#         {
#             "name": "Class with constructor",
#             "code": """
# class WithConstructor {
#     constructor WithConstructor new() {
#         return this;
#     }
# }""",
#             "should_pass": True
#         },
#         {
#             "name": "Complex class",
#             "code": """
# class Complex {
#     field int x, y;
#     static boolean flag;
    
#     constructor Complex new() {
#         let x = 0;
#         let y = 0;
#         let flag = true;
#         return this;
#     }
    
#     method void setX(int val) {
#         let x = val;
#         return;
#     }
    
#     method int getX() {
#         return x;
#     }
    
#     method void compute() {
#         var int temp;
#         let temp = x * y;
#         if (temp < 100) {
#             let x = x + 1;
#         } else {
#             let y = y + 1;
#         }
#         return;
#     }
# }""",
#             "should_pass": True
#         },
#         {
#             "name": "Missing closing brace",
#             "code": """
# class Error {
#     field int x;
    
#     method void test() {
#         return;
    
# """,
#             "should_pass": False
#         },
#         {
#             "name": "Array manipulation",
#             "code": """
# class Array {
#     field int numbers;
    
#     method void set(int index, int value) {
#         let numbers[index] = value;
#         return;
#     }
    
#     method int get(int index) {
#         return numbers[index];
#     }
# }""",
#             "should_pass": True
#         },
#         {
#             "name": "While loop and expressions",
#             "code": """
# class Loops {
#     method void count() {
#         var int i;
#         let i = 0;
#         while (i < 10) {
#             let i = i + 1;
#         }
#         return;
#     }
# }""",
#             "should_pass": True
#         },
#         {
#             "name": "Do statement and subroutine calls",
#             "code": """
# class Calls {
#     method void test() {
#         do Output.printInt(42);
#         do move.left();
#         return;
#     }
# }""",
#             "should_pass": True
#         }
#     ]
    
#     total_tests = len(test_cases)
#     passed_tests = 0
    
#     for test in test_cases:
#         print(f"\nRunning test: {test['name']}")
#         try:
#             parser = GeneratedParser(test["code"])
#             result = parser.parse()
#             if test["should_pass"]:
#                 print("✓ Test passed as expected")
#                 passed_tests += 1
#             else:
#                 print("✗ Test unexpectedly passed")
#         except SyntaxError as e:
#             if not test["should_pass"]:
#                 print("✓ Test failed as expected")
#                 passed_tests += 1
#             else:
#                 print(f"✗ Test unexpectedly failed: {e}")
    
#     print(f"\nTest Results: {passed_tests}/{total_tests} tests passed")
#     return passed_tests == total_tests

# if __name__ == "__main__":
#     test_parser()
