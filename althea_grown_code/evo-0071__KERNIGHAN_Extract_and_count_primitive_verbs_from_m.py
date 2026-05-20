#!/usr/bin/env python3
import re
from collections import Counter
from typing import List, Dict

def extract_verbs(text: str) -> List[str]:
    """Extract action verbs from text - one thing only."""
    words = re.findall(r'\b[a-z]+\b', text.lower())
    verbs = [
        'build', 'extract', 'define', 'generate', 'prove', 'check',
        'validate', 'reconstruct', 'interpolate', 'process', 'decay',
        'bind', 'influence', 'detect', 'excavate', 'erode', 'express',
        'maintain', 'wipe', 'update', 'reveal', 'compose', 'parse'
    ]
    return [w for w in words if w in verbs]

def count_primitives(memories: List[str]) -> Dict[str, int]:
    """Count verb frequency across all memories."""
    all_verbs = []
    for memory in memories:
        all_verbs.extend(extract_verbs(memory))
    return dict(Counter(all_verbs).most_common())

def format_vocabulary(counts: Dict[str, int]) -> str:
    """Format as pipe-delimited output."""
    lines = [f"{verb}|{count}" for verb, count in counts.items()]
    return '\n'.join(lines)

def main():
    memories = [
        "Build a loop invariant validator that proves memory operations",
        "Extract recurring semantic primitives from memory and growth patterns",
        "Reconstruct latent processing states from minimal output artifacts",
        "Bind disparate response threads into non-local correlation patterns",
        "Excavate layered traces of previous coherence regimes to detect",
        "Define a domain-specific vocabulary builder that extracts and generates"
    ]
    
    counts = count_primitives(memories)
    print(format_vocabulary(counts))

if __name__ == '__main__':
    main()