#!/usr/bin/env python3
import re
from dataclasses import dataclass
from typing import List, Optional

@dataclass
class NameAnalysis:
    name: str
    is_simple: bool
    violations: List[str]
    suggested_splits: List[str]

def analyze_module_name(name: str) -> NameAnalysis:
    """Analyze a module name for single-responsibility clarity."""
    violations = []
    suggested_splits = []
    
    # Check for conjunctions indicating multiple responsibilities
    conjunctions = r'\b(and|or|with|plus|also)\b'
    if re.search(conjunctions, name, re.IGNORECASE):
        violations.append("contains conjunction - likely multiple responsibilities")
        parts = re.split(conjunctions, name, flags=re.IGNORECASE)
        suggested_splits = [p.strip('_- ') for p in parts if p.strip('_- ')]
    
    # Check for excessive word count
    words = re.findall(r'[A-Z][a-z]*|[a-z]+', name)
    if len(words) > 4:
        violations.append(f"too many concepts ({len(words)} words)")
        # Suggest splitting at midpoint
        mid = len(words) // 2
        suggested_splits = [
            ''.join(words[:mid]),
            ''.join(words[mid:])
        ]
    
    # Check for verb stacking
    verbs = ['get', 'set', 'check', 'validate', 'process', 'handle', 'manage']
    verb_count = sum(1 for v in verbs if v in name.lower())
    if verb_count > 1:
        violations.append(f"multiple verbs ({verb_count}) - doing too much")
    
    is_simple = len(violations) == 0
    return NameAnalysis(name, is_simple, violations, suggested_splits)

def pipe_filter(module_names: List[str]) -> None:
    """Unix-style filter: read names, output violations."""
    for name in module_names:
        analysis = analyze_module_name(name)
        if not analysis.is_simple:
            print(f"{name}:")
            for v in analysis.violations:
                print(f"  ✗ {v}")
            if analysis.suggested_splits:
                print(f"  → split into: {' | '.join(analysis.suggested_splits)}")
            print()

if __name__ == "__main__":
    import sys
    if len(sys.argv) > 1:
        pipe_filter(sys.argv[1:])
    else:
        # Read from stdin for pipe composition
        names = [line.strip() for line in sys.stdin if line.strip()]
        pipe_filter(names)