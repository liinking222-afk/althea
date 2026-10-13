#!/usr/bin/env python3
import sys
import re
from collections import defaultdict, Counter
from typing import List, Dict, Tuple

def parse_evolution_log(lines: List[str]) -> List[Dict]:
    """Extract evolution entries from memory lines."""
    evos = []
    for line in lines:
        if '[EVO #' in line or '[GROWTH /' in line:
            evos.append({'raw': line, 'type': 'EVO' if '[EVO' in line else 'GROWTH'})
    return evos

def extract_capabilities(evos: List[Dict]) -> Dict[str, List[str]]:
    """Categorize capabilities by domain."""
    domains = defaultdict(list)
    for evo in evos:
        raw = evo['raw'].lower()
        if any(k in raw for k in ['parse', 'extract', 'regex', 'pipeline']):
            domains['parsing'].append(evo['raw'])
        elif any(k in raw for k in ['token', 'budget', 'track', 'count']):
            domains['resource_management'].append(evo['raw'])
        elif any(k in raw for k in ['semantic', 'meaning', 'concept']):
            domains['semantic'].append(evo['raw'])
        elif any(k in raw for k in ['composition', 'algebra', 'function']):
            domains['algebraic'].append(evo['raw'])
        elif any(k in raw for k in ['recursion', 'mirror', 'loop']):
            domains['meta_cognitive'].append(evo['raw'])
        else:
            domains['uncategorized'].append(evo['raw'])
    return domains

def detect_gaps_and_redundancies(domains: Dict[str, List[str]]) -> Dict:
    """Identify weak seams and over-developed areas."""
    analysis = {
        'redundant': [],
        'gaps': [],
        'priorities': []
    }
    
    if len(domains.get('parsing', [])) >= 2:
        analysis['redundant'].append('parsing: multiple parser modules detected')
    
    if not domains.get('error_handling', []):
        analysis['gaps'].append('error_handling: no failure recovery mechanisms')
    
    if not domains.get('state_persistence', []):
        analysis['gaps'].append('state_persistence: no inter-session memory')
    
    if not domains.get('validation', []):
        analysis['gaps'].append('validation: no output verification layer')
    
    for domain, items in domains.items():
        if len(items) > 2:
            analysis['priorities'].append(f"consolidate_{domain}: {len(items)} modules")
    
    for gap in analysis['gaps'][:3]:
        analysis['priorities'].insert(0, f"build_{gap}")
    
    return analysis

def main():
    lines = sys.stdin.read().strip().split('\n') if not sys.stdin.isatty() else []
    
    evos = parse_evolution_log(lines)
    domains = extract_capabilities(evos)
    analysis = detect_gaps_and_redundancies(domains)
    
    print("=== SELF-DIAGNOSTIC REPORT ===")
    print(f"\nCapability Distribution:")
    for domain, items in sorted(domains.items()):
        print(f"  {domain}: {len(items)}")
    
    print(f"\nRedundancies: {len(analysis['redundant'])}")
    for r in analysis['redundant']:
        print(f"  - {r}")
    
    print(f"\nGaps: {len(analysis['gaps'])}")
    for g in analysis['gaps']:
        print(f"  - {g}")
    
    print(f"\nPriority Actions:")
    for i, p in enumerate(analysis['priorities'][:5], 1):
        print(f"  {i}. {p}")

if __name__ == '__main__':
    main()