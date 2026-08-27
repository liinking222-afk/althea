#!/usr/bin/env python3
import sys
import json
from typing import Any, List

def get_nested(obj: Any, path: str) -> str:
    """Extract value from nested object using dot notation."""
    keys = path.split('.')
    current = obj
    try:
        for key in keys:
            if isinstance(current, dict):
                current = current[key]
            elif isinstance(current, list) and key.isdigit():
                current = current[int(key)]
            else:
                return ""
        return str(current) if current is not None else ""
    except (KeyError, IndexError, TypeError):
        return ""

def main():
    if len(sys.argv) < 2:
        print("Usage: jq_stream.py <field1> [field2] ... < input.jsonl", file=sys.stderr)
        print("Example: cat data.jsonl | jq_stream.py user.name timestamp", file=sys.stderr)
        sys.exit(1)
    
    fields = sys.argv[1:]
    
    for line in sys.stdin:
        line = line.strip()
        if not line:
            continue
        
        try:
            obj = json.loads(line)
            values = [get_nested(obj, field) for field in fields]
            print('\t'.join(values))
        except json.JSONDecodeError:
            continue

if __name__ == "__main__":
    main()