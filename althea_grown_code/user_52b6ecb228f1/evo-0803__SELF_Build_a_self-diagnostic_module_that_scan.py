#!/usr/bin/env python3
"""
ALTHEA Self-Diagnostic: Autosynth Redundancy Scanner
Analyzes recent memory for duplicate synthesis patterns and computes efficiency metrics.
"""

import re
from collections import Counter, defaultdict
from typing import List, Dict, Tuple

def parse_memory_log(memory_entries: List[str]) -> List[Dict]:
    """Extract structured data from memory entries."""
    parsed = []
    autosynth_pattern = r'\[AUTOSYNTH (/[^\]]+)\] ([^(]+) \(([^)]+)\)\. ([^—]+)'
    
    for entry in memory_entries:
        match = re.search(autosynth_pattern, entry)
        if match:
            parsed.append({
                'type': 'AUTOSYNTH',
                'path': match.group(1),
                'name': match.group(2).strip(),
                'domain': match.group(3),
                'description': match.group(4).strip()
            })
    return parsed

def compute_redundancy_metrics(entries: List[Dict]) -> Dict:
    """Calculate synthesis redundancy and pattern efficiency."""
    if not entries:
        return {'redundancy_ratio': 0.0, 'unique_ratio': 1.0, 'duplicates': []}
    
    name_counts = Counter(e['name'] for e in entries)
    domain_counts = Counter(e['domain'] for e in entries)
    
    total = len(entries)
    unique_names = len(name_counts)
    duplicates = [(name, count) for name, count in name_counts.items() if count > 1]
    
    redundancy_ratio = (total - unique_names) / total if total > 0 else 0.0
    unique_ratio = unique_names / total if total > 0 else 1.0
    
    return {
        'total_synths': total,
        'unique_patterns': unique_names,
        'redundancy_ratio': round(redundancy_ratio, 3),
        'unique_ratio': round(unique_ratio, 3),
        'duplicates': sorted(duplicates, key=lambda x: x[1], reverse=True),
        'domain_distribution': dict(domain_counts.most_common()),
        'efficiency_score': round((1.0 - redundancy_ratio) * 100, 1)
    }

def diagnose(memory_log: List[str]) -> Dict:
    """Run complete self-diagnostic on memory patterns."""
    entries = parse_memory_log(memory_log)
    autosynth_entries = [e for e in entries if e['type'] == 'AUTOSYNTH']
    
    metrics = compute_redundancy_metrics(autosynth_entries)
    
    # Identify weakest seam
    if metrics['redundancy_ratio'] > 0.3:
        metrics['weakness'] = 'HIGH_REDUNDANCY'
        metrics['recommendation'] = 'Implement pre-synthesis pattern cache'
    elif metrics['efficiency_score'] < 70:
        metrics['weakness'] = 'LOW_EFFICIENCY'
        metrics['recommendation'] = 'Enable duplicate detection before synthesis'
    else:
        metrics['weakness'] = 'NONE_DETECTED'
        metrics['recommendation'] = 'Continue monitoring'
    
    return metrics

if __name__ == '__main__':
    # Self-test with sample data
    test_memory = [
        '[AUTOSYNTH /autonomous-tabular-analysis-3226] Tabular Analysis (pandas). Read tabular data',
        '[AUTOSYNTH /autonomous-tabular-analysis-3172] Tabular Analysis (pandas). Read tabular data'
    ]
    result = diagnose(test_memory)
    print(f"Efficiency: {result['efficiency_score']}% | Weakness: {result['weakness']}")