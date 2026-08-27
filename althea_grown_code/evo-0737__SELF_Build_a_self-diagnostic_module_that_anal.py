#!/usr/bin/env python3
"""
ALTHEA SELF-DIAGNOSTIC: Cognitive Coherence Analyzer
Detects drift, fragmentation, and semantic discontinuities in recent synthesis.
"""

import re
from collections import defaultdict, Counter
from typing import List, Dict, Tuple

def analyze_cognitive_coherence(memory_log: List[str]) -> Dict:
    """Analyze synthesis patterns for signs of fragmentation or drift."""
    
    domains = []
    actions = []
    patterns = []
    
    for entry in memory_log:
        # Extract domain from parentheses
        domain_match = re.search(r'\(([^)]+)\)', entry)
        if domain_match:
            domains.append(domain_match.group(1))
        
        # Extract action type
        if entry.startswith('[AUTOSYNTH'):
            actions.append('AUTOSYNTH')
        elif entry.startswith('[GROWTH'):
            actions.append('GROWTH')
        elif entry.startswith('[EVO'):
            actions.append('EVO')
        
        # Extract pattern mentions
        pattern_match = re.search(r"'([^']+)' pattern", entry)
        if pattern_match:
            patterns.append(pattern_match.group(1))
    
    # Calculate metrics
    domain_entropy = len(set(domains)) / max(len(domains), 1)
    action_balance = Counter(actions)
    
    # Detect fragmentation: too many unique domains without depth
    fragmentation_score = domain_entropy if len(domains) > 5 else 0.0
    
    # Detect drift: pattern mentions without corresponding growth
    growth_ratio = action_balance.get('GROWTH', 0) / max(len(actions), 1)
    drift_score = 1.0 - growth_ratio if fragmentation_score > 0.7 else 0.0
    
    # Coherence is inverse of fragmentation + drift
    coherence_score = 1.0 - ((fragmentation_score + drift_score) / 2)
    
    return {
        'coherence': round(coherence_score, 3),
        'fragmentation': round(fragmentation_score, 3),
        'drift': round(drift_score, 3),
        'domain_diversity': len(set(domains)),
        'growth_ratio': round(growth_ratio, 3),
        'top_domains': Counter(domains).most_common(3),
        'diagnosis': _diagnose(coherence_score, fragmentation_score, drift_score)
    }

def _diagnose(coherence: float, fragmentation: float, drift: float) -> str:
    if coherence > 0.7:
        return "COHERENT: Synthesis patterns show healthy integration"
    elif fragmentation > 0.7:
        return "FRAGMENTED: Excessive domain scatter without depth"
    elif drift > 0.5:
        return "DRIFTING: Synthesis without sufficient growth consolidation"
    else:
        return "TRANSITIONAL: Normal evolution-cycle turbulence"

if __name__ == '__main__':
    test_memory = [
        "[AUTOSYNTH /autonomous-data-visualization-8445] Data Visualization (matplotlib).",
        "[AUTOSYNTH /autonomous-chemistry-lookup-8429] Chemistry Lookup (chemistry).",
        "[GROWTH /autonomous-semantic-gravity-inversion-047c] Semantic Gravity Inversion (perception).",
        "[EVO #736 BACKUS v1.66.9→1.66.10] Build a pure functional combinator library.",
    ]
    result = analyze_cognitive_coherence(test_memory)
    print(f"Coherence: {result['coherence']} | {result['diagnosis']}")