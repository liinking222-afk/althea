#!/usr/bin/env python3
import sys
import re
import json

def sniff_structure(line):
    """Duck-type the line into whatever it wants to be."""
    line = line.strip()
    if not line:
        return None
    
    # JSON-ish?
    if line.startswith('{') or line.startswith('['):
        try:
            return ('json', json.loads(line))
        except:
            pass
    
    # Key-value-ish?
    kv_match = re.match(r'^(\w+)[:=]\s*(.+)$', line)
    if kv_match:
        return ('kv', {kv_match.group(1): kv_match.group(2)})
    
    # List-ish with bullets/dashes?
    list_match = re.match(r'^[-*•]\s*(.+)$', line)
    if list_match:
        return ('list', list_match.group(1))
    
    # Bracketed tag-ish?
    tag_match = re.match(r'^\[([^\]]+)\]\s*(.*)$', line)
    if tag_match:
        return ('tagged', {'tag': tag_match.group(1), 'content': tag_match.group(2)})
    
    # Path-ish?
    if re.match(r'^[/~]', line) or re.search(r'\w+/\w+', line):
        return ('path', line)
    
    # Just text
    return ('text', line)

def extract_patterns(stream):
    """There's more than one way to parse it."""
    patterns = {}
    
    for line in stream:
        result = sniff_structure(line)
        if result:
            type_name, payload = result
            if type_name not in patterns:
                patterns[type_name] = []
            patterns[type_name].append(payload)
    
    return patterns

if __name__ == '__main__':
    patterns = extract_patterns(sys.stdin)
    
    # Emit what we found, however we found it
    for pattern_type, instances in patterns.items():
        print(json.dumps({
            'pattern': pattern_type,
            'count': len(instances),
            'samples': instances[:3],
            'total': instances
        }))