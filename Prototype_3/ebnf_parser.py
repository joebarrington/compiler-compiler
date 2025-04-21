from grammar_types import *

class EBNFLexer(BaseLexer):
    def __init__(self, text: str):
        super().__init__(text)

    def identifier(self) -> Token:
        result = ''
        start_col = self.col
        
        while self.current_char and (self.current_char.isalnum() or 
                                   self.current_char == '_' or 
                                   self.current_char == '-'):
            result += self.current_char
            self.advance()
        
        return Token(TokenType.IDENTIFIER, result, self.line, start_col)

    def terminal(self) -> Token:
        result = ''
        start_col = self.col
        quote_char = self.current_char
        self.advance()
        
        while self.current_char and self.current_char != quote_char:
            if self.current_char == '\\':
                self.advance()
                if self.current_char:
                    result += self.current_char
                    self.advance()
                continue
            result += self.current_char
            self.advance()
        
        if self.current_char == quote_char:
            self.advance()
            return Token(TokenType.TERMINAL, result, self.line, start_col)
        else:
            raise Exception(f'Unterminated string at line {self.line}, column {start_col}')

    def get_next_token(self) -> Token:
        while self.current_char:
            if self.current_char.isspace():
                self.skip_whitespace()
                continue

            if self.current_char == '#':
                self.skip_comment()
                continue

            if self.current_char.isalpha() or self.current_char == '_':
                return self.identifier()

            if self.current_char in '"\'':
                return self.terminal()

            char_to_token = {
                '=': TokenType.EQUALS,
                ';': TokenType.SEMICOLON,
                ',': TokenType.COMMA,
                '|': TokenType.PIPE,
                '(': TokenType.LPAREN,
                ')': TokenType.RPAREN,
                '{': TokenType.LBRACE,
                '}': TokenType.RBRACE,
                '[': TokenType.LBRACKET,
                ']': TokenType.RBRACKET,
                '*': TokenType.STAR,
                '+': TokenType.PLUS,
                '?': TokenType.QUESTION,
                '-': None
            }

            if self.current_char in char_to_token:
                if char_to_token[self.current_char] is None:
                    if self.current_char == '-' and (
                        (self.pos > 0 and self.text[self.pos-1].isalnum()) or
                        (self.peek() and self.peek().isalnum())
                    ):
                        return self.identifier()
                    self.error()
                
                token = Token(
                    char_to_token[self.current_char],
                    self.current_char,
                    self.line,
                    self.col
                )
                self.advance()
                return token

            self.error()

        return Token(TokenType.EOF, '', self.line, self.col)

class EBNFParser(BaseParser):
    def __init__(self, text: str):
        super().__init__(text)
        self.lexer = EBNFLexer(text)
        self.current_token = self.lexer.get_next_token()

    def error(self, expected: str):
        lines = self.lexer.text.split('\n')
        error_line = lines[self.current_token.line - 1] if self.current_token.line - 1 < len(lines) else ''
        pointer = ' ' * (self.current_token.col - 1) + '^'
        
        error_msg = (
            f'\nSyntax error at line {self.current_token.line}, column {self.current_token.col}\n'
            f'Got token: {self.current_token.type.name}("{self.current_token.value}")\n'
            f'Expected: {expected}\n'
            f'\nContext:\n{error_line}\n{pointer}\n'
        )
        
        raise Exception(error_msg)

    def eat(self, token_type: TokenType):
        if self.current_token.type == token_type:
            self.current_token = self.lexer.get_next_token()
        else:
            self.error(str(token_type))

    def parse_grammar(self) -> List[Rule]:
        """Parse a complete EBNF grammar"""
        while self.current_token.type != TokenType.EOF:
            rule = self.parse_rule()
            if rule:
                self.rules.append(rule)
        return self.rules

    def parse_rule(self) -> Union[Rule, None]:
        """Parse an EBNF rule: name = expression ;"""
        if self.current_token.type != TokenType.IDENTIFIER:
            if self.current_token.type == TokenType.EOF:
                return None
            self.error('identifier')
            
        name = self.current_token.value
        self.eat(TokenType.IDENTIFIER)
        self.eat(TokenType.EQUALS)
        
        definition = self.parse_expression()
        
        if self.current_token.type == TokenType.SEMICOLON:
            self.eat(TokenType.SEMICOLON)
            
        return Rule(name, definition)

    def parse_expression(self) -> ASTNode:
        """Parse an EBNF expression (alternatives)"""
        terms = [self.parse_sequence()]
        
        while self.current_token.type == TokenType.PIPE:
            self.eat(TokenType.PIPE)
            terms.append(self.parse_sequence())
            
        return terms[0] if len(terms) == 1 else Alternative(terms)

    def parse_sequence(self) -> ASTNode:
        """Parse a sequence of terms"""
        terms = [self.parse_term()]
        
        while self.current_token.type == TokenType.COMMA:
            self.eat(TokenType.COMMA)
            terms.append(self.parse_term())
            
        return terms[0] if len(terms) == 1 else Sequence(terms)

    def parse_term(self) -> ASTNode:
        """Parse a single term with possible repetition or optional markers"""
        if self.current_token.type == TokenType.TERMINAL:
            term = Terminal(self.current_token.value)
            self.eat(TokenType.TERMINAL)
        elif self.current_token.type == TokenType.IDENTIFIER:
            term = NonTerminal(self.current_token.value)
            self.eat(TokenType.IDENTIFIER)
        elif self.current_token.type == TokenType.LPAREN:
            self.eat(TokenType.LPAREN)
            term = self.parse_expression()
            self.eat(TokenType.RPAREN)
        elif self.current_token.type == TokenType.LBRACE:
            self.eat(TokenType.LBRACE)
            term = self.parse_expression()
            self.eat(TokenType.RBRACE)
            return Repetition(term)
        elif self.current_token.type == TokenType.LBRACKET:
            self.eat(TokenType.LBRACKET)
            term = self.parse_expression()
            self.eat(TokenType.RBRACKET)
            return Optional(term)
        else:
            self.error('term')

        if self.current_token.type in {TokenType.STAR, TokenType.PLUS, TokenType.QUESTION}:
            if self.current_token.type == TokenType.STAR:
                self.eat(TokenType.STAR)
                return Repetition(term)
            elif self.current_token.type == TokenType.PLUS:
                self.eat(TokenType.PLUS)
                return Sequence([term, Repetition(term)])
            else:
                self.eat(TokenType.QUESTION)
                return Optional(term)

        return term