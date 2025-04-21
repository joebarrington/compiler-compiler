
lexer_code =  r'''
from dataclasses import dataclass

class TokenType:
    IDENTIFIER = "IDENTIFIER"
    INTEGER = "INTEGER"
    STRING = "STRING"
    KEYWORD = "KEYWORD"
    SYMBOL = "SYMBOL"
    EOF = "EOF"

@dataclass
class Token:
    type: str
    value: str
    line: int
    column: int

class StandardLexer:
    
    def __init__(self, text: str, keywords: set):
        self.text = text
        self.keywords = keywords
        self.pos = 0
        self.line = 1
        self.column = 1
        self.current_char = self.text[0] if text else None
        
        self.symbols = {
            '{', '}', '(', ')', '[', ']', '.', ',', ';', '+', '-',
            '*', '/', '&', '|', '<', '>', '=', '~'
        }

    def error(self):
        char = self.current_char if self.current_char else 'EOF'
        raise Exception(f'Invalid character {char} at line {self.line}, column {self.column}')

    def advance(self):
        self.pos += 1
        if self.current_char == '\n':
            self.line += 1
            self.column = 1
        else:
            self.column += 1
        self.current_char = self.text[self.pos] if self.pos < len(self.text) else None

    def peek(self):
        peek_pos = self.pos + 1
        return self.text[peek_pos] if peek_pos < len(self.text) else None

    def skip_whitespace(self):
        while self.current_char and self.current_char.isspace():
            self.advance()

    def skip_comment(self):
        if self.peek() == '/':
            while self.current_char and self.current_char != '\n':
                self.advance()
        elif self.peek() == '*':
            self.advance()
            self.advance()
            while self.current_char:
                if self.current_char == '*' and self.peek() == '/':
                    self.advance()
                    self.advance()
                    break
                self.advance()

    def identifier(self):
        result = ''
        start_column = self.column
        
        while self.current_char and (self.current_char.isalnum() or self.current_char == '_'):
            result += self.current_char
            self.advance()
        
        if result in self.keywords:
            return Token(TokenType.KEYWORD, result, self.line, start_column)
        return Token(TokenType.IDENTIFIER, result, self.line, start_column)

    def number(self):
        result = ''
        start_column = self.column
        
        while self.current_char and self.current_char.isdigit():
            result += self.current_char
            self.advance()
            
        return Token(TokenType.INTEGER, result, self.line, start_column)

    def string(self):
        result = ''
        start_column = self.column
        self.advance()
        
        while self.current_char and self.current_char != '"':
            result += self.current_char
            self.advance()
            
        if self.current_char == '"':
            self.advance()
            return Token(TokenType.STRING, result, self.line, start_column)
        else:
            raise Exception(f'Unterminated string at line {self.line}, column {start_column}')

    def get_next_token(self):
        while self.current_char:
            if self.current_char.isspace():
                self.skip_whitespace()
                continue

            if self.current_char == '/':
                current_column = self.column
                
                if self.peek() in ['/', '*']:
                    self.skip_comment()
                    continue
                else:
                    symbol = self.current_char
                    self.advance()
                    return Token(TokenType.SYMBOL, symbol, self.line, current_column)

            if self.current_char.isalpha():
                return self.identifier()

            if self.current_char.isdigit():
                return self.number()

            if self.current_char == '"':
                return self.string()

            if self.current_char in self.symbols:
                symbol = self.current_char
                token = Token(TokenType.SYMBOL, symbol, self.line, self.column)
                self.advance()
                return token

            self.error()

        return Token(TokenType.EOF, '', self.line, self.column)

'''
