from dataclasses import dataclass
from typing import List, Union
from enum import Enum, auto

class TokenType(Enum):
    IDENTIFIER = auto()
    TERMINAL = auto()
    EQUALS = auto()
    SEMICOLON = auto()
    COMMA = auto()
    PIPE = auto()
    LPAREN = auto()
    RPAREN = auto()
    LBRACE = auto()
    RBRACE = auto()
    LBRACKET = auto()
    RBRACKET = auto()
    EOF = auto()

@dataclass
class Token:
    type: TokenType
    value: str
    line: int
    col: int

@dataclass
class ASTNode: pass

@dataclass
class Terminal(ASTNode):
    value: str

@dataclass
class NonTerminal(ASTNode):
    name: str


@dataclass
class Sequence(ASTNode):
    items: List[ASTNode]

@dataclass
class Alternative(ASTNode):
    options: List[ASTNode]

@dataclass
class Repetition(ASTNode):
    item: ASTNode

@dataclass
class Optional(ASTNode):
    item: ASTNode

@dataclass
class Rule(ASTNode):
    name: str
    definition: ASTNode


# lexer used to tokenize the grammar input
class GrammarLexer:
    def __init__(self, text: str):
        self.text = text
        self.pos = 0
        self.line = 1
        self.col = 1
        self.current_char = self.text[0] if self.text else None

    def advance(self):
        if self.current_char == '\n':
            self.line += 1
            self.col = 1
        else:
            self.col += 1
            
        self.pos += 1
        self.current_char = self.text[self.pos] if self.pos < len(self.text) else None

    def skip_whitespace(self):
        while self.current_char and self.current_char.isspace():
            self.advance()

    def error(self):
        raise Exception(f"Bad char '{self.current_char}' at {self.line}:{self.col}")

    def identifier(self):
        result = ''
        start_col = self.col

        while self.current_char and (self.current_char.isalnum() or self.current_char == '_'):
            result += self.current_char
            self.advance()

        return Token(TokenType.IDENTIFIER, result, self.line, start_col)

    def terminal(self):
        result = ''
        start_col = self.col
        self.advance() 
        while self.current_char and self.current_char != '"':
            result += self.current_char
            self.advance()

        if self.current_char == '"':
            self.advance()
            return Token(TokenType.TERMINAL, result, self.line, start_col)
        raise Exception(f"Unclosed string at line {self.line}, col {start_col}")

    def get_next_token(self):
        while self.current_char:
            if self.current_char.isspace():
                self.skip_whitespace()
                continue

            if self.current_char.isalpha():
                return self.identifier()

            if self.current_char == '"':
                return self.terminal()

            token_map = {
                '=': TokenType.EQUALS, ';': TokenType.SEMICOLON, ',': TokenType.COMMA,
                '|': TokenType.PIPE, '(': TokenType.LPAREN, ')': TokenType.RPAREN,
                '{': TokenType.LBRACE, '}': TokenType.RBRACE,
                '[': TokenType.LBRACKET, ']': TokenType.RBRACKET,
            }

            if self.current_char in token_map:
                tok = Token(token_map[self.current_char], self.current_char, self.line, self.col)
                self.advance()
                return tok

            self.error()

        return Token(TokenType.EOF, '', self.line, self.col)

#  basic parser for the grammar
class GrammarParser:
    def __init__(self, text: str):
        self.lexer = GrammarLexer(text)
        self.current_token = self.lexer.get_next_token()
        self.rules = []

    def eat(self, token_type: TokenType):

        if self.current_token.type == token_type:
            self.current_token = self.lexer.get_next_token()
        else:
            self.error(f"Expected {token_type.name}, got {self.current_token.type.name}")

    def error(self, msg: str):
        raise Exception(f"[Parser] {msg} at line {self.current_token.line}, col {self.current_token.col}")

    def parse_grammar(self) -> List[Rule]:
        while self.current_token.type != TokenType.EOF:
            rule = self.parse_rule()
            if rule:
                self.rules.append(rule)

        return self.rules

    def parse_rule(self):
        if self.current_token.type != TokenType.IDENTIFIER:
            self.error("Expected rule name")
        name = self.current_token.value

        self.eat(TokenType.IDENTIFIER)
        self.eat(TokenType.EQUALS)

        body = self.parse_alternatives()
        self.eat(TokenType.SEMICOLON)
        return Rule(name, body)

    def parse_alternatives(self):
        terms = [self.parse_sequence()]

        while self.current_token.type == TokenType.PIPE:
            self.eat(TokenType.PIPE)
            terms.append(self.parse_sequence())

        return terms[0] if len(terms) == 1 else Alternative(terms)

    def parse_sequence(self):
        terms = [self.parse_element()]
        while self.current_token.type == TokenType.COMMA:
            self.eat(TokenType.COMMA)
            terms.append(self.parse_element())

        return terms[0] if len(terms) == 1 else Sequence(terms)

    def parse_element(self):
        tok = self.current_token
        if tok.type == TokenType.TERMINAL:
            self.eat(TokenType.TERMINAL)
            return Terminal(tok.value)

        elif tok.type == TokenType.IDENTIFIER:
            self.eat(TokenType.IDENTIFIER)
            return NonTerminal(tok.value)

        elif tok.type == TokenType.LPAREN:
            self.eat(TokenType.LPAREN)
            expr = self.parse_alternatives()
            self.eat(TokenType.RPAREN)
            return expr

        elif tok.type == TokenType.LBRACE:
            self.eat(TokenType.LBRACE)
            expr = self.parse_alternatives()
            self.eat(TokenType.RBRACE)
            return Repetition(expr)

        elif tok.type == TokenType.LBRACKET:
            self.eat(TokenType.LBRACKET)
            expr = self.parse_alternatives()
            self.eat(TokenType.RBRACKET)
            return Optional(expr)

        # print(f"Unexpected: {tok}")
        self.error("Unexpected token in grammar element")


