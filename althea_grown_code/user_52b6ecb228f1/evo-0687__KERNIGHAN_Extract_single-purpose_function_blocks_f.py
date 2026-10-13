#!/usr/bin/env python3
import ast
import sys
from pathlib import Path
from typing import List, Tuple

def count_statements(node: ast.AST) -> int:
    """Count executable statements in a node."""
    stmt_types = (ast.Assign, ast.AugAssign, ast.Return, ast.Expr, 
                  ast.If, ast.For, ast.While, ast.With, ast.Try, ast.Raise)
    return sum(1 for _ in ast.walk(node) if isinstance(_, stmt_types))

def analyze_function(func: ast.FunctionDef) -> Tuple[str, int, int, List[str]]:
    """Return (name, statement_count, branch_count, called_functions)."""
    stmts = count_statements(func)
    branches = sum(1 for _ in ast.walk(func) if isinstance(_, (ast.If, ast.For, ast.While)))
    calls = [n.func.id for n in ast.walk(func) 
             if isinstance(n, ast.Call) and isinstance(n.func, ast.Name)]
    return (func.name, stmts, branches, calls)

def measure_module(path: Path) -> List[dict]:
    """Parse module and extract function metrics."""
    try:
        tree = ast.parse(path.read_text())
    except:
        return []
    
    functions = [node for node in ast.walk(tree) if isinstance(node, ast.FunctionDef)]
    results = []
    
    for func in functions:
        name, stmts, branches, calls = analyze_function(func)
        complexity = stmts + (branches * 2)
        results.append({
            'name': name,
            'statements': stmts,
            'branches': branches,
            'complexity': complexity,
            'calls': len(calls),
            'does_one_thing': complexity <= 10 and branches <= 2
        })
    
    return results

def report(module_path: str):
    """Generate Kernighan-style clarity report."""
    results = measure_module(Path(module_path))
    if not results:
        return
    
    complex_funcs = [r for r in results if not r['does_one_thing']]
    
    print(f"MODULE: {module_path}")
    print(f"FUNCTIONS: {len(results)} | FOCUSED: {len(results) - len(complex_funcs)}")
    
    if complex_funcs:
        print("\nNEEDS DECOMPOSITION:")
        for f in sorted(complex_funcs, key=lambda x: -x['complexity']):
            print(f"  {f['name']}: {f['statements']} stmts, {f['branches']} branches → split")
    else:
        print("\nCLARITY ACHIEVED: All functions do one thing.")

if __name__ == '__main__':
    report(sys.argv[1] if len(sys.argv) > 1 else __file__)