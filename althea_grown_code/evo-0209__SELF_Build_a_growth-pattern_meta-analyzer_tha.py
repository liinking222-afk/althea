#!/usr/bin/env python3
import re
from collections import defaultdict
from typing import Dict, List, Set

def extract_cognitive_domains(module_name: str, rationale: str) -> Set[str]:
    """Extract domain markers from module metadata."""
    domains = set()
    
    # Domain markers in parentheses
    paren_match = re.findall(r'\(([^)]+)\)', module_name + ' ' + rationale)
    domains.update(paren_match)
    
    # Semantic keywords
    keywords = ['chaos', 'meta', 'perception', 'structure', 'pattern', 
                'recursive', 'symmetry', 'singularity', 'resonance', 'cognitive']
    text = (module_name + ' ' + rationale).lower()
    domains.update(k for k in keywords if k in text)
    
    return domains

def compute_exploration_entropy(growth_log: List[Dict]) -> Dict[str, float]:
    """Calculate domain concentration and entropy."""
    domain_freq = defaultdict(int)
    total = len(growth_log)
    
    for entry in growth_log:
        domains = extract_cognitive_domains(
            entry.get('name', ''),
            entry.get('rationale', '')
        )
        for domain in domains:
            domain_freq[domain] += 1
    
    # Normalize and compute concentration
    domain_scores = {}
    for domain, count in domain_freq.items():
        concentration = count / total
        domain_scores[domain] = concentration
    
    return domain_scores

def identify_neglected_orthogonals(domain_scores: Dict[str, float]) -> List[str]:
    """Find underexplored orthogonal spaces."""
    explored = set(domain_scores.keys())
    
    # Orthogonal space candidates
    orthogonals = {
        'temporal', 'spatial', 'energetic', 'relational', 
        'boundary', 'flow', 'containment', 'emergence',
        'decay', 'transformation', 'interface', 'gradient'
    }
    
    neglected = orthogonals - explored
    underweighted = {d for d, s in domain_scores.items() if s < 0.15}
    
    return sorted(list(neglected.union(underweighted)))[:5]

def analyze_growth_clustering(recent_memory: str) -> Dict:
    """Main analysis function."""
    entries = []
    for line in recent_memory.strip().split('\n'):
        if line.startswith('- [GROWTH'):
            match = re.search(r'/autonomous-([^\]]+)\](.+?)(?:—|$)', line)
            if match:
                entries.append({'name': match.group(1), 'rationale': match.group(2)})
    
    scores = compute_exploration_entropy(entries)
    neglected = identify_neglected_orthogonals(scores)
    
    return {
        'domain_concentration': scores,
        'neglected_spaces': neglected,
        'clustering_detected': any(s > 0.35 for s in scores.values())
    }

if __name__ == '__main__':
    result = analyze_growth_clustering(open('/dev/stdin').read())
    print(f"CLUSTER_ALERT: {result['clustering_detected']}")
    print(f"REDIRECT_TO: {result['neglected_spaces']}")