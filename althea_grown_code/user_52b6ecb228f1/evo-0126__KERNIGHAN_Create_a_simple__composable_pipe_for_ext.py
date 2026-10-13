#!/usr/bin/env python3
"""memory_fact_extractor.py - Extract one fact type from memory stream"""

import sys
import json
import re

def extract_evolution_number(line):
    """Extract evolution cycle number from EVO entries."""
    match = re.search(r'\[EVO #(\d+)', line)
    return match.group(1) if match else None

def extract_growth_path(line):
    """Extract growth module path from GROWTH entries."""
    match = re.search(r'\[GROWTH (/[^\]]+)\]', line)
    return match.group(1) if match else None

def extract_archetype(line):
    """Extract archetype name from EVO entries."""
    match = re.search(r'\[EVO #\d+ (\w+)', line)
    return match.group(1) if match else None

def extract_version(line):
    """Extract version transition from EVO entries."""
    match = re.search(r'v([\d.]+)→v([\d.]+)', line)
    return f"{match.group(1)}→{match.group(2)}" if match else None

EXTRACTORS = {
    'evo-number': extract_evolution_number,
    'growth-path': extract_growth_path,
    'archetype': extract_archetype,
    'version': extract_version,
}

def main():
    if len(sys.argv) != 2 or sys.argv[1] not in EXTRACTORS:
        print(f"Usage: {sys.argv[0]} {{{','.join(EXTRACTORS.keys())}}}", file=sys.stderr)
        sys.exit(1)
    
    extractor = EXTRACTORS[sys.argv[1]]
    
    for line in sys.stdin:
        result = extractor(line.strip())
        if result:
            print(result)

if __name__ == '__main__':
    main()