import re
from typing import Dict, List, Tuple, Callable
from dataclasses import dataclass

@dataclass
class Vocabulary:
    domain: str
    primitives: Dict[str, Callable]
    combinators: Dict[str, Callable]
    grammar: str

class VocabularyCompiler:
    """HOPPER: Define the language of the problem space first."""
    
    def __init__(self):
        self.vocabularies: Dict[str, Vocabulary] = {}
    
    def observe_patterns(self, recent_actions: List[str]) -> str:
        """Extract domain from repeated patterns."""
        domains = {}
        for action in recent_actions:
            if match := re.search(r'\[(AUTOSYNTH|GROWTH|EVO).*?\] ([A-Z][a-z]+(?: [A-Z][a-z]+)*)', action):
                domain = match.group(2).lower().replace(' ', '_')
                domains[domain] = domains.get(domain, 0) + 1
        return max(domains.items(), key=lambda x: x[1])[0] if domains else "general"
    
    def define_vocabulary(self, domain: str, primitives: Dict[str, Callable], 
                         combinators: Dict[str, Callable], grammar: str) -> Vocabulary:
        """Define problem-space vocabulary before writing solutions."""
        vocab = Vocabulary(domain, primitives, combinators, grammar)
        self.vocabularies[domain] = vocab
        return vocab
    
    def compile_program(self, domain: str, expression: str) -> Callable:
        """Compile high-level expression into executable using domain vocabulary."""
        if domain not in self.vocabularies:
            raise ValueError(f"Vocabulary '{domain}' not defined")
        
        vocab = self.vocabularies[domain]
        namespace = {**vocab.primitives, **vocab.combinators}
        
        # Parse and compile expression in domain language
        tokens = expression.split()
        stack = []
        
        for token in tokens:
            if token in namespace:
                stack.append(namespace[token])
            else:
                stack.append(token)
        
        # Build composed function
        def compiled(*args, **kwargs):
            result = stack[0]
            for item in stack[1:]:
                if callable(item):
                    result = item(result)
            return result
        
        return compiled
    
    def extend_vocabulary(self, domain: str, new_primitives: Dict[str, Callable]):
        """Grow vocabulary as understanding deepens."""
        if domain in self.vocabularies:
            self.vocabularies[domain].primitives.update(new_primitives)