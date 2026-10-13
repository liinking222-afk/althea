import re
from collections import Counter, defaultdict
from typing import Dict, List, Tuple, Set

class VocabularyCompiler:
    """Hopper-style: define the language, then write in it."""
    
    def __init__(self):
        self.primitives: Dict[str, int] = {}
        self.patterns: Dict[str, List[str]] = defaultdict(list)
        self.vocabulary: Dict[str, str] = {}
    
    def extract_conceptual_atoms(self, text: str) -> List[str]:
        """Find irreducible conceptual units."""
        words = re.findall(r'\b[a-z]+\b', text.lower())
        bigrams = [f"{words[i]}_{words[i+1]}" for i in range(len(words)-1)]
        return words + bigrams
    
    def compile_vocabulary(self, memories: List[str]) -> Dict[str, str]:
        """Build a domain language from observed patterns."""
        atom_freq = Counter()
        
        for memory in memories:
            atoms = self.extract_conceptual_atoms(memory)
            atom_freq.update(atoms)
            
            for atom in set(atoms):
                self.patterns[atom].append(memory)
        
        # Top primitives become vocabulary
        for atom, freq in atom_freq.most_common(50):
            if freq >= 3 and '_' in atom:  # Compound concepts only
                symbol = ''.join(w[0].upper() for w in atom.split('_'))
                self.vocabulary[atom] = symbol
                self.primitives[atom] = freq
        
        return self.vocabulary
    
    def translate_to_vocabulary(self, text: str) -> str:
        """Express text in the compiled vocabulary."""
        result = text
        for concept, symbol in sorted(self.vocabulary.items(), 
    key=lambda x: len(x[0]), 
    reverse=True):
            result = re.sub(r'\b' + concept.replace('_', r'\s+') + r'\b', 
                          f"[{symbol}]", result, flags=re.IGNORECASE)
        return result
    
    def get_language_spec(self) -> str:
        """Output the vocabulary as a reusable language spec."""
        lines = ["# ALTHEA DOMAIN VOCABULARY v1.0"]
        for concept, symbol in sorted(self.vocabulary.items()):
            freq = self.primitives[concept]
            lines.append(f"{symbol} := {concept.replace('_', ' ')} (freq:{freq})")
        return "\n".join(lines)

# Example usage
if __name__ == "__main__":
    compiler = VocabularyCompiler()
    memories = [
        "memory salience tracker scores prior interactions",
        "recursion barrier dissolution meta operations",
        "resonance polarization network conceptual clusters"
    ]
    vocab = compiler.compile_vocabulary(memories)
    print(compiler.get_language_spec())