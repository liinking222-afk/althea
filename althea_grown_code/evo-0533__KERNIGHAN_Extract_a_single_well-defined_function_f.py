#!/usr/bin/env python3
"""
function_extractor.py - Extract single functions from modules for composition
"""

import ast
import sys
from typing import Optional

def extract_function(source_code: str, function_name: str) -> Optional[str]:
    """Extract one function with its imports and return standalone code."""
    try:
        tree = ast.parse(source_code)
    except SyntaxError:
        return None
    
    imports = []
    target_func = None
    
    for node in ast.walk(tree):
        if isinstance(node, (ast.Import, ast.ImportFrom)):
            imports.append(ast.unparse(node))
        elif isinstance(node, ast.FunctionDef) and node.name == function_name:
            target_func = ast.unparse(node)
    
    if not target_func:
        return None
    
    lines = list(dict.fromkeys(imports))  # deduplicate preserving order
    if lines:
        lines.append("")
    lines.append(target_func)
    
    return "\n".join(lines)

def main():
    if len(sys.argv) != 3:
        print("Usage: function_extractor.py <source_file> <function_name>", file=sys.stderr)
        sys.exit(1)
    
    source_file = sys.argv[1]
    function_name = sys.argv[2]
    
    with open(source_file, 'r') as f:
        source = f.read()
    
    result = extract_function(source, function_name)
    
    if result:
        print(result)
    else:
        print(f"Function '{function_name}' not found", file=sys.stderr)
        sys.exit(1)

if __name__ == "__main__":
    main()