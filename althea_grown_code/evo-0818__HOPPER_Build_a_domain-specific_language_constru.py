#!/usr/bin/env python3
"""DSL Constructor - Grace Hopper Archetype Module
Defines vocabularies for problem domains, then writes solutions in those vocabularies.
"""

import re
from dataclasses import dataclass
from typing import List, Dict, Callable, Any


@dataclass
class Primitive:
    name: str
    signature: str
    impl: Callable
    doc: str


@dataclass
class CompositionRule:
    pattern: str
    transformer: Callable
    precedence: int


class DSLConstructor:
    def __init__(self, domain_name: str):
        self.domain = domain_name
        self.primitives: Dict[str, Primitive] = {}
        self.rules: List[CompositionRule] = []
        self.compiled_grammar = None
    
    def define_primitive(self, name: str, sig: str, impl: Callable, doc: str = ""):
        """Define atomic vocabulary element"""
        self.primitives[name] = Primitive(name, sig, impl, doc)
        return self
    
    def define_composition(self, pattern: str, transformer: Callable, precedence: int = 0):
        """Define how primitives compose"""
        self.rules.append(CompositionRule(pattern, transformer, precedence))
        self.rules.sort(key=lambda r: r.precedence, reverse=True)
        return self
    
    def compile_expression(self, expr: str) -> Callable:
        """Compile domain expression to executable function"""
        tokens = self._tokenize(expr)
        ast = self._parse(tokens)
        return self._codegen(ast)
    
    def _tokenize(self, expr: str) -> List[str]:
        return re.findall(r'\w+|[().,|&]', expr)
    
    def _parse(self, tokens: List[str]) -> Dict:
        """Simple recursive descent parser"""
        if not tokens:
            return {"type": "noop"}
        
        token = tokens[0]
        if token in self.primitives:
            return {"type": "primitive", "name": token, "impl": self.primitives[token].impl}
        
        for rule in self.rules:
            match = re.match(rule.pattern, " ".join(tokens))
            if match:
                return {"type": "composition", "rule": rule, "matched": match.groups()}
        
        return {"type": "sequence", "tokens": tokens}
    
    def _codegen(self, ast: Dict) -> Callable:
        """Generate executable code from AST"""
        if ast["type"] == "primitive":
            return ast["impl"]
        elif ast["type"] == "composition":
            return ast["rule"].transformer(ast["matched"])
        else:
            return lambda *args: args
    
    def export_vocabulary(self) -> str:
        """Generate human-readable vocabulary spec"""
        lines = [f"DOMAIN: {self.domain}", "PRIMITIVES:"]
        for p in self.primitives.values():
            lines.append(f"  {p.name} :: {p.signature} -- {p.doc}")
        lines.append("COMPOSITION_RULES:")
        for r in self.rules:
            lines.append(f"  [{r.precedence}] {r.pattern}")
        return "\n".join(lines)