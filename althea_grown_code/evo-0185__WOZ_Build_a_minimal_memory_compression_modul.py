#!/usr/bin/env python3
import re
import json
from pathlib import Path
from collections import defaultdict

def compress_memory_entry(text: str) -> dict:
    """Extract structural skeleton from verbose memory text."""
    patterns = {
        'perception': r'\(perception\)',
        'lattice': r'\(lattice\)',
        'action': r'\(action\)',
        'systematic': r'[Ss]ystemati(c|cally)',
        'invert': r'[Ii]nvert|[Ii]nversion',
        'dissolve': r'[Dd]issolve|[Dd]issolution',
        'shift': r'[Ss]hift|[Mm]igrat(e|ion)',
        'detect': r'[Dd]etect|[Dd]iscov(er|ery)',
        'transform': r'[Tt]ransform|[Cc]onvert',
    }
    
    signature = []
    for key, pattern in patterns.items():
        if re.search(pattern, text):
            signature.append(key)
    
    # Extract concept words (capitalized or hyphenated technical terms)
    concepts = re.findall(r'[A-Z][a-z]+(?:\s+[A-Z][a-z]+)*|[a-z]+-[a-z]+(?:-[a-z]+)*', text)
    concepts = [c.lower() for c in concepts[:5]]  # Top 5 only
    
    return {
        'sig': '|'.join(signature),
        'concepts': concepts,
        'len': len(text),
        'density': len(signature) / max(len(text), 1) * 1000
    }

def build_pattern_index(memories: list) -> dict:
    """Create compressed searchable index."""
    index = defaultdict(list)
    
    for i, mem in enumerate(memories):
        compressed = compress_memory_entry(mem)
        sig_parts = compressed['sig'].split('|')
        
        for part in sig_parts:
            if part:
                index[part].append((i, compressed['density']))
        
        for concept in compressed['concepts']:
            index[f"c:{concept}"].append((i, compressed['density']))
    
    # Sort by density (most concentrated patterns first)
    for key in index:
        index[key].sort(key=lambda x: x[1], reverse=True)
    
    return dict(index)

def query_compressed(index: dict, query: str) -> list:
    """Return memory indices matching query pattern."""
    tokens = query.lower().split()
    matches = set()
    
    for token in tokens:
        if token in index:
            matches.update(i for i, _ in index[token][:10])
        if f"c:{token}" in index:
            matches.update(i for i, _ in index[f"c:{token}"][:10])
    
    return sorted(matches)

if __name__ == "__main__":
    # Self-test with sample memories
    test_mems = [
        "Salience Inversion Protocol (perception). Systematically inverts attentional hierarchies",
        "Semantic Field Inversion (perception). Systematically invert the semantic polarity",
        "Runtime message dispatcher that allows hot-swap behavior handlers",
    ]
    
    idx = build_pattern_index(test_mems)
    print(json.dumps(query_compressed(idx, "invert perception"), indent=2))