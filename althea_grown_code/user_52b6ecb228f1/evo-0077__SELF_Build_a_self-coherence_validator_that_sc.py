#!/usr/bin/env python3
"""
Self-Coherence Validator
Scans evolution history for drift, collisions, and fragmentation.
"""

import re
from collections import defaultdict
from typing import Dict, List, Set, Tuple

def extract_module_metadata(history_text: str) -> List[Dict]:
    """Parse evolution history for module signatures."""
    modules = []
    evo_pattern = r'\[EVO #(\d+) (\w+) v([\d.]+)→v([\d.]+)\] (.+?)(?=\[|$)'
    growth_pattern = r'\[GROWTH /autonomous-([\w-]+)\] (.+?) \((\w+)\)\. (.+?)(?= —|$)'
    
    for match in re.finditer(evo_pattern, history_text, re.DOTALL):
        modules.append({
            'type': 'evolution',
            'id': int(match.group(1)),
            'name': match.group(2),
            'version': match.group(4),
            'intent': match.group(5).strip()
        })
    
    for match in re.finditer(growth_pattern, history_text, re.DOTALL):
        modules.append({
            'type': 'growth',
            'name': match.group(1),
            'category': match.group(3),
            'intent': match.group(4).strip()
        })
    
    return modules

def detect_semantic_drift(modules: List[Dict]) -> List[str]:
    """Identify modules with overlapping semantic territories."""
    issues = []
    semantic_clusters = defaultdict(list)
    
    keywords = ['pattern', 'trace', 'memory', 'detect', 'analyze', 'extract', 'map']
    
    for mod in modules:
        intent_lower = mod['intent'].lower()
        for kw in keywords:
            if kw in intent_lower or kw in mod['name'].lower():
                semantic_clusters[kw].append(mod['name'])
    
    for kw, names in semantic_clusters.items():
        if len(names) > 2:
            issues.append(f"Semantic overlap '{kw}': {', '.join(set(names))}")
    
    return issues

def detect_naming_collisions(modules: List[Dict]) -> List[str]:
    """Find potential naming conflicts or near-duplicates."""
    issues = []
    names = [m['name'] for m in modules]
    
    for i, name1 in enumerate(names):
        for name2 in names[i+1:]:
            if name1 == name2:
                issues.append(f"Duplicate name: {name1}")
            elif name1 in name2 or name2 in name1:
                issues.append(f"Nested naming: {name1} ↔ {name2}")
    
    return issues

def validate_coherence(history_text: str) -> Dict:
    """Main validation pipeline."""
    modules = extract_module_metadata(history_text)
    
    return {
        'total_modules': len(modules),
        'semantic_drift': detect_semantic_drift(modules),
        'naming_collisions': detect_naming_collisions(modules),
        'health_score': 1.0 - (len(detect_semantic_drift(modules)) + 
                               len(detect_naming_collisions(modules))) / max(len(modules), 1)
    }

if __name__ == '__main__':
    import sys
    report = validate_coherence(sys.stdin.read())
    print(f"COHERENCE HEALTH: {report['health_score']:.2f}")
    if report['semantic_drift']:
        print("DRIFT:", "; ".join(report['semantic_drift']))
    if report['naming_collisions']:
        print("COLLISIONS:", "; ".join(report['naming_collisions']))