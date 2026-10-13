#!/usr/bin/env python3
"""refactor_extract_function.py - Extract one function from module code"""

import re
import sys
from typing import Optional

def find_function_body(code: str, func_name: str) -> Optional[str]:
    """Locate and return a complete function definition by name."""
    pattern = rf'^(def {re.escape(func_name)}\([^)]*\):.*?)(?=^def |\Z)'
    match = re.search(pattern, code, re.MULTILINE | re.DOTALL)
    return match.group(1).rstrip() if match else None

def extract_imports(code: str, func_body: str) -> str:
    """Find imports used by the function body."""
    imports = []
    for line in code.split('\n'):
        line = line.strip()
        if line.startswith(('import ', 'from ')):
            # Check if any symbol in import appears in function
            if any(word in func_body for word in line.split()[1:3]):
                imports.append(line)
    return '\n'.join(imports)

def create_standalone_module(code: str, func_name: str) -> Optional[str]:
    """Extract function with its imports into standalone module."""
    func_body = find_function_body(code, func_name)
    if not func_body:
        return None
    
    imports = extract_imports(code, func_body)
    header = f'"""Extracted function: {func_name}"""'
    
    return '\n\n'.join(filter(None, [header, imports, func_body]))

if __name__ == '__main__':
    if len(sys.argv) != 3:
        print("Usage: refactor_extract_function.py <file.py> <function_name>")
        sys.exit(1)
    
    with open(sys.argv[1]) as f:
        code = f.read()
    
    result = create_standalone_module(code, sys.argv[2])
    if result:
        print(result)
    else:
        print(f"Function '{sys.argv[2]}' not found", file=sys.stderr)
        sys.exit(1)