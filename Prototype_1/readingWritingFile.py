import re
from dataclasses import dataclass
from typing import List, Dict, Set

@dataclass
class Rule:
    name: str
    alternatives: List[List[dict]]

class GrammarParser:
    def __init__(self, grammar: str):
        self.grammar = grammar
        self.rules: Dict[str, Rule] = {}
        self.terminals: Set[str] = set()
        self.parse_grammar()

    def parse_grammar(self):
        rule_strings = [r.strip() for r in self.grammar.split(';') if r.strip()]
        
        for rule_str in rule_strings:
            if '=' not in rule_str:
                continue
                
            name, definition = rule_str.split('=', 1)
            name = name.strip()
            
            tokens = re.findall(r'"[^"]*"|\{[^}]*\}|\([^)]*\)|\w+|[,|]', definition.strip())
            
            alternatives = []
            current_sequence = []
            nesting_level = 0
            
            for token in tokens:
                token = token.strip()
                
                if token.startswith('{') or token.startswith('('):
                    nesting_level += 1
                elif token.endswith('}') or token.endswith(')'):
                    nesting_level -= 1
                
                if token == '|' and nesting_level == 0:
                    if current_sequence:
                        alternatives.append(current_sequence)
                    current_sequence = []
                    continue
                
                if token.startswith('"') and token.endswith('"'):
                    terminal = token[1:-1]
                    current_sequence.append({'type': 'terminal', 'value': terminal})
                    self.terminals.add(terminal)
                
                elif token.startswith('{') and token.endswith('}'):
                    inner_content = token[1:-1].strip()
                    inner_tokens = re.findall(r'"[^"]*"|\([^)]*\)|\w+|[,]', inner_content)
                    inner_sequence = []
                    
                    for inner_token in inner_tokens:
                        inner_token = inner_token.strip()
                        if inner_token == ',':
                            continue
                            
                        if inner_token.startswith('('):
                            group_content = inner_token[1:-1].strip()
                            group_alternatives = []
                            for group_part in group_content.split('|'):
                                part = group_part.strip()
                                if part.startswith('"'):
                                    term = part[1:-1]
                                    group_alternatives.append({'type': 'terminal', 'value': term})
                                    self.terminals.add(term)
                                else:
                                    group_alternatives.append({'type': 'nonterminal', 'value': part})
                            inner_sequence.append({'type': 'group', 'value': group_alternatives})
                        elif inner_token.startswith('"'):
                            term = inner_token[1:-1]
                            inner_sequence.append({'type': 'terminal', 'value': term})
                            self.terminals.add(term)
                        elif inner_token.isalpha():
                            inner_sequence.append({'type': 'nonterminal', 'value': inner_token})
                    
                    current_sequence.append({'type': 'repetition', 'value': inner_sequence})
                
                elif token.startswith('(') and token.endswith(')'):
                    group_content = token[1:-1].strip()
                    group_alternatives = []
                    for group_part in group_content.split('|'):
                        part = group_part.strip()
                        if part.startswith('"'):
                            term = part[1:-1]
                            group_alternatives.append({'type': 'terminal', 'value': term})
                            self.terminals.add(term)
                        else:
                            group_alternatives.append({'type': 'nonterminal', 'value': part})
                    current_sequence.append({'type': 'group', 'value': group_alternatives})
                
                elif token.isalpha():
                    current_sequence.append({'type': 'nonterminal', 'value': token})
            
            if current_sequence:
                alternatives.append(current_sequence)
            
            self.rules[name] = Rule(name, alternatives)

class ParserGenerator:
    def __init__(self, grammar: str):
        self.grammar_parser = GrammarParser(grammar)
        self.rules = self.grammar_parser.rules
        self.terminals = self.grammar_parser.terminals

    def generate_rule_method(self, rule_name: str, rule: Rule) -> str:
        method_code = f"\n    def parse_{rule_name}(self):\n"
        method_code += "        start_pos = self.pos\n"
        method_code += "        self.skip_whitespace()\n\n"
        
        alternatives = []
        for sequence in rule.alternatives:
            seq_parts = []
            
            for i, item in enumerate(sequence):
                if item['type'] == 'terminal':
                    seq_parts.append(f'self.match("{item["value"]}")')
                
                elif item['type'] == 'nonterminal':
                    seq_parts.append(f'self.parse_{item["value"]}()')
                
                elif item['type'] == 'repetition':
                    if seq_parts:
                        initial_sequence = ' and '.join(seq_parts)
                        seq_parts = [initial_sequence]
                    
                    rep_parts = []
                    for rep_item in item['value']:
                        if rep_item['type'] == 'terminal':
                            rep_parts.append(f'self.match("{rep_item["value"]}")')
                        elif rep_item['type'] == 'nonterminal':
                            rep_parts.append(f'self.parse_{rep_item["value"]}()')
                        elif rep_item['type'] == 'group':
                            group_alts = []
                            for group_item in rep_item['value']:
                                if group_item['type'] == 'terminal':
                                    group_alts.append(f'self.match("{group_item["value"]}")')
                                else:
                                    group_alts.append(f'self.parse_{group_item["value"]}()')
                            if group_alts:
                                rep_parts.append(f"({' or '.join(group_alts)})")
                    
                    if rep_parts:
                        rep_sequence = ' and '.join(rep_parts)
                        seq_parts.append("self.repeat_parse(lambda: " + rep_sequence + ")")
                
                elif item['type'] == 'group':
                    group_alts = []
                    for group_item in item['value']:
                        if group_item['type'] == 'terminal':
                            group_alts.append(f'self.match("{group_item["value"]}")')
                        else:
                            group_alts.append(f'self.parse_{group_item["value"]}()')
                    if group_alts:
                        seq_parts.append(f"({' or '.join(group_alts)})")
            
            if seq_parts:
                alternatives.append(' and '.join(seq_parts))
        
        if alternatives:
            method_code += f"        if {' or '.join(alternatives)}:\n"
            method_code += "            return True\n\n"
        
        method_code += "        self.pos = start_pos\n"
        method_code += "        return False\n"
        
        return method_code




    def generate_parser(self) -> str:
        code = """
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
    
    def repeat_parse(self, parse_fn):
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
"""
        
        first_rule = next(iter(self.rules.keys()))
        code = code.replace("parse_expr()", f"parse_{first_rule}()")
        
        for rule_name, rule in self.rules.items():
            code += self.generate_rule_method(rule_name, rule)
        
        return code

def main():
    arithmetic_grammar = """
    expr = term , { ("+" | "-") , term } ;
    term = factor , { ("*" | "/") , factor } ;
    factor = number | "(" , expr , ")" ;
    number = digit , { digit } ;
    digit = "0" | "1" | "2" | "3" | "4" | "5" | "6" | "7" | "8" | "9" ;
    """

    sentence_grammar = """
    sentence = subject , verb , object ;
    subject = article , noun ;
    object = article , noun ;
    article = "the" | "a" ;
    noun = "cat" | "dog" | "bird" ;
    verb = "chases" | "catches" | "watches" ;
    """


    print("Generating arithmetic parser...")
    arithmetic_generator = ParserGenerator(arithmetic_grammar)
    arithmetic_parser_code = arithmetic_generator.generate_parser()
    print("\nDebugging Grammar Parsing:")
    for rule_name, rule in arithmetic_generator.rules.items():
        print(f"\nRule: {rule_name}")
        for alt in rule.alternatives:
            print("  Alternative:", alt)
    
    with open('arithmetic_parser.py', 'w') as f:
        f.write(arithmetic_parser_code)

    print("Generating sentence parser...")
    sentence_generator = ParserGenerator(sentence_grammar)
    sentence_parser_code = sentence_generator.generate_parser()
    
    with open('sentence_parser.py', 'w') as f:
        f.write(sentence_parser_code)

    print("\nTesting arithmetic parser...")
    exec(arithmetic_parser_code)
    test_expressions = [
        "3+*6",
        "3+6*2",
        "4*(5+6)",
        "10/(2+3)",
        "1+2+3",
        "1*2*3",
        "1+(2*3)"]
    
    
    for expr in test_expressions:
        arithmetic_parser = locals()['GeneratedParser'](expr)
        try:
            result = arithmetic_parser.parse()
            print(f"Valid arithmetic expression: {expr}")
        except SyntaxError as e:
            print(f"Invalid arithmetic expression: {expr} - {e}")

    print("\nTesting sentence parser...")
    test_sentences = ["a bird chases a dog", "the cat watches the bird"]
    
    exec(sentence_parser_code)
    for sentence in test_sentences:
        sentence_parser = locals()['GeneratedParser'](sentence)
        try:
            result = sentence_parser.parse()
            print(f"Valid sentence: {sentence}")
        except SyntaxError as e:
            print(f"Invalid sentence: {sentence} - {e}")



if __name__ == "__main__":
    main()