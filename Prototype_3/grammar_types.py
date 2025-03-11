from dataclasses import dataclass
from typing import List, Union
from enum import Enum, auto

class TokenType(Enum):
    IDENTIFIER = auto()
    TERMINAL = auto()
    EQUALS = auto()      # For both = and ::=
    SEMICOLON = auto()
    COMMA = auto()
    PIPE = auto()
    LPAREN = auto()
    RPAREN = auto()
    LBRACE = auto()
    RBRACE = auto()
    LBRACKET = auto()
    RBRACKET = auto()
    LANGLE = auto()      # For <
    RANGLE = auto()      # For >
    STAR = auto()        # For *
    PLUS = auto()        # For +
    QUESTION = auto()    # For ?
    EOF = auto()

@dataclass
class Token:
    type: TokenType
    value: str
    line: int
    col: int

@dataclass
class ASTNode:
    """Base class for all AST nodes"""
    pass

@dataclass
class Terminal(ASTNode):
    """Represents a terminal symbol (like a string literal or keyword)"""
    value: str

@dataclass
class NonTerminal(ASTNode):
    """Represents a non-terminal symbol (like a rule reference)"""
    name: str

@dataclass
class Sequence(ASTNode):
    """Represents a sequence of grammar elements"""
    items: List[ASTNode]

@dataclass
class Alternative(ASTNode):
    """Represents alternative productions (separated by |)"""
    options: List[ASTNode]

@dataclass
class Repetition(ASTNode):
    """Represents repetition (*, +, or {...})"""
    item: ASTNode

@dataclass
class Optional(ASTNode):
    """Represents optional elements ([...] or ?)"""
    item: ASTNode

@dataclass
class Rule(ASTNode):
    """Represents a complete grammar rule"""
    name: str
    definition: ASTNode

# Base class for both BNF and EBNF lexers
class BaseLexer:
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

    def peek(self, n=1) -> Union[str, None]:
        peek_pos = self.pos + n
        return self.text[peek_pos] if peek_pos < len(self.text) else None

    def skip_whitespace(self):
        while self.current_char and self.current_char.isspace():
            self.advance()

    def skip_comment(self):
        while self.current_char and self.current_char != '\n':
            self.advance()
        if self.current_char:
            self.advance()

# Base class for both BNF and EBNF parsers
class BaseParser:
    def __init__(self, text: str):
        self.rules = []

    def error(self, expected: str):
        raise NotImplementedError("Subclasses must implement error()")

    def eat(self, token_type: TokenType):
        raise NotImplementedError("Subclasses must implement eat()")

    def parse_grammar(self) -> List[Rule]:
        raise NotImplementedError("Subclasses must implement parse_grammar()")