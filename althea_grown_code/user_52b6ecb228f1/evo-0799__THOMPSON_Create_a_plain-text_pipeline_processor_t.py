#!/usr/bin/env python3
import sys
import json
import importlib.util
from pathlib import Path

def load_module_from_path(module_path):
    """Load a Python module from filesystem path."""
    spec = importlib.util.spec_from_file_location("piped_module", module_path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module

def invoke_module(module, input_data):
    """Call module's process() function with input, return output."""
    if hasattr(module, 'process'):
        return module.process(input_data)
    elif hasattr(module, 'main'):
        return module.main(input_data)
    else:
        raise AttributeError(f"Module lacks process() or main() function")

def main():
    if len(sys.argv) < 2:
        print("Usage: pipe.py <module1.py> [module2.py] ...", file=sys.stderr)
        sys.exit(1)
    
    module_paths = [Path(p) for p in sys.argv[1:]]
    modules = [load_module_from_path(p) for p in module_paths]
    
    # Read input from stdin
    input_text = sys.stdin.read().strip()
    
    # Try to parse as JSON, fall back to plain text
    try:
        data = json.loads(input_text)
    except json.JSONDecodeError:
        data = input_text
    
    # Chain modules: output of one becomes input of next
    current = data
    for module in modules:
        current = invoke_module(module, current)
    
    # Write final output to stdout
    if isinstance(current, (dict, list)):
        print(json.dumps(current, indent=2))
    else:
        print(current)

if __name__ == "__main__":
    main()