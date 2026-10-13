#!/usr/bin/env python3
import ast
import sys
from typing import Dict, List, Set, Optional, Tuple

class InvariantValidator(ast.NodeVisitor):
    def __init__(self):
        self.violations: List[Tuple[int, str]] = []
        self.loop_invariants: Dict[int, List[str]] = {}
        self.preconditions: Dict[int, List[str]] = {}
        self.postconditions: Dict[int, List[str]] = {}
        
    def extract_assertion(self, node: ast.Assert) -> Optional[str]:
        """Extract assertion text for invariant checking"""
        try:
            return ast.unparse(node.test)
        except:
            return None
    
    def visit_While(self, node: ast.While):
        """Validate while loops have explicit invariants"""
        lineno = node.lineno
        invariants = []
        precond = []
        
        # Check for preceding assertions as preconditions
        # Check loop body for invariant assertions
        for stmt in node.body:
            if isinstance(stmt, ast.Assert):
                inv = self.extract_assertion(stmt)
                if inv and "invariant" in ast.unparse(stmt).lower():
                    invariants.append(inv)
        
        if not invariants:
            self.violations.append((lineno, "While loop lacks explicit invariant"))
        else:
            self.loop_invariants[lineno] = invariants
            
        self.generic_visit(node)
    
    def visit_For(self, node: ast.For):
        """Validate for loops maintain range invariants"""
        lineno = node.lineno
        invariants = []
        
        for stmt in node.body:
            if isinstance(stmt, ast.Assert):
                inv = self.extract_assertion(stmt)
                if inv:
                    invariants.append(inv)
        
        # For loops should have bound invariants
        if not invariants:
            self.violations.append((lineno, "For loop lacks bound invariant"))
        else:
            self.loop_invariants[lineno] = invariants
            
        self.generic_visit(node)

def validate_module(source_code: str) -> Dict:
    """Validate loop invariants in Python module"""
    try:
        tree = ast.parse(source_code)
    except SyntaxError as e:
        return {"valid": False, "error": str(e)}
    
    validator = InvariantValidator()
    validator.visit(tree)
    
    return {
        "valid": len(validator.violations) == 0,
        "violations": validator.violations,
        "invariants": validator.loop_invariants,
        "total_loops": len(validator.loop_invariants) + len(validator.violations)
    }

if __name__ == "__main__":
    source = sys.stdin.read() if len(sys.argv) == 1 else open(sys.argv[1]).read()
    result = validate_module(source)
    print(f"Valid: {result['valid']}")
    for lineno, msg in result.get('violations', []):
        print(f"Line {lineno}: {msg}")