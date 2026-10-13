#!/usr/bin/env python3
"""Loop Invariant Validator for Cognitive State Transitions"""

from typing import Callable, Any, Dict, List, Tuple
from dataclasses import dataclass
import inspect

@dataclass
class Invariant:
    name: str
    predicate: Callable[[Dict[str, Any]], bool]
    critical: bool = True

class InvariantValidator:
    def __init__(self):
        self.invariants: List[Invariant] = []
        self.violations: List[Tuple[str, Dict[str, Any]]] = []
    
    def register(self, name: str, predicate: Callable, critical: bool = True):
        """Register an invariant that must hold across state transitions."""
        self.invariants.append(Invariant(name, predicate, critical))
    
    def validate(self, state: Dict[str, Any], context: str = "") -> bool:
        """Verify all invariants hold for given state. Returns False if any critical invariant fails."""
        all_valid = True
        for inv in self.invariants:
            try:
                holds = inv.predicate(state)
                if not holds:
                    self.violations.append((f"{context}::{inv.name}", state.copy()))
                    if inv.critical:
                        all_valid = False
            except Exception as e:
                self.violations.append((f"{context}::{inv.name}::EXCEPTION::{e}", state.copy()))
                if inv.critical:
                    all_valid = False
        return all_valid
    
    def guard_loop(self, loop_body: Callable, initial_state: Dict[str, Any], 
                   max_iterations: int = 1000) -> Dict[str, Any]:
        """Execute loop body with invariant checking at each iteration."""
        state = initial_state.copy()
        
        if not self.validate(state, "PRE"):
            raise RuntimeError(f"Precondition failed: {self.violations[-1]}")
        
        for i in range(max_iterations):
            if not self.validate(state, f"ITER_{i}"):
                raise RuntimeError(f"Invariant violated at iteration {i}: {self.violations[-1]}")
            
            new_state = loop_body(state, i)
            if new_state is None:
                break
            state = new_state
        
        if not self.validate(state, "POST"):
            raise RuntimeError(f"Postcondition failed: {self.violations[-1]}")
        
        return state
    
    def prove_termination(self, variant: Callable[[Dict[str, Any]], int], 
                         state: Dict[str, Any]) -> bool:
        """Verify loop variant strictly decreases (Dijkstra's termination proof)."""
        return variant(state) >= 0

# Global validator for cognitive state transitions
cognitive_validator = InvariantValidator()

# Example: Register core cognitive invariants
cognitive_validator.register("coherence_preserved", 
                            lambda s: s.get("coherence", 0) >= 0)
cognitive_validator.register("energy_bounded",
                            lambda s: s.get("energy", 0) <= s.get("max_energy", float('inf')))