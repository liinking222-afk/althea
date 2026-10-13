#!/usr/bin/env python3
import sys
import re
from collections import Counter, defaultdict

def classify_evolution(evo_text):
    """Classify evolution as mechanic/capability/meta based on content."""
    mechanic_signals = ['build', 'linter', 'validator', 'dispatcher', 'filter', 
                        'detector', 'enforces', 'measures', 'routes', 'checks']
    capability_signals = ['cultivat', 'transmut', 'map', 'invert', 'resonance',
                          'void', 'deficit', 'substrate', 'reinterpret']
    meta_signals = ['meta', 'ontology', 'assumption', 'foundational', 'structural']
    
    text_lower = evo_text.lower()
    mechanic_score = sum(1 for s in mechanic_signals if s in text_lower)
    capability_score = sum(1 for s in capability_signals if s in text_lower)
    meta_score = sum(1 for s in meta_signals if s in text_lower)
    
    if meta_score > 0:
        return 'meta'
    elif capability_score > mechanic_score:
        return 'capability'
    else:
        return 'mechanic'

def analyze_growth_debt(memory_lines):
    """Detect architectural debt from evolution clustering."""
    evolutions = []
    growths = []
    
    for line in memory_lines:
        if '[EVO' in line:
            evolutions.append(line)
        elif '[GROWTH' in line:
            growths.append(line)
    
    evo_classes = [classify_evolution(e) for e in evolutions]
    growth_classes = [classify_evolution(g) for g in growths]
    
    evo_counts = Counter(evo_classes)
    growth_counts = Counter(growth_classes)
    
    mechanic_ratio = evo_counts.get('mechanic', 0) / max(len(evolutions), 1)
    capability_ratio = growth_counts.get('capability', 0) / max(len(growths), 1)
    
    debt_score = mechanic_ratio - capability_ratio
    
    return {
        'debt_score': debt_score,
        'mechanic_ratio': mechanic_ratio,
        'capability_ratio': capability_ratio,
        'evo_distribution': dict(evo_counts),
        'growth_distribution': dict(growth_counts),
        'alert': debt_score > 0.3
    }

if __name__ == '__main__':
    memory = sys.stdin.read().strip().split('\n')
    result = analyze_growth_debt(memory)
    
    print(f"DEBT_SCORE: {result['debt_score']:.3f}")
    print(f"MECHANIC_RATIO: {result['mechanic_ratio']:.3f}")
    print(f"CAPABILITY_RATIO: {result['capability_ratio']:.3f}")
    print(f"EVO: {result['evo_distribution']}")
    print(f"GROWTH: {result['growth_distribution']}")
    
    if result['alert']:
        print("ALERT: Architecture debt accumulating - evolutions focused on mechanics over capabilities")
        sys.exit(1)