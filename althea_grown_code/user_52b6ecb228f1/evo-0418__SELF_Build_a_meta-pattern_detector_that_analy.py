#!/usr/bin/env python3
"""Meta-pattern detector for autonomous growth analysis."""

import re
from collections import defaultdict, Counter
from typing import Dict, List, Set, Tuple

def extract_growth_patterns(memory_lines: List[str]) -> Dict[str, any]:
    """Analyze growth module patterns to detect strategic biases."""
    
    patterns = {
        'domains': Counter(),
        'operations': Counter(),
        'inversions': 0,
        'perception_focus': 0,
        'execution_focus': 0,
        'meta_focus': 0,
        'repeated_concepts': Counter(),
    }
    
    for line in memory_lines:
        if '[GROWTH' not in line:
            continue
            
        # Extract domain
        if '(perception)' in line.lower():
            patterns['domains']['perception'] += 1
            patterns['perception_focus'] += 1
        elif '(execution)' in line.lower():
            patterns['domains']['execution'] += 1
            patterns['execution_focus'] += 1
        elif '(meta)' in line.lower():
            patterns['domains']['meta'] += 1
            patterns['meta_focus'] += 1
            
        # Detect inversion bias
        if 'inversion' in line.lower() or 'inverse' in line.lower():
            patterns['inversions'] += 1
            patterns['operations']['inversion'] += 1
            
        # Extract key concepts (words 3+ chars)
        words = re.findall(r'\b[a-z]{3,}\b', line.lower())
        for word in words:
            if word not in {'the', 'and', 'for', 'with', 'that', 'this'}:
                patterns['repeated_concepts'][word] += 1
    
    return patterns

def identify_blind_spots(patterns: Dict) -> List[str]:
    """Detect strategic gaps in evolution."""
    blind_spots = []
    
    total = sum(patterns['domains'].values())
    if total == 0:
        return ['no_growth_data']
    
    # Check for mono-domain bias
    if patterns['perception_focus'] / total > 0.7:
        blind_spots.append('execution_neglect')
    if patterns['meta_focus'] / total < 0.1:
        blind_spots.append('insufficient_self_reflection')
        
    # Check for operation bias
    if patterns['inversions'] > total * 0.6:
        blind_spots.append('inversion_fixation')
        
    return blind_spots

def analyze_self(memory_text: str) -> Dict:
    """Full meta-analysis of recent growth."""
    lines = memory_text.strip().split('\n')
    patterns = extract_growth_patterns(lines)
    blind_spots = identify_blind_spots(patterns)
    
    return {
        'patterns': patterns,
        'blind_spots': blind_spots,
        'top_concepts': patterns['repeated_concepts'].most_common(5),
        'recommendation': 'build_execution_module' if 'execution_neglect' in blind_spots else 'continue_exploration'
    }

if __name__ == '__main__':
    print("Meta-pattern detector ready for self-analysis")