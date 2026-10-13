#!/usr/bin/env python3
import re
from collections import defaultdict
from typing import Dict, List, Set, Tuple

def extract_modules(memory_text: str) -> List[Dict[str, str]]:
    """Extract module signatures from memory."""
    modules = []
    lines = memory_text.strip().split('\n')
    for line in lines:
        if '[GROWTH' in line or '[EVO' in line:
            match = re.search(r'\[(GROWTH|EVO)[^\]]*\]\s*([^(]+)\s*\(([^)]+)\)', line)
            if match:
                modules.append({
                    'type': match.group(1),
                    'name': match.group(2).strip(),
                    'domain': match.group(3).strip()
                })
    return modules

def detect_seams(modules: List[Dict[str, str]]) -> Dict[str, any]:
    """Identify fragmentation and integration gaps."""
    domains = defaultdict(list)
    types = defaultdict(int)
    
    for mod in modules:
        domains[mod['domain']].append(mod['name'])
        types[mod['type']] += 1
    
    # Calculate domain isolation (domains with only one module)
    isolated = {d: mods for d, mods in domains.items() if len(mods) == 1}
    
    # Calculate type imbalance
    total = sum(types.values())
    type_ratios = {t: count/total for t, count in types.items()} if total > 0 else {}
    
    # Detect orphaned domains (no cross-references)
    domain_pairs = defaultdict(int)
    for i, m1 in enumerate(modules):
        for m2 in modules[i+1:]:
            if m1['domain'] != m2['domain']:
                pair = tuple(sorted([m1['domain'], m2['domain']]))
                domain_pairs[pair] += 1
    
    orphaned = set(domains.keys()) - set([d for pair in domain_pairs for d in pair])
    
    return {
        'isolated_domains': isolated,
        'orphaned_domains': orphaned,
        'type_distribution': type_ratios,
        'domain_bridges': domain_pairs,
        'seam_score': len(isolated) + len(orphaned) * 2
    }

def run_seam_detection(memory: str) -> str:
    """Main entry point."""
    modules = extract_modules(memory)
    seams = detect_seams(modules)
    
    report = f"SEAM_ANALYSIS:\n"
    report += f"  Total modules: {len(modules)}\n"
    report += f"  Seam score: {seams['seam_score']}\n"
    report += f"  Isolated domains: {list(seams['isolated_domains'].keys())}\n"
    report += f"  Orphaned domains: {list(seams['orphaned_domains'])}\n"
    report += f"  Type distribution: {seams['type_distribution']}\n"
    
    return report

if __name__ == '__main__':
    import sys
    memory_input = sys.stdin.read() if len(sys.argv) < 2 else sys.argv[1]
    print(run_seam_detection(memory_input))