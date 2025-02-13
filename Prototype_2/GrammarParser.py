from dataclasses import dataclass
from typing import List, Optional, Union, List
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
class ASTNode:
    pass

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

class GrammarLexer:
    def __init__(self, text: str):
        self.text = text
        self.pos = 0
        self.line = 1
        self.col = 1
        self.current_char = self.text[0] if text else None

    def error(self):
        raise Exception(f'Invalid character {self.current_char} at line {self.line}, column {self.col}')

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

    def identifier(self) -> Token:
        result = ''
        start_col = self.col
        
        while self.current_char and (self.current_char.isalnum() or self.current_char == '_'):
            result += self.current_char
            self.advance()
            
        return Token(TokenType.IDENTIFIER, result, self.line, start_col)

    def terminal(self) -> Token:
        result = ''
        start_col = self.col
        self.advance()
        
        while self.current_char and self.current_char != '"':
            result += self.current_char
            self.advance()
            
        if self.current_char == '"':
            self.advance()
            return Token(TokenType.TERMINAL, result, self.line, start_col)
        else:
            raise Exception(f'Unterminated string at line {self.line}, column {start_col}')

    def get_next_token(self) -> Token:
        while self.current_char:
            if self.current_char.isspace():
                self.skip_whitespace()
                continue

            if self.current_char.isalpha():
                return self.identifier()

            if self.current_char == '"':
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
            }

            if self.current_char in char_to_token:
                token = Token(char_to_token[self.current_char], self.current_char, self.line, self.col)
                self.advance()
                return token

            self.error()

        return Token(TokenType.EOF, '', self.line, self.col)

class GrammarParser:
    def __init__(self, text: str):
        self.lexer = GrammarLexer(text)
        self.current_token = self.lexer.get_next_token()
        self.rules: List[Rule] = []

    def error(self, expected: str):
        raise Exception(
            f'Unexpected token {self.current_token.value} at line {self.current_token.line}, '
            f'column {self.current_token.col}. Expected {expected}'
        )

    def eat(self, token_type: TokenType):
        if self.current_token.type == token_type:
            self.current_token = self.lexer.get_next_token()
        else:
            self.error(str(token_type))

    def parse_grammar(self) -> List[Rule]:
        """Parse a complete grammar"""
        while self.current_token.type != TokenType.EOF:
            rule = self.parse_rule()
            if rule:
                self.rules.append(rule)
        return self.rules

    def parse_rule(self) -> Union[Rule, None]:
        """Parse a single grammar rule"""
        if self.current_token.type != TokenType.IDENTIFIER:
            return None

        name = self.current_token.value
        self.eat(TokenType.IDENTIFIER)
        self.eat(TokenType.EQUALS)
        
        definition = self.parse_expression()
        self.eat(TokenType.SEMICOLON)
        
        return Rule(name, definition)

    def parse_expression(self) -> ASTNode:
        """Parse an expression (alternatives)"""
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
        """Parse a single term"""
        if self.current_token.type == TokenType.TERMINAL:
            value = self.current_token.value
            self.eat(TokenType.TERMINAL)
            return Terminal(value)
            
        elif self.current_token.type == TokenType.IDENTIFIER:
            name = self.current_token.value
            self.eat(TokenType.IDENTIFIER)
            return NonTerminal(name)
            
        elif self.current_token.type == TokenType.LPAREN:
            self.eat(TokenType.LPAREN)
            expr = self.parse_expression()
            self.eat(TokenType.RPAREN)
            return expr
            
        elif self.current_token.type == TokenType.LBRACE:
            self.eat(TokenType.LBRACE)
            expr = self.parse_expression()
            self.eat(TokenType.RBRACE)
            return Repetition(expr)
            
        elif self.current_token.type == TokenType.LBRACKET:
            self.eat(TokenType.LBRACKET)
            expr = self.parse_expression()
            self.eat(TokenType.RBRACKET)
            return Optional(expr)
            
        else:
            self.error('term')
