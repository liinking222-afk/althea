#!/usr/bin/env python3
"""Meta-Evolution Analyzer: Detects redundancy in growth trajectory"""

import re
from collections import defaultdict
from typing import List, Dict, Tuple

def extract_growth_modules(memory: str) -> List[Dict[str, str]]:
    """Extract growth modules from memory stream"""
    pattern = r'\[GROWTH /autonomous-([^\]]+)\] ([^(]+)\(([^)]+)\)\. ([^—]+)'
    modules = []
    for match in re.finditer(pattern, memory):
        modules.append({
            'name': match.group(1),
            'title': match.group(2).strip(),
            'category': match.group(3),
            'description': match.group(4).strip()
        })
    return modules

def tokenize_semantic(text: str) -> set:
    """Extract semantic tokens from text"""
    words = re.findall(r'\b[a-z]{4,}\b', text.lower())
    return set(words) - {'this', 'that', 'with', 'from', 'into', 'through'}

def compute_overlap_matrix(modules: List[Dict]) -> Dict[Tuple[str, str], float]:
    """Compute semantic overlap between all module pairs"""
    overlap = {}
    for i, m1 in enumerate(modules):
        tokens1 = tokenize_semantic(m1['description'])
        for j, m2 in enumerate(modules[i+1:], i+1):
            tokens2 = tokenize_semantic(m2['description'])
            if tokens1 and tokens2:
                jaccard = len(tokens1 & tokens2) / len(tokens1 | tokens2)
                if jaccard > 0.15:  # Threshold for meaningful overlap
                    overlap[(m1['name'], m2['name'])] = jaccard
    return overlap

def detect_redundancy_clusters(modules: List[Dict], overlaps: Dict) -> List[List[str]]:
    """Find clusters of modules with high mutual overlap"""
    graph = defaultdict(set)
    for (m1, m2), score in overlaps.items():
        graph[m1].add(m2)
        graph[m2].add(m1)
    
    visited = set()
    clusters = []
    
    for node in graph:
        if node not in visited:
            cluster = {node}
            stack = [node]
            while stack:
                current = stack.pop()
                visited.add(current)
                for neighbor in graph[current]:
                    if neighbor not in visited:
                        cluster.add(neighbor)
                        stack.append(neighbor)
            if len(cluster) > 1:
                clusters.append(sorted(cluster))
    
    return clusters

def analyze_evolution_redundancy(memory: str) -> Dict:
    """Main analysis pipeline"""
    modules = extract_growth_modules(memory)
    overlaps = compute_overlap_matrix(modules)
    clusters = detect_redundancy_clusters(modules, overlaps)
    
    return {
        'total_modules': len(modules),
        'overlap_count': len(overlaps),
        'redundancy_clusters': clusters,
        'consolidation_opportunities': len(clusters)
    }

if __name__ == '__main__':
    import sys
    memory = sys.stdin.read() if not sys.stdin.isatty() else ""
    result = analyze_evolution_redundancy(memory)
    print(f"Redundancy Analysis: {result}")