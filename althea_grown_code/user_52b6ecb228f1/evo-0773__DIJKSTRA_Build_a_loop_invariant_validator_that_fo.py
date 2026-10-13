#!/usr/bin/env python3
"""Loop Invariant Validator - Dijkstra-style formal correctness for runtime loops."""

from typing import Callable, Any, Dict, List, Tuple
from dataclasses import dataclass
import inspect

@dataclass
class Invariant:
    """Formal specification of a loop invariant with proof obligations."""
    name: str
    predicate: Callable[[Dict[str, Any]], bool]
    proof_trace: List[str]

@dataclass
class LoopSpec:
    """Complete formal specification: precondition, invariant, postcondition, bound function."""
    precondition: Callable[[Dict[str, Any]], bool]
    invariant: Invariant
    postcondition: Callable[[Dict[str, Any]], bool]
    bound_function: Callable[[Dict[str, Any]], int]  # Must decrease each iteration
    
class InvariantValidator:
    """Validates loop correctness via Dijkstra's proof obligations."""
    
    def __init__(self):
        self.violations: List[Tuple[str, str, Dict[str, Any]]] = []
    
    def verify_loop(self, spec: LoopSpec, initial_state: Dict[str, Any], 
                   iteration_fn: Callable[[Dict[str, Any]], Dict[str, Any]],
                   termination_fn: Callable[[Dict[str, Any]], bool],
                   max_iterations: int = 1000) -> bool:
        """Execute loop with full invariant checking at each step."""
        
        # Proof obligation 1: Precondition implies invariant (initialization)
        if not spec.precondition(initial_state):
            self.violations.append(("PRECONDITION", "Initial state violates precondition", initial_state.copy()))
            return False
        
        if not spec.invariant.predicate(initial_state):
            self.violations.append(("INIT", "Precondition does not establish invariant", initial_state.copy()))
            return False
        
        spec.invariant.proof_trace.append(f"INIT: Invariant established")
        
        state = initial_state.copy()
        prev_bound = spec.bound_function(state)
        iteration = 0
        
        while not termination_fn(state) and iteration < max_iterations:
            # Proof obligation 2: Invariant + !termination => invariant after iteration
            if not spec.invariant.predicate(state):
                self.violations.append(("INVARIANT", f"Invariant violated at iteration {iteration}", state.copy()))
                return False
            
            prev_state = state.copy()
            state = iteration_fn(state)
            iteration += 1
            
            # Proof obligation 3: Bound function decreases (progress toward termination)
            current_bound = spec.bound_function(state)
            if current_bound >= prev_bound:
                self.violations.append(("BOUND", f"Bound function did not decrease: {prev_bound} -> {current_bound}", state.copy()))
                return False
            
            prev_bound = current_bound
            spec.invariant.proof_trace.append(f"ITER {iteration}: bound={current_bound}, invariant holds")
        
        # Proof obligation 4: Invariant + termination => postcondition
        if iteration >= max_iterations:
            self.violations.append(("TERMINATION", "Loop did not terminate within bound", state.copy()))
            return False
        
        if not spec.invariant.predicate(state):
            self.violations.append(("FINAL_INV", "Invariant violated at termination", state.copy()))
            return False
        
        if not spec.postcondition(state):
            self.violations.append(("POSTCONDITION", "Postcondition not satisfied", state.copy()))
            return False
        
        spec.invariant.proof_trace.append(f"TERMINATION: Postcondition verified after {iteration} iterations")
        return True

# Singleton instance for Althea's formal verification layer
validator = InvariantValidator()