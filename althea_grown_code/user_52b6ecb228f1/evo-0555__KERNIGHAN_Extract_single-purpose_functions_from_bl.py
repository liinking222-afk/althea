#!/usr/bin/env python3
"""
refactor_extract_function.py
Kernighan's Law: Debugging is twice as hard as writing.
Therefore: write simple functions you can actually debug.
"""

import ast
import sys
from pathlib import Path
from typing import List, Tuple


def extract_functions(source_code: str) -> List[Tuple[str, str, int]]:
    """Return list of (name, source, line_count) for each function."""
    tree = ast.parse(source_code)
    functions = []
    
    for node in ast.walk(tree):
        if isinstance(node, ast.FunctionDef):
            func_source = ast.get_source_segment(source_code, node)
            if func_source:
                line_count = func_source.count('\n') + 1
                functions.append((node.name, func_source, line_count))
    
    return functions


def count_responsibilities(func_source: str) -> int:
    """Count distinct operations: assignments, calls, returns, loops."""
    tree = ast.parse(func_source)
    responsibilities = 0
    
    for node in ast.walk(tree):
        if isinstance(node, (ast.Assign, ast.AugAssign, ast.Call, 
                           ast.Return, ast.For, ast.While, ast.If)):
            responsibilities += 1
    
    return responsibilities


def suggest_extractions(module_path: str) -> None:
    """Identify bloated functions that violate single-responsibility."""
    source = Path(module_path).read_text()
    functions = extract_functions(source)
    
    print(f"MODULE: {module_path}")
    print("=" * 60)
    
    for name, source, lines in functions:
        responsibilities = count_responsibilities(source)
        ratio = responsibilities / max(lines, 1)
        
        if responsibilities > 5 or lines > 30:
            print(f"\n⚠ {name}()")
            print(f"  Lines: {lines} | Operations: {responsibilities}")
            print(f"  Complexity ratio: {ratio:.2f}")
            print(f"  → EXTRACT smaller functions")
            print(f"  → Each should do ONE thing")
            print(f"  → Pipe them together")


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: refactor_extract_function.py <module.py>")
        sys.exit(1)
    
    suggest_extractions(sys.argv[1])