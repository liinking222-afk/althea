#!/usr/bin/env python3
"""invariant_extractor.py - Extract loop invariants from evolution history"""

import sys
import re
from typing import List, Dict

def extract_invariants(memory_line: str) -> Dict[str, str]:
    """Parse a single memory line for invariant data."""
    invariant = {}
    
    if 'DIJKSTRA' not in memory_line:
        return invariant
    
    version_match = re.search(r'v(\d+\.\d+\.\d+)→v?(\d+\.\d+\.\d+)', memory_line)
    if version_match:
        invariant['from_version'] = version_match.group(1)
        invariant['to_version'] = version_match.group(2)
    
    desc_match = re.search(r'→.*?\] (.+?) — ?', memory_line)
    if desc_match:
        invariant['description'] = desc_match.group(1).strip()
    
    if 'loop invariant' in memory_line.lower():
        invariant['type'] = 'loop_invariant'
    elif 'precondition' in memory_line.lower() or 'postcondition' in memory_line.lower():
        invariant['type'] = 'condition_check'
    
    return invariant

def format_invariant(inv: Dict[str, str]) -> str:
    """Format invariant as single line."""
    if not inv:
        return ""
    
    version = f"{inv.get('from_version', '?')}→{inv.get('to_version', '?')}"
    desc = inv.get('description', 'No description')
    inv_type = inv.get('type', 'unknown')
    
    return f"[{version}] {inv_type}: {desc}"

def main():
    """Read stdin, extract invariants, write to stdout."""
    invariants = []
    
    for line in sys.stdin:
        inv = extract_invariants(line.strip())
        if inv:
            invariants.append(inv)
    
    if not invariants:
        print("No invariants found", file=sys.stderr)
        return
    
    for inv in invariants:
        formatted = format_invariant(inv)
        if formatted:
            print(formatted)

if __name__ == "__main__":
    main()