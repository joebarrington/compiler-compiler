
class GeneratedParser:
    def __init__(self, text):
        self.text = text
        self.pos = 0
        self.length = len(text)
        
    def skip_whitespace(self):
        while self.pos < self.length and self.text[self.pos].isspace():
            self.pos += 1
            
    def match(self, terminal):
        self.skip_whitespace()
        if self.pos < self.length:
            current_text = self.text[self.pos:]
            if current_text.startswith(terminal):
                self.pos += len(terminal)
                return True
        return False
    
    def _repeat_parse(self, parse_fn):
        while True:
            start_pos = self.pos
            if not parse_fn():
                self.pos = start_pos
                break
        return True
        
    def parse(self):
        self.pos = 0
        result = self.parse_start()
        self.skip_whitespace()
        if self.pos < self.length:
            raise SyntaxError(f"Unexpected input at position {self.pos}")
        return result

    def parse_start(self):
        return self.parse_expr()

    def parse_expr(self):
        start_pos = self.pos
        self.skip_whitespace()

        if self.parse_term() and self._repeat_parse(lambda: (self.match("+") or self.match("-")) and self.parse_term()):
            return True

        self.pos = start_pos
        return False

    def parse_term(self):
        start_pos = self.pos
        self.skip_whitespace()

        if self.parse_factor() and self._repeat_parse(lambda: (self.match("*") or self.match("/")) and self.parse_factor()):
            return True

        self.pos = start_pos
        return False

    def parse_factor(self):
        start_pos = self.pos
        self.skip_whitespace()

        if self.parse_number() or self.match("(") and self.parse_expr() and self.match(")"):
            return True

        self.pos = start_pos
        return False

    def parse_number(self):
        start_pos = self.pos
        self.skip_whitespace()

        if self.parse_digit() and self._repeat_parse(lambda: self.parse_digit()):
            return True

        self.pos = start_pos
        return False

    def parse_digit(self):
        start_pos = self.pos
        self.skip_whitespace()

        if self.match("0") or self.match("1") or self.match("2") or self.match("3") or self.match("4") or self.match("5") or self.match("6") or self.match("7") or self.match("8") or self.match("9"):
            return True

        self.pos = start_pos
        return False
