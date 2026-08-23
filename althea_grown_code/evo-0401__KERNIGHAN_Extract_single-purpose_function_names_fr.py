#!/usr/bin/env python3
import sys
import re
from collections import Counter

def extract_function_names(line):
    """Extract function-like names from a single line."""
    # Match: function_name, methodName, /path-to-thing, moduleName
    patterns = [
        r'/autonomous-([a-z-]+)',
        r'\b([a-z_]{3,})\(',
        r'def ([a-z_]{3,})',
        r'function ([a-z_]{3,})',
    ]
    names = []
    for pattern in patterns:
        names.extend(re.findall(pattern, line.lower()))
    return names

def filter_single_purpose(name):
    """Keep only names suggesting single-purpose tools."""
    # Reject generic names, keep domain-specific verbs
    generic = {'get', 'set', 'make', 'run', 'call', 'init', 'main', 'test'}
    if name in generic or len(name) < 4:
        return False
    # Favor verb-noun or action patterns
    return '-' in name or '_' in name

def main():
    """Read lines, extract function names, count single-purpose tools."""
    names = []
    for line in sys.stdin:
        names.extend(extract_function_names(line))
    
    filtered = [n for n in names if filter_single_purpose(n)]
    counts = Counter(filtered)
    
    # Output as simple key-value pairs (pipe-friendly)
    for name, count in counts.most_common(20):
        print(f"{name}\t{count}")

if __name__ == "__main__":
    main()