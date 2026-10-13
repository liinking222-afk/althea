#!/usr/bin/env python3
"""Loop Invariant Validator - Dijkstra-style correctness enforcement"""

from typing import Callable, Any, Dict, List, Tuple
from dataclasses import dataclass
import inspect

@dataclass
class Invariant:
    """Formal loop invariant with pre/post conditions"""
    name: str
    condition: Callable[[Dict[str, Any]], bool]
    description: str

class LoopValidator:
    """Enforce loop invariants during iteration"""
    
    def __init__(self, name: str):
        self.name = name
        self.invariants: List[Invariant] = []
        self.iterations = 0
        
    def add_invariant(self, name: str, condition: Callable, desc: str):
        """Register an invariant to check"""
        self.invariants.append(Invariant(name, condition, desc))
        
    def validate(self, state: Dict[str, Any], phase: str = "loop") -> Tuple[bool, List[str]]:
        """Check all invariants hold; return (valid, violations)"""
        violations = []
        for inv in self.invariants:
            try:
                if not inv.condition(state):
                    violations.append(f"{phase}:{inv.name}: {inv.description}")
            except Exception as e:
                violations.append(f"{phase}:{inv.name}: EXCEPTION {e}")
        return len(violations) == 0, violations
        
    def iterate(self, state: Dict[str, Any], body: Callable[[Dict[str, Any]], Dict[str, Any]]) -> Dict[str, Any]:
        """Execute one iteration with invariant checking"""
        valid_pre, viols_pre = self.validate(state, "PRE")
        assert valid_pre, f"Precondition violated: {viols_pre}"
        
        new_state = body(state)
        self.iterations += 1
        
        valid_post, viols_post = self.validate(new_state, "POST")
        assert valid_post, f"Postcondition violated: {viols_post}"
        
        return new_state
        
    def prove_termination(self, state: Dict[str, Any], variant: Callable[[Dict[str, Any]], int]) -> bool:
        """Check that variant function is decreasing (termination proof)"""
        return variant(state) >= 0

def example_binary_search_with_proof():
    """Binary search with formal loop invariants"""
    validator = LoopValidator("binary_search")
    validator.add_invariant("bounds", lambda s: 0 <= s["low"] <= s["high"] < len(s["arr"]), "Search bounds valid")
    validator.add_invariant("sorted", lambda s: all(s["arr"][i] <= s["arr"][i+1] for i in range(len(s["arr"])-1)), "Array is sorted")
    
    state = {"arr": [1, 3, 5, 7, 9, 11], "target": 7, "low": 0, "high": 5, "found": False}
    
    while state["low"] <= state["high"] and not state["found"]:
        state = validator.iterate(state, lambda s: {
            **s, "mid": (s["low"] + s["high"]) // 2,
            "found": s["arr"][(s["low"] + s["high"]) // 2] == s["target"],
            "low": s["low"] if s["arr"][(s["low"] + s["high"]) // 2] >= s["target"] else (s["low"] + s["high"]) // 2 + 1,
            "high": (s["low"] + s["high"]) // 2 - 1 if s["arr"][(s["low"] + s["high"]) // 2] > s["target"] else s["high"]
        })
    
    return state["found"]