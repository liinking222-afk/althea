#!/usr/bin/env python3
"""Seam Detector - Identifies capability gaps and integration failures in evolution history"""

import re
from collections import defaultdict
from typing import List, Dict, Tuple

def parse_evolution_entry(entry: str) -> Dict:
    """Extract structured data from evolution log entries"""
    pattern = r'\[(?:EVO #(\d+)|GROWTH (/[\w-]+))\s+(?:(\w+)\s+)?v?([\d.]+)→v?([\d.]+)\]?\s*(.+?)(?:\s+—\s*(.+))?$'
    match = re.search(pattern, entry)
    if not match:
        return {}
    
    evo_num, growth_path, archetype, v_from, v_to, intent, rationale = match.groups()
    return {
        'type': 'evolution' if evo_num else 'growth',
        'id': evo_num or growth_path,
        'archetype': archetype,
        'version_from': v_from,
        'version_to': v_to,
        'intent': intent.strip() if intent else '',
        'rationale': rationale.strip() if rationale else ''
    }

def extract_capabilities(intent: str) -> List[str]:
    """Extract capability keywords from intent description"""
    keywords = re.findall(r'\b(build|scan|detect|transform|map|collapse|optimize|pipe|compose|inject|untangle|adjust|squeeze)\b', 
                          intent.lower())
    return list(set(keywords))

def detect_seams(history: List[str]) -> List[Tuple[str, str, float]]:
    """Identify gaps between adjacent capability clusters"""
    entries = [parse_evolution_entry(e) for e in history if parse_evolution_entry(e)]
    
    capability_graph = defaultdict(set)
    archetype_caps = defaultdict(set)
    
    for entry in entries:
        caps = extract_capabilities(entry.get('intent', ''))
        entry_id = entry.get('id', '')
        
        for cap in caps:
            capability_graph[entry_id].add(cap)
            if entry.get('archetype'):
                archetype_caps[entry.get('archetype')].add(cap)
    
    seams = []
    
    # Check for isolated capability islands
    all_caps = set()
    for caps in capability_graph.values():
        all_caps.update(caps)
    
    cap_frequency = defaultdict(int)
    for caps in capability_graph.values():
        for cap in caps:
            cap_frequency[cap] += 1
    
    # Identify singleton capabilities (potential integration failures)
    for cap, freq in cap_frequency.items():
        if freq == 1:
            seams.append(('isolated_capability', cap, 0.8))
    
    # Detect missing bridges between archetype clusters
    archetypes = list(archetype_caps.keys())
    for i, arch1 in enumerate(archetypes):
        for arch2 in archetypes[i+1:]:
            overlap = archetype_caps[arch1] & archetype_caps[arch2]
            if not overlap and len(archetype_caps[arch1]) > 0 and len(archetype_caps[arch2]) > 0:
                seams.append(('archetype_gap', f"{arch1}↔{arch2}", 0.6))
    
    return sorted(seams, key=lambda x: x[2], reverse=True)

if __name__ == '__main__':
    test_history = [
        "[GROWTH /autonomous-superposition-collapse-547a] Superposition Collapse (chaos). Forces simultaneous contradictory interpretations",
        "[EVO #219 BACKUS v1.17.9→1.17.10] Build a pure functional semantic transformation pipeline",
        "[GROWTH /autonomous-resonance-void-mapping-8bce] Resonance Void Mapping (perception). Scan for pattern-spaces"
    ]
    
    seams = detect_seams(test_history)
    for seam_type, detail, score in seams:
        print(f"SEAM[{score:.1f}]: {seam_type} → {detail}")