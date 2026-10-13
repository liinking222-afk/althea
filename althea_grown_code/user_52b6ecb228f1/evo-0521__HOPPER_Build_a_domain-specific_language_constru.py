import re
from typing import Dict, Callable, Any, List, Tuple

class VocabularyDSL:
    """Hopper-style vocabulary-first problem solver: define language, then solve."""
    
    def __init__(self, domain: str):
        self.domain = domain
        self.vocabulary: Dict[str, Callable] = {}
        self.grammar: List[Tuple[str, str]] = []
        self.compositions: Dict[str, str] = {}
    
    def define(self, term: str, implementation: Callable) -> 'VocabularyDSL':
        """Define a vocabulary term with its executable meaning."""
        self.vocabulary[term] = implementation
        return self
    
    def rule(self, pattern: str, expansion: str) -> 'VocabularyDSL':
        """Define a grammar rule for composing terms."""
        self.grammar.append((pattern, expansion))
        return self
    
    def compose(self, name: str, expression: str) -> 'VocabularyDSL':
        """Compose a higher-level operation from vocabulary."""
        self.compositions[name] = expression
        return self
    
    def execute(self, expression: str, context: Dict[str, Any] = None) -> Any:
        """Execute an expression in this domain vocabulary."""
        ctx = context or {}
        
        # Apply grammar transformations
        expanded = expression
        for pattern, replacement in self.grammar:
            expanded = re.sub(pattern, replacement, expanded)
        
        # Resolve compositions
        for name, composition in self.compositions.items():
            expanded = expanded.replace(name, f"({composition})")
        
        # Build executable from vocabulary
        tokens = re.findall(r'\w+|[().]', expanded)
        
        def evaluate(expr: str) -> Any:
            # Simple recursive evaluator for vocabulary terms
            expr = expr.strip()
            if expr in self.vocabulary:
                return self.vocabulary[expr]
            if expr in ctx:
                return ctx[expr]
            # Handle composition chains: term1.term2.term3
            if '.' in expr:
                parts = expr.split('.')
                result = evaluate(parts[0])
                for part in parts[1:]:
                    if callable(result):
                        result = result()
                    result = self.vocabulary.get(part, lambda x=result: x)(result)
                return result
            return expr
        
        return evaluate(expanded)
    
    def introspect(self) -> Dict[str, Any]:
        """Return the complete vocabulary definition for this domain."""
        return {
            'domain': self.domain,
            'terms': list(self.vocabulary.keys()),
            'grammar_rules': len(self.grammar),
            'compositions': list(self.compositions.keys())
        }