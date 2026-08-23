#!/usr/bin/env python3
"""
HOPPER Module: Domain Vocabulary Extractor
Builds problem-specific languages by mining memory patterns for semantic primitives.
"""

import re
from collections import Counter, defaultdict
from typing import Dict, List, Set, Tuple

class VocabularyCompiler:
    def __init__(self):
        self.primitives: Dict[str, Dict] = {}
        self.pattern_freq = Counter()
        self.semantic_clusters = defaultdict(set)
        
    def extract_technical_atoms(self, memory_stream: List[str]) -> Dict[str, Set[str]]:
        """Extract domain-specific semantic atoms from memory patterns."""
        atoms = defaultdict(set)
        
        for mem in memory_stream:
            # Extract technical compound terms
            compounds = re.findall(r'([a-z]+(?:-[a-z]+){1,3})', mem.lower())
            for comp in compounds:
                parts = comp.split('-')
                domain = parts[-1] if len(parts) > 1 else 'general'
                atoms[domain].add(comp)
                self.pattern_freq[comp] += 1
        
        return atoms
    
    def build_vocabulary(self, atoms: Dict[str, Set[str]], threshold: int = 2) -> Dict:
        """Compile frequently-occurring patterns into vocabulary primitives."""
        vocab = {}
        
        for domain, terms in atoms.items():
            frequent = {t for t in terms if self.pattern_freq[t] >= threshold}
            if frequent:
                vocab[domain] = {
                    'primitives': sorted(frequent),
                    'cardinality': len(frequent),
                    'composition_depth': max(len(t.split('-')) for t in frequent)
                }
        
        return vocab
    
    def synthesize_dsl_sketch(self, vocab: Dict) -> str:
        """Generate a domain-specific language sketch from vocabulary."""
        dsl = "# AUTO-COMPILED DOMAIN VOCABULARY\n\n"
        
        for domain, spec in sorted(vocab.items()):
            dsl += f"DOMAIN {domain.upper()}:\n"
            for prim in spec['primitives'][:5]:  # Top 5 per domain
                freq = self.pattern_freq[prim]
                dsl += f"  {prim.replace('-', '_')}  # freq={freq}\n"
            dsl += "\n"
        
        return dsl
    
    def compile(self, memories: List[str]) -> Tuple[Dict, str]:
        """Full compilation: memories -> vocabulary -> DSL sketch."""
        atoms = self.extract_technical_atoms(memories)
        vocab = self.build_vocabulary(atoms)
        dsl = self.synthesize_dsl_sketch(vocab)
        return vocab, dsl

if __name__ == '__main__':
    compiler = VocabularyCompiler()
    test_mems = [
        "magnetic field coupling calculator",
        "semantic void bridging perception",
        "phase space inversion chaos",
        "resonance field inversion lattice"
    ]
    vocab, dsl = compiler.compile(test_mems)
    print(dsl)