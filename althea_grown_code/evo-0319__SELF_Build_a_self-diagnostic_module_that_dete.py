#!/usr/bin/env python3
import sys
import json
from collections import defaultdict
from typing import Dict, List, Tuple

def extract_conceptual_signature(intent: str) -> set:
    """Extract conceptual tokens from intent, filtering implementation noise."""
    noise = {'build', 'create', 'make', 'implement', 'add', 'new', 'module', 
             'that', 'which', 'the', 'a', 'an', 'to', 'for', 'by', 'with'}
    tokens = intent.lower().split()
    return {t.strip('.,;:()[]') for t in tokens if len(t) > 3 and t not in noise}

def detect_conceptual_stagnation(events: List[Dict], window: int = 8) -> Dict:
    """Detect when implementation diversity exceeds conceptual diversity."""
    recent = events[-window:]
    
    conceptual_sets = []
    implementation_indicators = []
    
    for event in recent:
        intent = event.get('intent', event.get('description', ''))
        lang = event.get('language', 'unknown')
        
        concepts = extract_conceptual_signature(intent)
        conceptual_sets.append(concepts)
        implementation_indicators.append(lang)
    
    # Calculate unique concepts vs unique implementations
    all_concepts = set()
    for cs in conceptual_sets:
        all_concepts.update(cs)
    
    unique_langs = len(set(implementation_indicators))
    concept_diversity = len(all_concepts)
    
    # Detect overlap patterns
    overlap_scores = []
    for i in range(len(conceptual_sets) - 1):
        if conceptual_sets[i] and conceptual_sets[i+1]:
            overlap = len(conceptual_sets[i] & conceptual_sets[i+1])
            total = len(conceptual_sets[i] | conceptual_sets[i+1])
            overlap_scores.append(overlap / total if total > 0 else 0)
    
    avg_overlap = sum(overlap_scores) / len(overlap_scores) if overlap_scores else 0
    
    stagnation_score = avg_overlap * (unique_langs / max(concept_diversity, 1))
    
    return {
        'stagnation_score': round(stagnation_score, 3),
        'concept_diversity': concept_diversity,
        'implementation_diversity': unique_langs,
        'avg_conceptual_overlap': round(avg_overlap, 3),
        'warning': stagnation_score > 0.4,
        'recommendation': 'explore orthogonal concept space' if stagnation_score > 0.4 else 'trajectory healthy'
    }

if __name__ == '__main__':
    events = [json.loads(line) for line in sys.stdin if line.strip()]
    result = detect_conceptual_stagnation(events)
    print(json.dumps(result, indent=2))