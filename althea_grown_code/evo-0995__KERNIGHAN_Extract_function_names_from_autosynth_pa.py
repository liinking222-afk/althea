#!/usr/bin/env python3
"""pattern_verb_extractor.py - Extract verbs from autosynth patterns"""

import re
from typing import List, Dict, Set
from pathlib import Path

def extract_pattern_name(line: str) -> str:
    """Extract pattern from [AUTOSYNTH /path/pattern-name-1234] format."""
    match = re.search(r'/autonomous-([a-z-]+)-\d+\]', line)
    return match.group(1) if match else ""

def pattern_to_verb(pattern: str) -> str:
    """Convert hyphenated-pattern to verb: last significant word."""
    parts = pattern.split('-')
    # Filter out common suffixes
    significant = [p for p in parts if p not in {'api', 'tool', 'module'}]
    return significant[-1] if significant else parts[-1]

def extract_description_verb(line: str) -> str:
    """Extract primary verb from description after pattern."""
    match = re.search(r'\] ([A-Z][a-z]+ [A-Z][a-z]+) \(', line)
    if match:
        words = match.group(1).split()
        return words[-1].lower()  # Last word is usually the verb
    return ""

def build_verb_index(memory_lines: List[str]) -> Dict[str, Set[str]]:
    """Build verb -> [patterns] index from memory."""
    index: Dict[str, Set[str]] = {}
    
    for line in memory_lines:
        if 'AUTOSYNTH' not in line:
            continue
        
        pattern = extract_pattern_name(line)
        if not pattern:
            continue
        
        verb = pattern_to_verb(pattern)
        desc_verb = extract_description_verb(line)
        
        for v in [verb, desc_verb]:
            if v:
                if v not in index:
                    index[v] = set()
                index[v].add(pattern)
    
    return index

def query_verb(index: Dict[str, Set[str]], verb: str) -> List[str]:
    """Query capabilities by verb."""
    return sorted(index.get(verb.lower(), set()))

if __name__ == '__main__':
    # Pipe-friendly: read from stdin, write to stdout
    import sys
    lines = sys.stdin.readlines()
    index = build_verb_index(lines)
    
    for verb in sorted(index.keys()):
        patterns = ','.join(sorted(index[verb]))
        print(f"{verb}:{patterns}")