#!/usr/bin/env python3
import ast
import sys
from pathlib import Path
from typing import List, Tuple

def cyclomatic_complexity(node: ast.AST) -> int:
    """Count decision points: if, for, while, and, or, except."""
    complexity = 1
    for child in ast.walk(node):
        if isinstance(child, (ast.If, ast.For, ast.While, ast.ExceptHandler)):
            complexity += 1
        elif isinstance(child, ast.BoolOp):
            complexity += len(child.values) - 1
    return complexity

def count_outputs(node: ast.FunctionDef) -> int:
    """Count distinct output paths: returns, yields, raises."""
    outputs = set()
    for child in ast.walk(node):
        if isinstance(child, ast.Return) and child.value:
            outputs.add("return")
        elif isinstance(child, ast.Yield):
            outputs.add("yield")
        elif isinstance(child, ast.Raise):
            outputs.add("raise")
    return len(outputs)

def analyze_function(func: ast.FunctionDef) -> Tuple[str, int, int, bool]:
    """Return (name, complexity, output_count, is_single_responsibility)."""
    cc = cyclomatic_complexity(func)
    outputs = count_outputs(func)
    is_sr = cc <= 4 and outputs <= 1
    return (func.name, cc, outputs, is_sr)

def audit_module(filepath: str) -> List[Tuple[str, int, int, bool]]:
    """Parse module and analyze all functions."""
    source = Path(filepath).read_text()
    tree = ast.parse(source, filename=filepath)
    results = []
    for node in ast.walk(tree):
        if isinstance(node, ast.FunctionDef):
            results.append(analyze_function(node))
    return results

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: single_responsibility_audit.py <module.py>")
        sys.exit(1)
    
    results = audit_module(sys.argv[1])
    print("FUNCTION | CC | OUTPUTS | SR")
    print("-" * 40)
    for name, cc, outputs, is_sr in results:
        sr_mark = "✓" if is_sr else "✗"
        print(f"{name:20} | {cc:2} | {outputs:7} | {sr_mark}")
    
    violations = [r for r in results if not r[3]]
    if violations:
        print(f"\n{len(violations)} function(s) violate single-responsibility")
        sys.exit(1)