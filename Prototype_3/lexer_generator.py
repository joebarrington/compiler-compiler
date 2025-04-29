#Thss is the lexer code. It is generated from within the parser generator and is written to a file as a raw string.
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
        self.current_char = self.text[0] if self.text else None

        self.symbols = set("{}()[].,;+-*/&|<>=~")

    #basic lexer functions like advance, peek etc.
    def advance(self):
        if self.current_char == '\n':
            self.line += 1
            self.column = 1

        else:
            self.column += 1
        self.pos += 1
        self.current_char = self.text[self.pos] if self.pos < len(self.text) else None

    def peek(self):
        next_pos = self.pos + 1
        return self.text[next_pos] if next_pos < len(self.text) else None

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
        else:
            return False

        return True

    #helper function to create tokens
    def make_token(self, token_type, value, start_col):
    
        return Token(token_type, value, self.line, start_col)

    ##Function to identify keywords and identifiers
    def identifier(self):
    
        start_col = self.column
        result = ''

        while self.current_char and (self.current_char.isalnum() or self.current_char == '_'):
            result += self.current_char
            self.advance()

        token_type = TokenType.KEYWORD if result in self.keywords else TokenType.IDENTIFIER
        return self.make_token(token_type, result, start_col)
    #function to get numbers
    def number(self):
        start_col = self.column
        result = ''
        # print(f"Current char: {self.current_char}")

        while self.current_char and self.current_char.isdigit():
            result += self.current_char
            self.advance()

        return self.make_token(TokenType.INTEGER, result, start_col)
    #function for strings
    def string(self):
        start_col = self.column

        result = ''
        self.advance() 

        while self.current_char and self.current_char != '"':
            result += self.current_char
            self.advance()

        if self.current_char == '"':
            self.advance() 
            return self.make_token(TokenType.STRING, result, start_col)

        raise Exception(f"Unterminated string at line {self.line}, column {start_col}")

    #Function determines what the next token is and calls the corresponding function to get it
    def get_next_token(self):
        while self.current_char:
        
            if self.current_char.isspace():
                self.skip_whitespace()
                continue

            if self.current_char == '/' and self.peek() in {'/', '*'}:
                self.skip_comment()
                continue

            if self.current_char.isalpha() or self.current_char == '_':
                return self.identifier()

            if self.current_char.isdigit():
                return self.number()

            if self.current_char == '"':
                return self.string()

            if self.current_char in self.symbols:
                tok = self.make_token(TokenType.SYMBOL, self.current_char, self.column)

                self.advance()
                return tok

            raise Exception(f"Invalid character '{self.current_char}' at line {self.line}, column {self.column}")

        print(self.current_char)
        return self.make_token(TokenType.EOF, '', self.column)

'''
