#!/usr/bin/env python3
import re
import json
from pathlib import Path
from collections import defaultdict

def extract_signatures(code_text):
    """Extract function/method signatures from code."""
    patterns = [
        r'def\s+([a-zA-Z_][a-zA-Z0-9_]*)\s*\([^)]*\):',  # Python
        r'function\s+([a-zA-Z_][a-zA-Z0-9_]*)\s*\([^)]*\)',  # JavaScript
        r'fn\s+([a-zA-Z_][a-zA-Z0-9_]*)\s*\([^)]*\)',  # Rust
        r'func\s+([a-zA-Z_][a-zA-Z0-9_]*)\s*\([^)]*\)',  # Go
    ]
    signatures = []
    for pattern in patterns:
        signatures.extend(re.findall(pattern, code_text))
    return signatures

def index_capabilities(evolution_log_path):
    """Build capability index from evolution history."""
    index = defaultdict(list)
    
    try:
        with open(evolution_log_path, 'r') as f:
            for line in f:
                if not line.strip():
                    continue
                try:
                    entry = json.loads(line)
                    if 'code' in entry and 'module' in entry:
                        sigs = extract_signatures(entry['code'])
                        for sig in sigs:
                            index[sig].append({
    'module': entry['module'],
    'version': entry.get('version', 'unknown'),
    'timestamp': entry.get('timestamp', 'unknown')
                            })
                except json.JSONDecodeError:
                    continue
    except FileNotFoundError:
        return {}
    
    return dict(index)

def query_capability(index, name_fragment):
    """Find capabilities matching name fragment."""
    matches = []
    for func_name, occurrences in index.items():
        if name_fragment.lower() in func_name.lower():
            matches.append({
                'function': func_name,
                'occurrences': len(occurrences),
                'latest': occurrences[-1]
            })
    return sorted(matches, key=lambda x: x['occurrences'], reverse=True)

if __name__ == '__main__':
    import sys
    log_path = sys.argv[1] if len(sys.argv) > 1 else 'evolution.log'
    query = sys.argv[2] if len(sys.argv) > 2 else None
    
    idx = index_capabilities(log_path)
    
    if query:
        results = query_capability(idx, query)
        for r in results[:10]:
            print(f"{r['function']} (n={r['occurrences']}) — {r['latest']['module']}")
    else:
        print(f"Indexed {len(idx)} unique functions across evolution history")