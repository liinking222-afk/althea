#!/usr/bin/env python3
import ast
import re
from typing import List, Dict, Tuple, Optional

class InvariantValidator(ast.NodeVisitor):
    def __init__(self):
        self.violations: List[Dict] = []
        self.invariants: Dict[str, List[str]] = {}
        self.current_function = None
        
    def visit_FunctionDef(self, node):
        self.current_function = node.name
        docstring = ast.get_docstring(node)
        if docstring:
            self._extract_invariants(docstring, node.name)
        self.generic_visit(node)
        self.current_function = None
        
    def _extract_invariants(self, docstring: str, func_name: str):
        invariant_pattern = r'@invariant:\s*(.+?)(?:\n|$)'
        pre_pattern = r'@pre:\s*(.+?)(?:\n|$)'
        post_pattern = r'@post:\s*(.+?)(?:\n|$)'
        
        self.invariants[func_name] = {
            'invariants': re.findall(invariant_pattern, docstring),
            'preconditions': re.findall(pre_pattern, docstring),
            'postconditions': re.findall(post_pattern, docstring)
        }
        
    def visit_While(self, node):
        if self.current_function:
            func_inv = self.invariants.get(self.current_function, {})
            if not func_inv.get('invariants'):
                self.violations.append({
                    'type': 'MISSING_INVARIANT',
                    'function': self.current_function,
                    'line': node.lineno,
                    'severity': 'HIGH'
                })
        self.generic_visit(node)
        
    def visit_For(self, node):
        if self.current_function:
            func_inv = self.invariants.get(self.current_function, {})
            if not func_inv.get('invariants'):
                self.violations.append({
                    'type': 'MISSING_INVARIANT',
                    'function': self.current_function,
                    'line': node.lineno,
                    'severity': 'HIGH'
                })
        self.generic_visit(node)

def validate_module(code: str) -> Tuple[bool, List[Dict]]:
    try:
        tree = ast.parse(code)
        validator = InvariantValidator()
        validator.visit(tree)
        is_valid = len(validator.violations) == 0
        return is_valid, validator.violations
    except SyntaxError as e:
        return False, [{'type': 'SYNTAX_ERROR', 'message': str(e), 'severity': 'CRITICAL'}]

if __name__ == "__main__":
    import sys
    if len(sys.argv) > 1:
        with open(sys.argv[1], 'r') as f:
            code = f.read()
        valid, violations = validate_module(code)
        print(f"VALID: {valid}")
        for v in violations:
            print(f"  [{v['severity']}] {v['type']}: {v}")
        sys.exit(0 if valid else 1)