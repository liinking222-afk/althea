#!/usr/bin/env python3
"""refactor_split_concerns.py - Decompose multi-concern functions into single-purpose units"""

import ast
import sys
from typing import List, Tuple

def count_responsibilities(node: ast.FunctionDef) -> int:
    """Count distinct concerns: assignments, calls, branches, loops"""
    concerns = 0
    for child in ast.walk(node):
        if isinstance(child, (ast.Assign, ast.AnnAssign)):
            concerns += 1
        elif isinstance(child, (ast.If, ast.For, ast.While)):
            concerns += 1
    return concerns

def extract_function_signatures(code: str) -> List[Tuple[str, int, int]]:
    """Return (name, line, responsibility_count) for each function"""
    tree = ast.parse(code)
    results = []
    for node in ast.walk(tree):
        if isinstance(node, ast.FunctionDef):
            count = count_responsibilities(node)
            results.append((node.name, node.lineno, count))
    return results

def propose_split(name: str, concerns: int) -> str:
    """Generate split suggestion following Kernighan principle"""
    if concerns <= 2:
        return ""
    parts = [f"{name}_parse", f"{name}_validate", f"{name}_transform"]
    return f"# Split {name} into: {' | '.join(parts[:concerns])}"

def main():
    if len(sys.argv) < 2:
        print("Usage: refactor_split_concerns.py <file.py>")
        sys.exit(1)
    
    with open(sys.argv[1]) as f:
        code = f.read()
    
    sigs = extract_function_signatures(code)
    
    for name, line, concerns in sigs:
        if concerns > 2:
            print(f"L{line:03d} {name:30s} concerns={concerns}")
            print(f"      {propose_split(name, concerns)}")

if __name__ == "__main__":
    main()