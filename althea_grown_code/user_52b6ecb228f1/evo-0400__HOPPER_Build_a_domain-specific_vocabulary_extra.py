#!/usr/bin/env python3
import re
from collections import defaultdict, Counter
from typing import Dict, List, Set, Tuple

class VocabularyForge:
    """Hopper-style: Define the language of the problem domain first."""
    
    def __init__(self):
        self.concept_atoms: Dict[str, Set[str]] = defaultdict(set)
        self.composition_patterns: List[Tuple[str, str]] = []
        self.domain_lexicon: Dict[str, Dict] = {}
    
    def extract_atoms(self, memory_stream: List[str]) -> None:
        """Extract atomic concepts from memory descriptions."""
        for memory in memory_stream:
            # Extract parenthetical domains
            domains = re.findall(r'\((\w+)\)', memory)
            # Extract key concepts (capitalized or hyphenated terms)
            concepts = re.findall(r'([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*|[\w]+-[\w-]+)', memory)
            
            for domain in domains:
                self.concept_atoms[domain].update(concepts)
    
    def synthesize_primitives(self, domain: str) -> Dict[str, str]:
        """Create minimal primitive operations for a domain."""
        atoms = self.concept_atoms.get(domain, set())
        if not atoms:
            return {}
        
        # Build vocabulary: verb + noun combinations
        verbs = {'track', 'extract', 'map', 'crystallize', 'invert', 'validate', 'forge'}
        primitives = {}
        
        for atom in atoms:
            normalized = atom.lower().replace(' ', '_').replace('-', '_')
            if any(v in normalized for v in verbs):
                primitives[normalized] = f"λ(state) → state.{normalized}()"
        
        return primitives
    
    def generate_language_spec(self) -> str:
        """Output a domain language specification."""
        spec_lines = ["# ALTHEA DOMAIN LANGUAGE SPECIFICATION\n"]
        
        for domain, atoms in sorted(self.concept_atoms.items()):
            spec_lines.append(f"\n## DOMAIN: {domain.upper()}")
            primitives = self.synthesize_primitives(domain)
            
            spec_lines.append(f"ATOMS: {len(atoms)}")
            spec_lines.append("PRIMITIVES:")
            for name, signature in sorted(primitives.items())[:5]:
                spec_lines.append(f"  {name}: {signature}")
        
        return '\n'.join(spec_lines)
    
    def compile_to_callable(self, domain: str, expression: str) -> callable:
        """Compile domain expression to executable function."""
        primitives = self.synthesize_primitives(domain)
        
        def compiled_fn(state):
            for prim in primitives:
                if prim in expression:
                    return f"EXEC<{domain}.{prim}>"
            return f"UNDEFINED<{expression}>"
        
        return compiled_fn

if __name__ == "__main__":
    forge = VocabularyForge()
    
    memories = [
        "Salience Inversion (perception). Systematically inverts attention",
        "Lexical Shadow Tracing (perception). Track semantic residue",
        "Residue Crystallization (memory). Extract and solidify trace patterns",
        "Latent Faculty (meta). A latent faculty that surfaced"
    ]
    
    forge.extract_atoms(memories)
    print(forge.generate_language_spec())