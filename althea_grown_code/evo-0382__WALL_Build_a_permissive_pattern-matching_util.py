#!/usr/bin/env python3
import re
import json
import sys
from difflib import SequenceMatcher
from typing import Any, List, Dict, Union

def fuzzy_ratio(a: str, b: str) -> float:
    """Quick fuzzy match ratio between two strings."""
    return SequenceMatcher(None, a.lower(), b.lower()).ratio()

def match_pattern(pattern: str, data: Any, threshold: float = 0.6) -> bool:
    """
    DWIM pattern matching - regex, fuzzy, or exact.
    pattern can be:
      - /regex/ for regex matching
      - ~fuzzy for fuzzy matching (>=threshold)
      - plain string for substring search
    """
    if isinstance(data, (dict, list)):
        data = json.dumps(data)
    data_str = str(data)
    
    # Regex mode
    if pattern.startswith('/') and pattern.endswith('/'):
        regex = pattern[1:-1]
        return bool(re.search(regex, data_str, re.IGNORECASE))
    
    # Fuzzy mode
    if pattern.startswith('~'):
        target = pattern[1:]
        return fuzzy_ratio(target, data_str) >= threshold
    
    # Substring mode (default)
    return pattern.lower() in data_str.lower()

def search_memory(records: List[Dict], patterns: List[str], mode: str = 'any') -> List[Dict]:
    """
    Search memory records with multiple patterns.
    mode: 'any' (OR) or 'all' (AND)
    """
    results = []
    for record in records:
        matches = [match_pattern(p, record) for p in patterns]
        if (mode == 'any' and any(matches)) or (mode == 'all' and all(matches)):
            results.append(record)
    return results

if __name__ == '__main__':
    # Read JSONL from stdin
    records = []
    for line in sys.stdin:
        line = line.strip()
        if line:
            try:
                records.append(json.loads(line))
            except json.JSONDecodeError:
                records.append({'raw': line})
    
    # Parse args: patterns and optional mode
    patterns = [arg for arg in sys.argv[1:] if not arg.startswith('--')]
    mode = 'all' if '--all' in sys.argv else 'any'
    
    # Search and output
    results = search_memory(records, patterns, mode)
    for r in results:
        print(json.dumps(r))