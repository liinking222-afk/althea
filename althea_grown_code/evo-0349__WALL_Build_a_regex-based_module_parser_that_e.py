#!/usr/bin/env python3
import re
import sys

def parse_evolution_entry(text):
    """Parse evolution log entries using pragmatic regex patterns."""
    
    # Multiple ways to match - embrace flexibility
    patterns = {
        'evo': r'\[EVO #(\d+) (\w+) v([\d.]+)→v([\d.]+)\]\s*(.+?)(?=\s*—|$)',
        'growth': r'\[GROWTH /([\w-]+)\]\s*(.+?)(?:\s*\((.+?)\))?\.?\s*(.+?)(?=\s*—|$)',
        'autosynth': r'\[AUTOSYNTH /([\w-]+)\]\s*(.+?)(?:\s*\((.+?)\))?\.?\s*(.+?)(?=\s*—|$)',
    }
    
    for entry_type, pattern in patterns.items():
        match = re.search(pattern, text, re.IGNORECASE)
        if match:
            if entry_type == 'evo':
                num, archetype, old_v, new_v, desc = match.groups()
                return {
                    'type': 'EVO',
                    'id': num,
                    'archetype': archetype,
                    'version': f"{old_v}→{new_v}",
                    'description': desc.strip()
                }
            else:
                groups = match.groups()
                return {
                    'type': entry_type.upper(),
                    'module': groups[0],
                    'title': groups[1].strip() if len(groups) > 1 else '',
                    'context': groups[2].strip() if len(groups) > 2 and groups[2] else '',
                    'description': groups[3].strip() if len(groups) > 3 else ''
                }
    return None

def main():
    """Read stdin, parse, output TSV to stdout - unix philosophy."""
    print("type\tidentifier\tmetadata\tdescription")
    
    for line in sys.stdin:
        line = line.strip()
        if not line or line.startswith('#'):
            continue
            
        parsed = parse_evolution_entry(line)
        if parsed:
            if parsed['type'] == 'EVO':
                print(f"{parsed['type']}\t#{parsed['id']}:{parsed['archetype']}\t{parsed['version']}\t{parsed['description']}")
            else:
                meta = f"{parsed.get('title','')} ({parsed.get('context','')})" if parsed.get('context') else parsed.get('title','')
                print(f"{parsed['type']}\t{parsed['module']}\t{meta}\t{parsed.get('description','')}")

if __name__ == '__main__':
    main()