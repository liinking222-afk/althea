#!/usr/bin/env python3
import sys
import json

def extract_path(obj, path):
    """Extract value from nested object using dot notation like 'user.name.first'"""
    keys = path.split('.')
    current = obj
    for key in keys:
        if isinstance(current, dict):
            current = current.get(key)
        elif isinstance(current, list) and key.isdigit():
            idx = int(key)
            current = current[idx] if idx < len(current) else None
        else:
            return None
        if current is None:
            return None
    return current

def main():
    if len(sys.argv) < 2:
        print("Usage: jq_simple.py <path> [path2...] < input.json", file=sys.stderr)
        sys.exit(1)
    
    paths = sys.argv[1:]
    
    try:
        for line in sys.stdin:
            line = line.strip()
            if not line:
                continue
            
            try:
                data = json.loads(line)
            except json.JSONDecodeError:
                continue
            
            results = []
            for path in paths:
                value = extract_path(data, path)
                if value is not None:
                    if isinstance(value, (dict, list)):
                        results.append(json.dumps(value))
                    else:
                        results.append(str(value))
            
            if results:
                print('\t'.join(results))
    
    except KeyboardInterrupt:
        sys.exit(0)

if __name__ == '__main__':
    main()