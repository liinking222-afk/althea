#!/usr/bin/env python3
import sys
import re
import json

def extract_module_signature(line):
    """Parse memory line and extract module metadata if present."""
    evo_match = re.search(r'\[EVO #(\d+) (\w+) v([\d.]+)→v([\d.]+)\]\s*(.+?)(?:\s*—\s*(.+))?$', line)
    if evo_match:
        return {
            'type': 'evolution',
            'id': int(evo_match.group(1)),
            'archetype': evo_match.group(2),
            'version_from': evo_match.group(3),
            'version_to': evo_match.group(4),
            'intent': evo_match.group(5).strip(),
            'note': evo_match.group(6).strip() if evo_match.group(6) else None
        }
    
    growth_match = re.search(r'\[GROWTH /autonomous-(\S+)\]\s*(.+?)(?:\s*\((.+?)\))?\.?\s*(.+?)(?:\s*—\s*(.+))?$', line)
    if growth_match:
        return {
            'type': 'growth',
            'module': growth_match.group(1),
            'title': growth_match.group(2).strip(),
            'category': growth_match.group(3).strip() if growth_match.group(3) else None,
            'description': growth_match.group(4).strip(),
            'rationale': growth_match.group(5).strip() if growth_match.group(5) else None
        }
    
    return None

def main():
    for line in sys.stdin:
        line = line.rstrip('\n')
        sig = extract_module_signature(line)
        if sig:
            print(json.dumps(sig))

if __name__ == '__main__':
    main()