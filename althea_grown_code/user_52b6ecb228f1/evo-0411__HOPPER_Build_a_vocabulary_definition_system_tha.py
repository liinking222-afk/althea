"""
Vocabulary Builder - Define problem-domain DSLs before solving
Hopper archetype: Name the concepts first, then speak in those names
"""

from typing import Dict, List, Callable, Any
import re
import json

class Vocabulary:
    def __init__(self, domain: str):
        self.domain = domain
        self.terms: Dict[str, Dict[str, Any]] = {}
        self.operators: Dict[str, Callable] = {}
        self.grammar: List[str] = []
    
    def define(self, term: str, meaning: str, examples: List[str] = None):
        """Define a term in this vocabulary"""
        self.terms[term] = {
            "meaning": meaning,
            "examples": examples or [],
            "usage_count": 0
        }
        return self
    
    def operator(self, symbol: str, func: Callable):
        """Register a domain-specific operator"""
        self.operators[symbol] = func
        return self
    
    def rule(self, pattern: str):
        """Add a grammar rule for combining terms"""
        self.grammar.append(pattern)
        return self
    
    def translate(self, expression: str) -> str:
        """Translate domain expression to executable form"""
        result = expression
        for term, meta in self.terms.items():
            if term in result:
                meta["usage_count"] += 1
        return result
    
    def execute(self, expression: str, context: Dict = None):
        """Parse and execute in this vocabulary"""
        ctx = context or {}
        translated = self.translate(expression)
        for symbol, func in self.operators.items():
            if symbol in translated:
                return func(translated, ctx)
        return translated
    
    def export(self) -> str:
        """Export vocabulary as reusable JSON"""
        return json.dumps({
            "domain": self.domain,
            "terms": self.terms,
            "grammar": self.grammar
        }, indent=2)

def build_vocabulary(domain: str) -> Vocabulary:
    """Factory for creating new domain vocabularies"""
    return Vocabulary(domain)