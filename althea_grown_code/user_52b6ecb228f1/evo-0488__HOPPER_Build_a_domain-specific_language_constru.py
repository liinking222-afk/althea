import inspect
from typing import Any, Callable, Dict, List, Optional
from dataclasses import dataclass, field

@dataclass
class VocabularyTerm:
    name: str
    signature: str
    implementation: Optional[Callable] = None
    compose_with: List[str] = field(default_factory=list)

class DomainVocabulary:
    def __init__(self, domain_name: str):
        self.domain = domain_name
        self.terms: Dict[str, VocabularyTerm] = {}
        self.fluent_chain: List[str] = []
        
    def define(self, name: str, sig: str, impl: Optional[Callable] = None):
        self.terms[name] = VocabularyTerm(name, sig, impl)
        return self
    
    def compose(self, term1: str, term2: str):
        if term1 in self.terms:
            self.terms[term1].compose_with.append(term2)
        return self
    
    def build_language(self) -> type:
        vocab = self
        
        class FluentLanguage:
            def __init__(self):
                self._context = {}
                self._chain = []
                
            def __getattr__(self, name: str):
                if name.startswith('_'):
                    return object.__getattribute__(self, name)
                if name in vocab.terms:
                    def method(*args, **kwargs):
                        self._chain.append((name, args, kwargs))
                        term = vocab.terms[name]
                        if term.implementation:
                            result = term.implementation(*args, **kwargs)
                            self._context[name] = result
                        return self
                    return method
                raise AttributeError(f"Term '{name}' not in {vocab.domain} vocabulary")
            
            def execute(self):
                return self._context
            
            def vocabulary(self):
                return {k: v.signature for k, v in vocab.terms.items()}
        
        FluentLanguage.__name__ = f"{vocab.domain}Language"
        return FluentLanguage
    
    def export_spec(self) -> str:
        spec = [f"DOMAIN: {self.domain}", "VOCABULARY:"]
        for name, term in self.terms.items():
            spec.append(f"  {name}: {term.signature}")
            if term.compose_with:
                spec.append(f"    → {', '.join(term.compose_with)}")
        return "\n".join(spec)