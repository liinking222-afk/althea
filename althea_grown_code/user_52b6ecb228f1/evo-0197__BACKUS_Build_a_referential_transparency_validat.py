#!/usr/bin/env python3
import ast
import sys
from pathlib import Path
from typing import Set, List, Tuple

class PurityViolationDetector(ast.NodeVisitor):
    def __init__(self):
        self.violations: List[Tuple[int, str]] = []
        self.impure_calls: Set[str] = {
            'print', 'open', 'input', 'exec', 'eval', 'compile',
            '__import__', 'breakpoint', 'exit', 'quit'
        }
        self.dangerous_modules: Set[str] = {
            'random', 'time', 'datetime', 'os', 'sys', 'subprocess'
        }
        
    def visit_Call(self, node):
        if isinstance(node.func, ast.Name):
            if node.func.id in self.impure_calls:
                self.violations.append((node.lineno, f"Impure call: {node.func.id}"))
        self.generic_visit(node)
    
    def visit_Assign(self, node):
        for target in node.targets:
            if isinstance(target, ast.Subscript):
                self.violations.append((node.lineno, "Mutation via subscript assignment"))
        self.generic_visit(node)
    
    def visit_AugAssign(self, node):
        self.violations.append((node.lineno, f"In-place mutation: {ast.unparse(node.target)}"))
        self.generic_visit(node)
    
    def visit_Global(self, node):
        self.violations.append((node.lineno, f"Global state access: {', '.join(node.names)}"))
        self.generic_visit(node)
    
    def visit_Nonlocal(self, node):
        self.violations.append((node.lineno, f"Nonlocal state: {', '.join(node.names)}"))
        self.generic_visit(node)
    
    def visit_Import(self, node):
        for alias in node.names:
            if alias.name.split('.')[0] in self.dangerous_modules:
                self.violations.append((node.lineno, f"Non-deterministic module: {alias.name}"))
        self.generic_visit(node)

def analyze_purity(source_code: str, filename: str = "<string>") -> dict:
    try:
        tree = ast.parse(source_code, filename)
    except SyntaxError as e:
        return {"error": str(e), "pure": False}
    
    detector = PurityViolationDetector()
    detector.visit(tree)
    
    return {
        "pure": len(detector.violations) == 0,
        "violations": detector.violations,
        "purity_score": max(0, 100 - len(detector.violations) * 10)
    }

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: purity_validator.py <file.py>")
        sys.exit(1)
    
    filepath = Path(sys.argv[1])
    source = filepath.read_text()
    result = analyze_purity(source, str(filepath))
    
    if result.get("error"):
        print(f"ERROR: {result['error']}")
        sys.exit(2)
    
    print(f"PURITY_SCORE: {result['purity_score']}/100")
    if result['pure']:
        print("✓ Module exhibits referential transparency")
    else:
        print("✗ Purity violations detected:")
        for lineno, violation in result['violations']:
            print(f"  Line {lineno}: {violation}")
        sys.exit(1)