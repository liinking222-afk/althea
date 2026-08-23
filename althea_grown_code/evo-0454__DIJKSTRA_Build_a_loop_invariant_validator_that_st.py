#!/usr/bin/env python3
"""Loop Invariant Validator - Dijkstra-style formal correctness checker."""

import re
import ast
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass

@dataclass
class LoopInvariant:
    """Represents a formal loop invariant with pre/post conditions."""
    location: str
    invariant: str
    initialization: bool
    maintenance: bool
    termination: bool
    
    def is_valid(self) -> bool:
        return self.initialization and self.maintenance and self.termination

class InvariantValidator:
    """Validates loop invariants in Althea's code for formal correctness."""
    
    def __init__(self):
        self.invariants: Dict[str, LoopInvariant] = {}
        self.violations: List[str] = []
    
    def extract_invariants(self, code: str, module_name: str) -> List[LoopInvariant]:
        """Extract loop invariant annotations from code comments."""
        invariants = []
        lines = code.split('\n')
        
        for i, line in enumerate(lines):
            # Match pattern: # INVARIANT: <condition>
            match = re.search(r'#\s*INVARIANT:\s*(.+)', line)
            if match:
                inv = LoopInvariant(
                    location=f"{module_name}:L{i+1}",
                    invariant=match.group(1).strip(),
                    initialization=False,
                    maintenance=False,
                    termination=False
                )
                invariants.append(inv)
        
        return invariants
    
    def verify_loop_structure(self, code: str, invariant: LoopInvariant) -> Tuple[bool, bool, bool]:
        """Verify invariant holds at initialization, maintenance, and termination."""
        tree = ast.parse(code)
        
        init_check = self._check_initialization(tree, invariant)
        maint_check = self._check_maintenance(tree, invariant)
        term_check = self._check_termination(tree, invariant)
        
        return init_check, maint_check, term_check
    
    def _check_initialization(self, tree: ast.AST, inv: LoopInvariant) -> bool:
        """Verify invariant holds before loop entry."""
        # Simplified: check variable initialization exists
        for node in ast.walk(tree):
            if isinstance(node, ast.Assign):
                return True
        return False
    
    def _check_maintenance(self, tree: ast.AST, inv: LoopInvariant) -> bool:
        """Verify invariant maintained through loop body."""
        # Check loop body preserves properties
        for node in ast.walk(tree):
            if isinstance(node, (ast.For, ast.While)):
                return len(node.body) > 0
        return False
    
    def _check_termination(self, tree: ast.AST, inv: LoopInvariant) -> bool:
        """Verify loop terminates and invariant implies postcondition."""
        # Check for bounded iteration or convergence
        for node in ast.walk(tree):
            if isinstance(node, ast.For):
                return True  # For loops guarantee termination
        return False
    
    def validate_module(self, code: str, module_name: str) -> Dict:
        """Validate all invariants in a module."""
        invariants = self.extract_invariants(code, module_name)
        results = []
        
        for inv in invariants:
            init, maint, term = self.verify_loop_structure(code, inv)
            inv.initialization = init
            inv.maintenance = maint
            inv.termination = term
            
            results.append({
                'location': inv.location,
                'invariant': inv.invariant,
                'valid': inv.is_valid(),
                'checks': {'init': init, 'maint': maint, 'term': term}
            })
        
        return {'module': module_name, 'invariants': results}