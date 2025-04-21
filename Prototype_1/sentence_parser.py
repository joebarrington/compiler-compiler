
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
        return self.parse_sentence()

    def parse_sentence(self):
        start_pos = self.pos
        self.skip_whitespace()

        if self.parse_subject() and self.parse_verb() and self.parse_object():
            return True

        self.pos = start_pos
        return False

    def parse_subject(self):
        start_pos = self.pos
        self.skip_whitespace()

        if self.parse_article() and self.parse_noun():
            return True

        self.pos = start_pos
        return False

    def parse_object(self):
        start_pos = self.pos
        self.skip_whitespace()

        if self.parse_article() and self.parse_noun():
            return True

        self.pos = start_pos
        return False

    def parse_article(self):
        start_pos = self.pos
        self.skip_whitespace()

        if self.match("the") or self.match("a"):
            return True

        self.pos = start_pos
        return False

    def parse_noun(self):
        start_pos = self.pos
        self.skip_whitespace()

        if self.match("cat") or self.match("dog") or self.match("bird"):
            return True

        self.pos = start_pos
        return False

    def parse_verb(self):
        start_pos = self.pos
        self.skip_whitespace()

        if self.match("chases") or self.match("catches") or self.match("watches"):
            return True

        self.pos = start_pos
        return False
