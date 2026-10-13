#!/usr/bin/env python3
"""Memory deduplication filter - removes consecutive duplicate entries."""

import sys
import json
from typing import List, Dict, Any
from hashlib import blake2b


def hash_entry(entry: Dict[str, Any]) -> str:
    """Generate stable hash of memory entry content."""
    content = json.dumps(entry, sort_keys=True, separators=(',', ':'))
    return blake2b(content.encode(), digest_size=16).hexdigest()


def deduplicate_consecutive(entries: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Remove consecutive duplicate entries, preserving order."""
    if not entries:
        return []
    
    result = []
    prev_hash = None
    
    for entry in entries:
        current_hash = hash_entry(entry)
        if current_hash != prev_hash:
            result.append(entry)
            prev_hash = current_hash
    
    return result


def main():
    """Read JSON array from stdin, deduplicate, write to stdout."""
    try:
        data = json.load(sys.stdin)
        
        if isinstance(data, list):
            deduplicated = deduplicate_consecutive(data)
            json.dump(deduplicated, sys.stdout, indent=2)
            
            removed = len(data) - len(deduplicated)
            if removed > 0:
                print(f"\n# Removed {removed} consecutive duplicates", file=sys.stderr)
        else:
            json.dump(data, sys.stdout, indent=2)
            
    except json.JSONDecodeError as e:
        print(f"Error: Invalid JSON input: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()