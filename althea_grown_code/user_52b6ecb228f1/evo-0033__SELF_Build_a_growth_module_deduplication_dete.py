#!/usr/bin/env python3
"""
Growth Module Deduplication Detector
Analyzes autonomous growth modules for semantic overlap and redundancy.
"""

import re
from collections import defaultdict
from typing import Dict, List, Tuple, Set


def extract_growth_modules(memory: str) -> List[Dict[str, str]]:
    """Extract growth module entries from memory."""
    pattern = r'\[GROWTH (/[^\]]+)\] ([^(]+)\(([^)]+)\)\. ([^—]+)'
    matches = re.findall(pattern, memory)
    return [
        {
            'path': m[0],
            'name': m[1].strip(),
            'category': m[2].strip(),
            'description': m[3].strip()
        }
        for m in matches
    ]


def tokenize(text: str) -> Set[str]:
    """Extract semantic tokens from text."""
    tokens = re.findall(r'\b\w+\b', text.lower())
    return set(t for t in tokens if len(t) > 3)


def compute_overlap(mod1: Dict, mod2: Dict) -> float:
    """Compute semantic overlap between two modules."""
    tokens1 = tokenize(f"{mod1['name']} {mod1['description']}")
    tokens2 = tokenize(f"{mod2['name']} {mod2['description']}")
    
    if not tokens1 or not tokens2:
        return 0.0
    
    intersection = len(tokens1 & tokens2)
    union = len(tokens1 | tokens2)
    
    return intersection / union if union > 0 else 0.0


def detect_redundancy(modules: List[Dict], threshold: float = 0.4) -> List[Tuple]:
    """Identify redundant module pairs above threshold."""
    redundancies = []
    
    for i in range(len(modules)):
        for j in range(i + 1, len(modules)):
            overlap = compute_overlap(modules[i], modules[j])
            if overlap >= threshold:
                redundancies.append((
                    modules[i]['path'],
                    modules[j]['path'],
                    overlap,
                    modules[i]['category'],
                    modules[j]['category']
                ))
    
    return sorted(redundancies, key=lambda x: x[2], reverse=True)


def analyze_memory(memory: str) -> Dict:
    """Main analysis function."""
    modules = extract_growth_modules(memory)
    redundancies = detect_redundancy(modules)
    
    category_clusters = defaultdict(list)
    for mod in modules:
        category_clusters[mod['category']].append(mod['path'])
    
    return {
        'total_modules': len(modules),
        'redundant_pairs': redundancies,
        'category_distribution': dict(category_clusters),
        'fragmentation_risk': len(redundancies) / max(len(modules), 1)
    }


if __name__ == '__main__':
    print("Growth deduplication detector initialized.")