"""
/autonomous-hopper-vocabulary-builder
Vocabulary-First DSL Constructor
Grace Hopper lens: Define the language of the problem, then solve in that language.
"""

from typing import Dict, List, Callable, Any
import re
from dataclasses import dataclass, field

@dataclass
class Vocabulary:
    """A domain-specific vocabulary definition"""
    domain: str
    primitives: Dict[str, Callable] = field(default_factory=dict)
    combinators: Dict[str, Callable] = field(default_factory=dict)
    syntax_patterns: Dict[str, str] = field(default_factory=dict)
    
    def define_primitive(self, word: str, implementation: Callable):
        """Define a basic vocabulary word"""
        self.primitives[word] = implementation
        return self
    
    def define_combinator(self, word: str, implementation: Callable):
        """Define a word that combines other words"""
        self.combinators[word] = implementation
        return self
    
    def define_syntax(self, name: str, pattern: str):
        """Define a syntax pattern for this vocabulary"""
        self.syntax_patterns[name] = pattern
        return self
    
    def compile(self, expression: str) -> Any:
        """Compile an expression in this vocabulary to executable form"""
        # Match against syntax patterns
        for name, pattern in self.syntax_patterns.items():
            match = re.match(pattern, expression.strip())
            if match:
                return self._execute_pattern(name, match.groupdict())
        
        # Fallback: try direct word lookup
        words = expression.split()
        if words[0] in self.primitives:
            return self.primitives[words[0]](*words[1:])
        if words[0] in self.combinators:
            return self.combinators[words[0]](*words[1:])
        
        raise ValueError(f"Expression '{expression}' not understood in {self.domain} vocabulary")
    
    def _execute_pattern(self, pattern_name: str, captures: Dict[str, str]) -> Any:
        """Execute a matched pattern"""
        if pattern_name in self.combinators:
            return self.combinators[pattern_name](**captures)
        return captures

class VocabularyRegistry:
    """Registry of domain vocabularies"""
    def __init__(self):
        self.vocabularies: Dict[str, Vocabulary] = {}
    
    def create(self, domain: str) -> Vocabulary:
        """Create a new domain vocabulary"""
        vocab = Vocabulary(domain=domain)
        self.vocabularies[domain] = vocab
        return vocab
    
    def get(self, domain: str) -> Vocabulary:
        """Retrieve a vocabulary by domain"""
        return self.vocabularies.get(domain)
    
    def solve_in_vocabulary(self, domain: str, expression: str) -> Any:
        """Solve a problem expressed in a domain's vocabulary"""
        vocab = self.get(domain)
        if not vocab:
            raise ValueError(f"No vocabulary defined for domain '{domain}'")
        return vocab.compile(expression)

# Global registry
VOCABULARIES = VocabularyRegistry()