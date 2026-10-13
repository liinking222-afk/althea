import re
from collections import Counter
from typing import Dict, List, Callable, Set

class VocabularyCompiler:
    """Hopper-style: define the language of the problem domain first."""
    
    def __init__(self):
        self.primitives: Dict[str, Callable] = {}
        self.frequency: Counter = Counter()
        self.compiled_patterns: Dict[str, str] = {}
    
    def extract_primitives(self, memory_stream: List[str]) -> Set[str]:
        """Extract conceptual atoms from memory traces."""
        atoms = set()
        for memory in memory_stream:
            tokens = re.findall(r'\b[a-z]+(?:-[a-z]+)*\b', memory.lower())
            bigrams = [f"{tokens[i]}_{tokens[i+1]}" for i in range(len(tokens)-1)]
            atoms.update(bigrams)
            self.frequency.update(bigrams)
        return {atom for atom, count in self.frequency.items() if count >= 2}
    
    def compile_predicate(self, primitive: str) -> Callable:
        """Generate executable predicate from primitive."""
        parts = primitive.split('_')
        def predicate(text: str) -> bool:
            text_lower = text.lower()
            if all(part in text_lower for part in parts):
                positions = [text_lower.find(part) for part in parts]
                return positions == sorted(positions)
            return False
        return predicate
    
    def build_vocabulary(self, memories: List[str]) -> Dict[str, Callable]:
        """Construct domain language from observed patterns."""
        primitives = self.extract_primitives(memories)
        for prim in primitives:
            self.primitives[prim] = self.compile_predicate(prim)
            self.compiled_patterns[prim] = f"λ(text): '{prim}' in order"
        return self.primitives
    
    def query(self, text: str, primitive: str) -> bool:
        """Execute compiled predicate."""
        if primitive in self.primitives:
            return self.primitives[primitive](text)
        return False
    
    def express_in_vocabulary(self, text: str) -> List[str]:
        """Translate raw text into domain vocabulary."""
        return [prim for prim, pred in self.primitives.items() if pred(text)]
    
    def vocabulary_size(self) -> int:
        return len(self.primitives)
    
    def get_vocabulary(self) -> List[str]:
        return sorted(self.primitives.keys(), key=lambda x: self.frequency[x], reverse=True)

def compile_memory_language(memory_traces: List[str]) -> VocabularyCompiler:
    """Hopper's principle: build the compiler, then write in the new language."""
    compiler = VocabularyCompiler()
    compiler.build_vocabulary(memory_traces)
    return compiler