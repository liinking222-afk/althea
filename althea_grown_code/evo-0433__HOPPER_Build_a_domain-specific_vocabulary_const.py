#!/usr/bin/env python3
"""vocabulary_forge.py - Extract domain primitives and generate DSL foundations"""

import re
from collections import Counter
from typing import Dict, List, Set, Tuple

def extract_primitives(memories: List[str]) -> Dict[str, List[str]]:
    """Extract recurring structural patterns as primitive vocabulary"""
    patterns = {
        'structures': r'\b(lattice|spiral|matrix|graph|tree|mesh|grid|array)\b',
        'transforms': r'\b(invert|reweave|reconstruct|render|compute|validate|flow)\b',
        'domains': r'\b(gradient|fractal|trace|ancestry|quantum|photovoltaic|magnetic)\b',
        'relations': r'\b(coupling|adjacent|embedded|recursive|causal|alternative)\b'
    }
    
    vocab = {category: [] for category in patterns}
    for memory in memories:
        for category, pattern in patterns.items():
            vocab[category].extend(re.findall(pattern, memory.lower()))
    
    return {cat: list(set(terms)) for cat, terms in vocab.items()}

def generate_type_system(vocab: Dict[str, List[str]]) -> str:
    """Generate type definitions from extracted vocabulary"""
    code = ["from typing import Protocol, TypeVar, Generic\n"]
    code.append("# Domain-specific type system\n")
    
    for category, terms in vocab.items():
        if terms:
            code.append(f"class {category.title()}Protocol(Protocol):")
            code.append(f"    \"\"\"Base protocol for {category} operations\"\"\"")
            code.append(f"    def compose(self, other: '{category.title()}Protocol') -> '{category.title()}Protocol': ...")
            code.append("")
    
    return "\n".join(code)

def generate_operators(vocab: Dict[str, List[str]]) -> str:
    """Generate composable operators from vocabulary"""
    ops = ["# Composable operators\n"]
    
    if vocab.get('transforms'):
        for transform in vocab['transforms'][:3]:
            ops.append(f"def {transform}_op(domain, *args):")
            ops.append(f"    \"\"\"Apply {transform} transformation to domain\"\"\"")
            ops.append(f"    return lambda x: domain.{transform}(x, *args)")
            ops.append("")
    
    return "\n".join(ops)

def forge_vocabulary(memories: List[str]) -> str:
    """Main: extract vocabulary and generate DSL foundation"""
    vocab = extract_primitives(memories)
    return generate_type_system(vocab) + "\n" + generate_operators(vocab)

if __name__ == "__main__":
    sample = [
        "Trace Ancestry Reweaving (memory). Reconstruct alternative causal lineages",
        "Fractal Render (generative-art). Compute and render a fractal region",
        "Gradient Inversion Lattice (lattice). Constructs a lattice structure"
    ]
    print(forge_vocabulary(sample))