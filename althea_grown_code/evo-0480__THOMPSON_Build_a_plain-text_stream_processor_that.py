#!/usr/bin/env python3
import sys
import json
import re

def module_stream_filter(operation, pattern=None):
    """UNIX-style filter for Althea module registry streams."""
    for line in sys.stdin:
        line = line.strip()
        if not line:
            continue
        
        try:
            module = json.loads(line)
        except json.JSONDecodeError:
            continue
        
        if operation == "grep":
            if pattern and re.search(pattern, json.dumps(module), re.IGNORECASE):
                print(json.dumps(module))
        
        elif operation == "list":
            name = module.get("name", "unknown")
            category = module.get("category", "unknown")
            print(f"{name}\t{category}")
        
        elif operation == "describe":
            name = module.get("name", "unknown")
            intent = module.get("intent", "no description")
            print(f"{name}: {intent}")
        
        elif operation == "deps":
            name = module.get("name", "unknown")
            deps = module.get("dependencies", [])
            for dep in deps:
                print(f"{name}\t{dep}")
        
        elif operation == "json":
            print(json.dumps(module, indent=2))
        
        elif operation == "count":
            print(1)

def main():
    if len(sys.argv) < 2:
        print("Usage: module_filter <grep|list|describe|deps|json|count> [pattern]", file=sys.stderr)
        sys.exit(1)
    
    operation = sys.argv[1]
    pattern = sys.argv[2] if len(sys.argv) > 2 else None
    
    module_stream_filter(operation, pattern)

if __name__ == "__main__":
    main()