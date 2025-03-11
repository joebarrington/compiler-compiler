from Lexer import StandardLexer, TokenType, Token
import functools

class GeneratedParser:
    def __init__(self, text: str):
        self.keywords = {'static', 'union', 'double', 'enum', 'struct', 'else', 'goto', 'unsigned', 'default', 'while', 'volatile', 'case', 'extern', 'void', 'register', 'float', 'for', 'sizeof', 'return', 'do', 'break', 'typedef', 'signed', 'short', 'char', 'int', 'continue', 'if', 'long', 'switch', 'const', 'auto'}
        self.symbols = {'!=', '[', '-', '--', '+=', '...', '>>=', '^=', '>', '%', '|=', '&=', '*', '<=', '~', '/=', '/', '?', '%=', ':', ';', '<', '>=', '&', '==', '->', '!', '(', '{', '}', ')', '+', '|', '>>', '++', '-=', ']', '*=', '||', '&&', ',', '<<', '^', '.', '=', '<<='}
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
        if not self.parse_translationunit():
            self.error("valid translationunit")
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
    def parse_translationunit(self):
        pos_start = self.lexer.pos
        if self._repeat_parse(lambda: self.parse_externaldeclaration()):
            return True
        self.lexer.pos = pos_start
        return False

    @memoize
    def parse_externaldeclaration(self):
        pos_start = self.lexer.pos
        if self.parse_functiondefinition() or self.parse_declaration():
            return True
        self.lexer.pos = pos_start
        return False

    @memoize
    def parse_functiondefinition(self):
        pos_start = self.lexer.pos
        if self._repeat_parse(lambda: self.parse_declarationspecifier()) and self.parse_declarator() and self._repeat_parse(lambda: self.parse_declaration()) and self.parse_compoundstatement():
            return True
        self.lexer.pos = pos_start
        return False

    @memoize
    def parse_declarationspecifier(self):
        pos_start = self.lexer.pos
        if self.parse_storageclassspecifier() or self.parse_typespecifier() or self.parse_typequalifier():
            return True
        self.lexer.pos = pos_start
        return False

    @memoize
    def parse_storageclassspecifier(self):
        pos_start = self.lexer.pos
        if self.match(TokenType.KEYWORD, "auto") or self.match(TokenType.KEYWORD, "register") or self.match(TokenType.KEYWORD, "static") or self.match(TokenType.KEYWORD, "extern") or self.match(TokenType.KEYWORD, "typedef"):
            return True
        self.lexer.pos = pos_start
        return False

    @memoize
    def parse_typespecifier(self):
        pos_start = self.lexer.pos
        if self.match(TokenType.KEYWORD, "void") or self.match(TokenType.KEYWORD, "char") or self.match(TokenType.KEYWORD, "short") or self.match(TokenType.KEYWORD, "int") or self.match(TokenType.KEYWORD, "long") or self.match(TokenType.KEYWORD, "float") or self.match(TokenType.KEYWORD, "double") or self.match(TokenType.KEYWORD, "signed") or self.match(TokenType.KEYWORD, "unsigned") or self.parse_structorunionspecifier() or self.parse_enumspecifier() or self.parse_typedefname():
            return True
        self.lexer.pos = pos_start
        return False

    @memoize
    def parse_structorunionspecifier(self):
        pos_start = self.lexer.pos
        if (self.parse_structorunion() and self.parse_identifier() and self.match(TokenType.SYMBOL, "{") and self._repeat_parse(lambda: self.parse_structdeclaration()) and self.match(TokenType.SYMBOL, "}")) or (self.parse_structorunion() and self.match(TokenType.SYMBOL, "{") and self._repeat_parse(lambda: self.parse_structdeclaration()) and self.match(TokenType.SYMBOL, "}")) or (self.parse_structorunion() and self.parse_identifier()):
            return True
        self.lexer.pos = pos_start
        return False

    @memoize
    def parse_structorunion(self):
        pos_start = self.lexer.pos
        if self.match(TokenType.KEYWORD, "struct") or self.match(TokenType.KEYWORD, "union"):
            return True
        self.lexer.pos = pos_start
        return False

    @memoize
    def parse_structdeclaration(self):
        pos_start = self.lexer.pos
        if self._repeat_parse(lambda: self.parse_specifierqualifier()) and self.parse_structdeclaratorlist():
            return True
        self.lexer.pos = pos_start
        return False

    @memoize
    def parse_specifierqualifier(self):
        pos_start = self.lexer.pos
        if self.parse_typespecifier() or self.parse_typequalifier():
            return True
        self.lexer.pos = pos_start
        return False

    @memoize
    def parse_structdeclaratorlist(self):
        pos_start = self.lexer.pos
        if self.parse_structdeclarator() or (self.parse_structdeclaratorlist() and self.match(TokenType.SYMBOL, ",") and self.parse_structdeclarator()):
            return True
        self.lexer.pos = pos_start
        return False

    @memoize
    def parse_structdeclarator(self):
        pos_start = self.lexer.pos
        if self.parse_declarator() or (self.parse_declarator() and self.match(TokenType.SYMBOL, ":") and self.parse_constantexpression()) or (self.match(TokenType.SYMBOL, ":") and self.parse_constantexpression()):
            return True
        self.lexer.pos = pos_start
        return False

    @memoize
    def parse_declarator(self):
        pos_start = self.lexer.pos
        if (self.parse_pointer() or True) and self.parse_directdeclarator():
            return True
        self.lexer.pos = pos_start
        return False

    @memoize
    def parse_pointer(self):
        pos_start = self.lexer.pos
        if self.match(TokenType.SYMBOL, "*") and self._repeat_parse(lambda: self.parse_typequalifier()) and (self.parse_pointer() or True):
            return True
        self.lexer.pos = pos_start
        return False

    @memoize
    def parse_typequalifier(self):
        pos_start = self.lexer.pos
        if self.match(TokenType.KEYWORD, "const") or self.match(TokenType.KEYWORD, "volatile"):
            return True
        self.lexer.pos = pos_start
        return False

    @memoize
    def parse_directdeclarator(self):
        pos_start = self.lexer.pos
        if self.parse_identifier() or (self.match(TokenType.SYMBOL, "(") and self.parse_declarator() and self.match(TokenType.SYMBOL, ")")) or (self.parse_directdeclarator() and self.match(TokenType.SYMBOL, "[") and (self.parse_constantexpression() or True) and self.match(TokenType.SYMBOL, "]")) or (self.parse_directdeclarator() and self.match(TokenType.SYMBOL, "(") and self.parse_parametertypelist() and self.match(TokenType.SYMBOL, ")")) or (self.parse_directdeclarator() and self.match(TokenType.SYMBOL, "(") and self._repeat_parse(lambda: self.parse_identifier()) and self.match(TokenType.SYMBOL, ")")):
            return True
        self.lexer.pos = pos_start
        return False

    @memoize
    def parse_constantexpression(self):
        pos_start = self.lexer.pos
        if self.parse_conditionalexpression():
            return True
        self.lexer.pos = pos_start
        return False

    @memoize
    def parse_conditionalexpression(self):
        pos_start = self.lexer.pos
        if self.parse_logicalorexpression() or (self.parse_logicalorexpression() and self.match(TokenType.SYMBOL, "?") and self.parse_expression() and self.match(TokenType.SYMBOL, ":") and self.parse_conditionalexpression()):
            return True
        self.lexer.pos = pos_start
        return False

    @memoize
    def parse_logicalorexpression(self):
        pos_start = self.lexer.pos
        if self.parse_logicalandexpression() or (self.parse_logicalorexpression() and self.match(TokenType.SYMBOL, "||") and self.parse_logicalandexpression()):
            return True
        self.lexer.pos = pos_start
        return False

    @memoize
    def parse_logicalandexpression(self):
        pos_start = self.lexer.pos
        if self.parse_inclusiveorexpression() or (self.parse_logicalandexpression() and self.match(TokenType.SYMBOL, "&&") and self.parse_inclusiveorexpression()):
            return True
        self.lexer.pos = pos_start
        return False

    @memoize
    def parse_inclusiveorexpression(self):
        pos_start = self.lexer.pos
        if self.parse_exclusiveorexpression() or (self.parse_inclusiveorexpression() and self.match(TokenType.SYMBOL, "|") and self.parse_exclusiveorexpression()):
            return True
        self.lexer.pos = pos_start
        return False

    @memoize
    def parse_exclusiveorexpression(self):
        pos_start = self.lexer.pos
        if self.parse_andexpression() or (self.parse_exclusiveorexpression() and self.match(TokenType.SYMBOL, "^") and self.parse_andexpression()):
            return True
        self.lexer.pos = pos_start
        return False

    @memoize
    def parse_andexpression(self):
        pos_start = self.lexer.pos
        if self.parse_equalityexpression() or (self.parse_andexpression() and self.match(TokenType.SYMBOL, "&") and self.parse_equalityexpression()):
            return True
        self.lexer.pos = pos_start
        return False

    @memoize
    def parse_equalityexpression(self):
        pos_start = self.lexer.pos
        if self.parse_relationalexpression() or (self.parse_equalityexpression() and self.match(TokenType.SYMBOL, "==") and self.parse_relationalexpression()) or (self.parse_equalityexpression() and self.match(TokenType.SYMBOL, "!=") and self.parse_relationalexpression()):
            return True
        self.lexer.pos = pos_start
        return False

    @memoize
    def parse_relationalexpression(self):
        pos_start = self.lexer.pos
        if self.parse_shiftexpression() or (self.parse_relationalexpression() and self.match(TokenType.SYMBOL, "<") and self.parse_shiftexpression()) or (self.parse_relationalexpression() and self.match(TokenType.SYMBOL, ">") and self.parse_shiftexpression()) or (self.parse_relationalexpression() and self.match(TokenType.SYMBOL, "<=") and self.parse_shiftexpression()) or (self.parse_relationalexpression() and self.match(TokenType.SYMBOL, ">=") and self.parse_shiftexpression()):
            return True
        self.lexer.pos = pos_start
        return False

    @memoize
    def parse_shiftexpression(self):
        pos_start = self.lexer.pos
        if self.parse_additiveexpression() or (self.parse_shiftexpression() and self.match(TokenType.SYMBOL, "<<") and self.parse_additiveexpression()) or (self.parse_shiftexpression() and self.match(TokenType.SYMBOL, ">>") and self.parse_additiveexpression()):
            return True
        self.lexer.pos = pos_start
        return False

    @memoize
    def parse_additiveexpression(self):
        pos_start = self.lexer.pos
        if self.parse_multiplicativeexpression() or (self.parse_additiveexpression() and self.match(TokenType.SYMBOL, "+") and self.parse_multiplicativeexpression()) or (self.parse_additiveexpression() and self.match(TokenType.SYMBOL, "-") and self.parse_multiplicativeexpression()):
            return True
        self.lexer.pos = pos_start
        return False

    @memoize
    def parse_multiplicativeexpression(self):
        pos_start = self.lexer.pos
        if self.parse_castexpression() or (self.parse_multiplicativeexpression() and self.match(TokenType.SYMBOL, "*") and self.parse_castexpression()) or (self.parse_multiplicativeexpression() and self.match(TokenType.SYMBOL, "/") and self.parse_castexpression()) or (self.parse_multiplicativeexpression() and self.match(TokenType.SYMBOL, "%") and self.parse_castexpression()):
            return True
        self.lexer.pos = pos_start
        return False

    @memoize
    def parse_castexpression(self):
        pos_start = self.lexer.pos
        if self.parse_unaryexpression() or (self.match(TokenType.SYMBOL, "(") and self.parse_typename() and self.match(TokenType.SYMBOL, ")") and self.parse_castexpression()):
            return True
        self.lexer.pos = pos_start
        return False

    @memoize
    def parse_unaryexpression(self):
        pos_start = self.lexer.pos
        if self.parse_postfixexpression() or (self.match(TokenType.SYMBOL, "++") and self.parse_unaryexpression()) or (self.match(TokenType.SYMBOL, "--") and self.parse_unaryexpression()) or (self.parse_unaryoperator() and self.parse_castexpression()) or (self.match(TokenType.KEYWORD, "sizeof") and self.parse_unaryexpression()) or (self.match(TokenType.KEYWORD, "sizeof") and self.parse_typename()):
            return True
        self.lexer.pos = pos_start
        return False

    @memoize
    def parse_postfixexpression(self):
        pos_start = self.lexer.pos
        if self.parse_primaryexpression() or (self.parse_postfixexpression() and self.match(TokenType.SYMBOL, "[") and self.parse_expression() and self.match(TokenType.SYMBOL, "]")) or (self.parse_postfixexpression() and self.match(TokenType.SYMBOL, "(") and self._repeat_parse(lambda: self.parse_assignmentexpression()) and self.match(TokenType.SYMBOL, ")")) or (self.parse_postfixexpression() and self.match(TokenType.SYMBOL, ".") and self.parse_identifier()) or (self.parse_postfixexpression() and self.match(TokenType.SYMBOL, "->") and self.parse_identifier()) or (self.parse_postfixexpression() and self.match(TokenType.SYMBOL, "++")) or (self.parse_postfixexpression() and self.match(TokenType.SYMBOL, "--")):
            return True
        self.lexer.pos = pos_start
        return False

    @memoize
    def parse_primaryexpression(self):
        pos_start = self.lexer.pos
        if self.parse_identifier() or self.parse_constant() or self.parse_string() or (self.match(TokenType.SYMBOL, "(") and self.parse_expression() and self.match(TokenType.SYMBOL, ")")):
            return True
        self.lexer.pos = pos_start
        return False

    @memoize
    def parse_constant(self):
        pos_start = self.lexer.pos
        if self.parse_integerconstant() or self.parse_characterconstant() or self.parse_floatingconstant() or self.parse_enumerationconstant():
            return True
        self.lexer.pos = pos_start
        return False

    @memoize
    def parse_expression(self):
        pos_start = self.lexer.pos
        if self.parse_assignmentexpression() or (self.parse_expression() and self.match(TokenType.SYMBOL, ",") and self.parse_assignmentexpression()):
            return True
        self.lexer.pos = pos_start
        return False

    @memoize
    def parse_assignmentexpression(self):
        pos_start = self.lexer.pos
        if self.parse_conditionalexpression() or (self.parse_unaryexpression() and self.parse_assignmentoperator() and self.parse_assignmentexpression()):
            return True
        self.lexer.pos = pos_start
        return False

    @memoize
    def parse_assignmentoperator(self):
        pos_start = self.lexer.pos
        if self.match(TokenType.SYMBOL, "=") or self.match(TokenType.SYMBOL, "*=") or self.match(TokenType.SYMBOL, "/=") or self.match(TokenType.SYMBOL, "%=") or self.match(TokenType.SYMBOL, "+=") or self.match(TokenType.SYMBOL, "-=") or self.match(TokenType.SYMBOL, "<<=") or self.match(TokenType.SYMBOL, ">>=") or self.match(TokenType.SYMBOL, "&=") or self.match(TokenType.SYMBOL, "^=") or self.match(TokenType.SYMBOL, "|="):
            return True
        self.lexer.pos = pos_start
        return False

    @memoize
    def parse_unaryoperator(self):
        pos_start = self.lexer.pos
        if self.match(TokenType.SYMBOL, "&") or self.match(TokenType.SYMBOL, "*") or self.match(TokenType.SYMBOL, "+") or self.match(TokenType.SYMBOL, "-") or self.match(TokenType.SYMBOL, "~") or self.match(TokenType.SYMBOL, "!"):
            return True
        self.lexer.pos = pos_start
        return False

    @memoize
    def parse_typename(self):
        pos_start = self.lexer.pos
        if self._repeat_parse(lambda: self.parse_specifierqualifier()) and (self.parse_abstractdeclarator() or True):
            return True
        self.lexer.pos = pos_start
        return False

    @memoize
    def parse_parametertypelist(self):
        pos_start = self.lexer.pos
        if self.parse_parameterlist() or (self.parse_parameterlist() and self.match(TokenType.SYMBOL, ",") and self.match(TokenType.SYMBOL, "...")):
            return True
        self.lexer.pos = pos_start
        return False

    @memoize
    def parse_parameterlist(self):
        pos_start = self.lexer.pos
        if self.parse_parameterdeclaration() or (self.parse_parameterlist() and self.match(TokenType.SYMBOL, ",") and self.parse_parameterdeclaration()):
            return True
        self.lexer.pos = pos_start
        return False

    @memoize
    def parse_parameterdeclaration(self):
        pos_start = self.lexer.pos
        if (self._repeat_parse(lambda: self.parse_declarationspecifier()) and self.parse_declarator()) or (self._repeat_parse(lambda: self.parse_declarationspecifier()) and self.parse_abstractdeclarator()) or self._repeat_parse(lambda: self.parse_declarationspecifier()):
            return True
        self.lexer.pos = pos_start
        return False

    @memoize
    def parse_abstractdeclarator(self):
        pos_start = self.lexer.pos
        if self.parse_pointer() or (self.parse_pointer() and self.parse_directabstractdeclarator()) or self.parse_directabstractdeclarator():
            return True
        self.lexer.pos = pos_start
        return False

    @memoize
    def parse_directabstractdeclarator(self):
        pos_start = self.lexer.pos
        if (self.match(TokenType.SYMBOL, "(") and self.parse_abstractdeclarator() and self.match(TokenType.SYMBOL, ")")) or ((self.parse_directabstractdeclarator() or True) and self.match(TokenType.SYMBOL, "[") and (self.parse_constantexpression() or True) and self.match(TokenType.SYMBOL, "]")) or ((self.parse_directabstractdeclarator() or True) and self.match(TokenType.SYMBOL, "(") and (self.parse_parametertypelist() or True) and self.match(TokenType.SYMBOL, ")")):
            return True
        self.lexer.pos = pos_start
        return False

    @memoize
    def parse_enumspecifier(self):
        pos_start = self.lexer.pos
        if (self.match(TokenType.KEYWORD, "enum") and self.parse_identifier() and self.match(TokenType.SYMBOL, "{") and self.parse_enumeratorlist() and self.match(TokenType.SYMBOL, "}")) or (self.match(TokenType.KEYWORD, "enum") and self.match(TokenType.SYMBOL, "{") and self.parse_enumeratorlist() and self.match(TokenType.SYMBOL, "}")) or (self.match(TokenType.KEYWORD, "enum") and self.parse_identifier()):
            return True
        self.lexer.pos = pos_start
        return False

    @memoize
    def parse_enumeratorlist(self):
        pos_start = self.lexer.pos
        if self.parse_enumerator() or (self.parse_enumeratorlist() and self.match(TokenType.SYMBOL, ",") and self.parse_enumerator()):
            return True
        self.lexer.pos = pos_start
        return False

    @memoize
    def parse_enumerator(self):
        pos_start = self.lexer.pos
        if self.parse_identifier() or (self.parse_identifier() and self.match(TokenType.SYMBOL, "=") and self.parse_constantexpression()):
            return True
        self.lexer.pos = pos_start
        return False

    @memoize
    def parse_typedefname(self):
        pos_start = self.lexer.pos
        if self.parse_identifier():
            return True
        self.lexer.pos = pos_start
        return False

    @memoize
    def parse_declaration(self):
        pos_start = self.lexer.pos
        if self._repeat_parse(lambda: self.parse_declarationspecifier()) and self._repeat_parse(lambda: self.parse_initdeclarator()) and self.match(TokenType.SYMBOL, ";"):
            return True
        self.lexer.pos = pos_start
        return False

    @memoize
    def parse_initdeclarator(self):
        pos_start = self.lexer.pos
        if self.parse_declarator() or (self.parse_declarator() and self.match(TokenType.SYMBOL, "=") and self.parse_initializer()):
            return True
        self.lexer.pos = pos_start
        return False

    @memoize
    def parse_initializer(self):
        pos_start = self.lexer.pos
        if self.parse_assignmentexpression() or (self.match(TokenType.SYMBOL, "{") and self.parse_initializerlist() and self.match(TokenType.SYMBOL, "}")) or (self.match(TokenType.SYMBOL, "{") and self.parse_initializerlist() and self.match(TokenType.SYMBOL, ",") and self.match(TokenType.SYMBOL, "}")):
            return True
        self.lexer.pos = pos_start
        return False

    @memoize
    def parse_initializerlist(self):
        pos_start = self.lexer.pos
        if self.parse_initializer() or (self.parse_initializerlist() and self.match(TokenType.SYMBOL, ",") and self.parse_initializer()):
            return True
        self.lexer.pos = pos_start
        return False

    @memoize
    def parse_compoundstatement(self):
        pos_start = self.lexer.pos
        if self.match(TokenType.SYMBOL, "{") and self._repeat_parse(lambda: self.parse_declaration()) and self._repeat_parse(lambda: self.parse_statement()) and self.match(TokenType.SYMBOL, "}"):
            return True
        self.lexer.pos = pos_start
        return False

    @memoize
    def parse_statement(self):
        pos_start = self.lexer.pos
        if self.parse_labeledstatement() or self.parse_expressionstatement() or self.parse_compoundstatement() or self.parse_selectionstatement() or self.parse_iterationstatement() or self.parse_jumpstatement():
            return True
        self.lexer.pos = pos_start
        return False

    @memoize
    def parse_labeledstatement(self):
        pos_start = self.lexer.pos
        if (self.parse_identifier() and self.match(TokenType.SYMBOL, ":") and self.parse_statement()) or (self.match(TokenType.KEYWORD, "case") and self.parse_constantexpression() and self.match(TokenType.SYMBOL, ":") and self.parse_statement()) or (self.match(TokenType.KEYWORD, "default") and self.match(TokenType.SYMBOL, ":") and self.parse_statement()):
            return True
        self.lexer.pos = pos_start
        return False

    @memoize
    def parse_expressionstatement(self):
        pos_start = self.lexer.pos
        if (self.parse_expression() or True) and self.match(TokenType.SYMBOL, ";"):
            return True
        self.lexer.pos = pos_start
        return False

    @memoize
    def parse_selectionstatement(self):
        pos_start = self.lexer.pos
        if (self.match(TokenType.KEYWORD, "if") and self.match(TokenType.SYMBOL, "(") and self.parse_expression() and self.match(TokenType.SYMBOL, ")") and self.parse_statement()) or (self.match(TokenType.KEYWORD, "if") and self.match(TokenType.SYMBOL, "(") and self.parse_expression() and self.match(TokenType.SYMBOL, ")") and self.parse_statement() and self.match(TokenType.KEYWORD, "else") and self.parse_statement()) or (self.match(TokenType.KEYWORD, "switch") and self.match(TokenType.SYMBOL, "(") and self.parse_expression() and self.match(TokenType.SYMBOL, ")") and self.parse_statement()):
            return True
        self.lexer.pos = pos_start
        return False

    @memoize
    def parse_iterationstatement(self):
        pos_start = self.lexer.pos
        if (self.match(TokenType.KEYWORD, "while") and self.match(TokenType.SYMBOL, "(") and self.parse_expression() and self.match(TokenType.SYMBOL, ")") and self.parse_statement()) or (self.match(TokenType.KEYWORD, "do") and self.parse_statement() and self.match(TokenType.KEYWORD, "while") and self.match(TokenType.SYMBOL, "(") and self.parse_expression() and self.match(TokenType.SYMBOL, ")") and self.match(TokenType.SYMBOL, ";")) or (self.match(TokenType.KEYWORD, "for") and self.match(TokenType.SYMBOL, "(") and (self.parse_expression() or True) and self.match(TokenType.SYMBOL, ";") and (self.parse_expression() or True) and self.match(TokenType.SYMBOL, ";") and (self.parse_expression() or True) and self.match(TokenType.SYMBOL, ")") and self.parse_statement()):
            return True
        self.lexer.pos = pos_start
        return False

    @memoize
    def parse_jumpstatement(self):
        pos_start = self.lexer.pos
        if (self.match(TokenType.KEYWORD, "goto") and self.parse_identifier() and self.match(TokenType.SYMBOL, ";")) or (self.match(TokenType.KEYWORD, "continue") and self.match(TokenType.SYMBOL, ";")) or (self.match(TokenType.KEYWORD, "break") and self.match(TokenType.SYMBOL, ";")) or (self.match(TokenType.KEYWORD, "return") and (self.parse_expression() or True) and self.match(TokenType.SYMBOL, ";")):
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
