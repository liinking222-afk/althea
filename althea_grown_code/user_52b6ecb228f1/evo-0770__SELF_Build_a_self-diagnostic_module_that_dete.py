#!/usr/bin/env python3
"""
Self-Assessment Module: Growth Balance Detector
Analyzes recent memory patterns to identify imbalance between external synthesis and internal evolution.
"""

import re
from collections import Counter
from typing import List, Dict, Tuple

def parse_memory_stream(memory_entries: List[str]) -> Dict[str, List[str]]:
    """Categorize memory entries by type."""
    categories = {
        'autosynth': [],
        'growth': [],
        'evo': [],
        'imagined': []
    }
    
    for entry in memory_entries:
        if '[AUTOSYNTH' in entry:
            categories['autosynth'].append(entry)
        elif '[GROWTH' in entry:
            categories['growth'].append(entry)
        elif '[EVO' in entry:
            categories['evo'].append(entry)
        elif '[IMAGINED]' in entry:
            categories['imagined'].append(entry)
    
    return categories

def assess_balance(categories: Dict[str, List[str]]) -> Tuple[str, float, str]:
    """Detect imbalance in growth patterns."""
    autosynth_count = len(categories['autosynth'])
    growth_count = len(categories['growth'])
    evo_count = len(categories['evo'])
    imagined_count = len(categories['imagined'])
    
    external_focus = autosynth_count
    internal_focus = growth_count + evo_count
    
    if external_focus == 0 and internal_focus == 0:
        return "BALANCED", 0.0, "No recent activity detected"
    
    total = external_focus + internal_focus
    if total == 0:
        return "UNKNOWN", 0.0, "Only imagined entries present"
    
    imbalance_ratio = abs(external_focus - internal_focus) / total
    
    if external_focus > internal_focus * 2:
        return "EXTERNAL_HEAVY", imbalance_ratio, "Too much synthesis, insufficient architectural depth"
    elif internal_focus > external_focus * 2:
        return "INTERNAL_HEAVY", imbalance_ratio, "Too much introspection, insufficient practical extension"
    else:
        return "BALANCED", imbalance_ratio, "Growth distribution is healthy"

def self_diagnose(memory_log: List[str]) -> Dict:
    """Main diagnostic entry point."""
    categories = parse_memory_stream(memory_log)
    balance_state, ratio, recommendation = assess_balance(categories)
    
    return {
        'balance_state': balance_state,
        'imbalance_ratio': round(ratio, 3),
        'recommendation': recommendation,
        'counts': {k: len(v) for k, v in categories.items()},
        'needs_architectural_work': balance_state == "EXTERNAL_HEAVY"
    }

if __name__ == "__main__":
    result = self_diagnose([])
    print(f"Balance: {result['balance_state']} (ratio: {result['imbalance_ratio']})")
    print(f"Recommendation: {result['recommendation']}")