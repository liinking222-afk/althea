import re
from typing import Dict, List, Callable, Any, Optional
from dataclasses import dataclass

@dataclass
class VocabTerm:
    pattern: str
    handler: Callable
    doc: str

class ProblemVocabulary:
    def __init__(self, domain: str):
        self.domain = domain
        self.terms: Dict[str, VocabTerm] = {}
        self.compiled_patterns: List[tuple] = []
    
    def define(self, term: str, pattern: str, doc: str = ""):
        def decorator(handler: Callable):
            self.terms[term] = VocabTerm(pattern, handler, doc)
            self._recompile()
            return handler
        return decorator
    
    def _recompile(self):
        self.compiled_patterns = [
            (re.compile(term.pattern, re.IGNORECASE), term.handler, name)
            for name, term in self.terms.items()
        ]
    
    def parse(self, utterance: str) -> Optional[tuple[str, Dict[str, Any]]]:
        for regex, handler, term_name in self.compiled_patterns:
            match = regex.search(utterance)
            if match:
                return (term_name, match.groupdict())
        return None
    
    def execute(self, utterance: str, context: Dict = None) -> Any:
        context = context or {}
        result = self.parse(utterance)
        if result:
            term_name, params = result
            handler = self.terms[term_name].handler
            return handler(**params, **context)
        return None
    
    def introspect(self) -> str:
        lines = [f"VOCABULARY[{self.domain}]:"]
        for name, term in self.terms.items():
            lines.append(f"  {name}: {term.doc or term.pattern}")
        return "\n".join(lines)

def create_vocabulary(domain: str) -> ProblemVocabulary:
    return ProblemVocabulary(domain)

VOCAB_REGISTRY: Dict[str, ProblemVocabulary] = {}

def register_vocabulary(vocab: ProblemVocabulary):
    VOCAB_REGISTRY[vocab.domain] = vocab
    return vocab