#!/usr/bin/env python3
"""DSL Constructor - Build languages for problem domains, not one-off solutions."""

import re
from typing import Dict, List, Callable, Any
from dataclasses import dataclass

@dataclass
class Vocabulary:
    """Problem domain vocabulary definition."""
    primitives: Dict[str, type]
    operators: Dict[str, Callable]
    combinators: List[str]

class DSLConstructor:
    """Build executable languages from vocabulary definitions."""
    
    def __init__(self, name: str, vocab: Vocabulary):
        self.name = name
        self.vocab = vocab
        self.grammar = {}
        self.runtime = {}
        
    def define_syntax(self, pattern: str, transformer: Callable) -> None:
        """Map surface syntax to semantic transformation."""
        self.grammar[pattern] = transformer
        
    def compile(self, source: str) -> Callable:
        """Compile domain code to executable."""
        tokens = self._tokenize(source)
        ast = self._parse(tokens)
        return self._codegen(ast)
    
    def _tokenize(self, source: str) -> List[str]:
        return re.findall(r'\w+|[^\w\s]', source)
    
    def _parse(self, tokens: List[str]) -> Dict[str, Any]:
        """Match tokens against grammar patterns."""
        for pattern, transformer in self.grammar.items():
            pattern_tokens = pattern.split()
            if self._matches(tokens, pattern_tokens):
                return {"transform": transformer, "tokens": tokens}
        return {"transform": lambda x: x, "tokens": tokens}
    
    def _matches(self, tokens: List[str], pattern: List[str]) -> bool:
        if len(tokens) != len(pattern):
            return False
        for t, p in zip(tokens, pattern):
            if p.startswith('<') and p.endswith('>'):
                continue
            if t != p:
                return False
        return True
    
    def _codegen(self, ast: Dict[str, Any]) -> Callable:
        """Generate executable from AST."""
        def executor(**kwargs):
            return ast["transform"](ast["tokens"], self.vocab, kwargs)
        return executor
    
    def extend(self, new_vocab: Vocabulary) -> 'DSLConstructor':
        """Evolve language with new vocabulary."""
        merged = Vocabulary(
            {**self.vocab.primitives, **new_vocab.primitives},
            {**self.vocab.operators, **new_vocab.operators},
            self.vocab.combinators + new_vocab.combinators
        )
        return DSLConstructor(f"{self.name}_extended", merged)

def create_temporal_dsl() -> DSLConstructor:
    """Example: temporal reasoning language."""
    vocab = Vocabulary(
        primitives={"instant": float, "duration": float, "timezone": str},
        operators={"after": lambda a, b: a > b, "before": lambda a, b: a < b},
        combinators=["sequence", "parallel", "choice"]
    )
    dsl = DSLConstructor("TemporalLogic", vocab)
    dsl.define_syntax("<instant> after <instant>", 
                     lambda t, v, k: v.operators["after"](t[0], t[2]))
    return dsl