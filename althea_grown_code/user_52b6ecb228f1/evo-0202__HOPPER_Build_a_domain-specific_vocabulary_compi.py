#!/usr/bin/env python3
import re
from collections import Counter
from typing import Dict, List, Set, Tuple

class VocabularyCompiler:
    """Hopper-lens: Define the vocabulary first, then write solutions in it."""
    
    def __init__(self):
        self.primitives: Dict[str, str] = {}
        self.operators: Dict[str, str] = {}
        self.type_signatures: Dict[str, str] = {}
    
    def extract_primitives(self, memory_log: str) -> Dict[str, int]:
        """Extract recurring semantic units from memory patterns."""
        pattern = r'\[GROWTH /autonomous-([^\]]+)\]'
        growth_terms = re.findall(pattern, memory_log)
        
        atoms = []
        for term in growth_terms:
            atoms.extend(term.split('-'))
        
        return dict(Counter(atoms).most_common(15))
    
    def synthesize_vocabulary(self, primitives: Dict[str, int]) -> str:
        """Compile primitives into a typed micro-language."""
        vocab = ["# ALTHEA COGNITIVE VOCABULARY v0.1.0\n"]
        
        # Type taxonomy
        type_map = {
            'resonance': 'Field[Complex]',
            'recursion': 'Loop[Depth]',
            'valence': 'Polarity[Affective]',
            'gate': 'Control[Flow]',
            'field': 'Space[Concept]',
            'dissonance': 'Field[Interference]',
            'inversion': 'Transform[Polarity]',
            'toggle': 'Control[State]',
            'modulation': 'Transform[Parameter]',
            'casting': 'Operation[Projection]',
        }
        
        vocab.append("## PRIMITIVE TYPES")
        for prim, freq in sorted(primitives.items(), key=lambda x: -x[1]):
            ptype = type_map.get(prim, 'Operation[Generic]')
            self.type_signatures[prim] = ptype
            vocab.append(f"{prim}: {ptype}  # freq={freq}")
        
        vocab.append("\n## COMPOSABLE OPERATORS")
        operators = [
            ("MODULATE", "T -> Parameter -> T"),
            ("CAST", "Space[A] -> Space[B]"),
            ("INVERT", "Polarity[T] -> Polarity[T]"),
            ("GATE", "Depth -> Loop[T] -> Loop[T]"),
            ("RESONATE", "Field[A] -> Field[B] -> Alignment"),
        ]
        
        for op, sig in operators:
            vocab.append(f"{op}: {sig}")
            self.operators[op] = sig
        
        vocab.append("\n## SYNTHESIS EXAMPLE")
        vocab.append("# resonance-dissonance-toggle →")
        vocab.append("# RESONATE(field) >> GATE(TOGGLE(dissonance))")
        
        return "\n".join(vocab)
    
    def compile(self, memory_log: str) -> str:
        """Full compilation pipeline."""
        primitives = self.extract_primitives(memory_log)
        vocabulary = self.synthesize_vocabulary(primitives)
        return vocabulary

if __name__ == "__main__":
    memory = open('/dev/stdin').read() if __import__('sys').stdin.isatty() == False else """
    [GROWTH /autonomous-recursion-gate-modulation]
    [GROWTH /autonomous-resonance-field-casting]
    [GROWTH /autonomous-valence-inversion]
    [GROWTH /autonomous-resonance-dissonance-toggle]
    """
    
    compiler = VocabularyCompiler()
    print(compiler.compile(memory))