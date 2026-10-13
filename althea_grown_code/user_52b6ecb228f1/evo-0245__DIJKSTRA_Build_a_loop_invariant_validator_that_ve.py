#!/usr/bin/env python3
"""Loop Invariant Validator - Dijkstra-style formal correctness checker"""

from typing import Callable, Any, Dict, List, Tuple
from dataclasses import dataclass
import hashlib

@dataclass
class Invariant:
    name: str
    predicate: Callable[[Dict[str, Any]], bool]
    proof_obligation: str

class InvariantValidator:
    def __init__(self):
        self.violations: List[Tuple[str, Dict[str, Any]]] = []
        self.validated_iterations: int = 0
        
    def register_invariant(self, name: str, predicate: Callable, proof: str) -> Invariant:
        """Register a loop invariant with its formal proof obligation"""
        return Invariant(name=name, predicate=predicate, proof_obligation=proof)
    
    def validate_loop(self, 
                     invariants: List[Invariant],
                     initial_state: Dict[str, Any],
                     step_function: Callable[[Dict[str, Any]], Dict[str, Any]],
                     termination_predicate: Callable[[Dict[str, Any]], bool],
                     max_iterations: int = 1000) -> bool:
        """Execute loop with continuous invariant checking"""
        
        # Verify precondition: all invariants hold initially
        for inv in invariants:
            if not inv.predicate(initial_state):
                self.violations.append((f"PRECONDITION_{inv.name}", initial_state))
                return False
        
        state = initial_state.copy()
        iteration = 0
        
        while not termination_predicate(state) and iteration < max_iterations:
            # Record state hash for proof of transformation
            prev_hash = self._state_hash(state)
            
            # Execute one iteration
            state = step_function(state)
            iteration += 1
            
            # Verify all invariants hold after transformation
            for inv in invariants:
                if not inv.predicate(state):
                    self.violations.append((f"ITERATION_{iteration}_{inv.name}", state))
                    return False
            
            # Ensure actual state change occurred (liveness property)
            curr_hash = self._state_hash(state)
            if curr_hash == prev_hash and not termination_predicate(state):
                self.violations.append((f"DEADLOCK_{iteration}", state))
                return False
        
        self.validated_iterations += iteration
        
        # Verify postcondition: termination with invariants intact
        return termination_predicate(state) and all(
            inv.predicate(state) for inv in invariants
        )
    
    def _state_hash(self, state: Dict[str, Any]) -> str:
        """Compute deterministic hash of state for equivalence checking"""
        return hashlib.sha256(str(sorted(state.items())).encode()).hexdigest()
    
    def report(self) -> Dict[str, Any]:
        """Return formal validation report"""
        return {
            "validated_iterations": self.validated_iterations,
            "violations": self.violations,
            "is_sound": len(self.violations) == 0
        }