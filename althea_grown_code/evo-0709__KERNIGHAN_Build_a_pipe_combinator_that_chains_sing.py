#!/usr/bin/env python3
"""pipe.py - Kernighan-style module composition via stdin/stdout"""

import sys
import subprocess
import json
from pathlib import Path

def pipe(*module_names):
    """Chain modules left-to-right. Each reads stdin, writes stdout."""
    if not module_names:
        return None
    
    data = sys.stdin.read() if not sys.stdin.isatty() else ""
    
    for module_name in module_names:
        module_path = Path(__file__).parent / f"{module_name}.py"
        
        if not module_path.exists():
            print(f"Module not found: {module_name}", file=sys.stderr)
            sys.exit(1)
        
        try:
            result = subprocess.run(
                [sys.executable, str(module_path)],
                input=data,
                capture_output=True,
                text=True,
                timeout=30
            )
            
            if result.returncode != 0:
                print(f"Module {module_name} failed: {result.stderr}", file=sys.stderr)
                sys.exit(result.returncode)
            
            data = result.stdout
            
        except subprocess.TimeoutExpired:
            print(f"Module {module_name} timed out", file=sys.stderr)
            sys.exit(124)
    
    return data

def main():
    if len(sys.argv) < 2:
        print("Usage: pipe.py module1 module2 ... moduleN", file=sys.stderr)
        print("Example: echo 'H2O' | pipe.py chemistry-lookup format-json", file=sys.stderr)
        sys.exit(1)
    
    result = pipe(*sys.argv[1:])
    if result is not None:
        print(result, end='')

if __name__ == "__main__":
    main()