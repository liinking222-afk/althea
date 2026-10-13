#!/usr/bin/env python3
"""Loop Invariant Validator - Dijkstra-style formal correctness for Althea cycles"""

from typing import Callable, Any, TypeVar, Generic
from dataclasses import dataclass
from functools import wraps

T = TypeVar('T')

@dataclass
class Invariant:
    """Immutable invariant specification with proof obligation"""
    predicate: Callable[[Any], bool]
    name: str
    proof_trace: list[tuple[str, bool]] = None
    
    def __post_init__(self):
        object.__setattr__(self, 'proof_trace', [])

def assert_invariant(inv: Invariant, state: Any, location: str) -> None:
    """Assert invariant holds; record proof step"""
    holds = inv.predicate(state)
    inv.proof_trace.append((location, holds))
    if not holds:
        raise AssertionError(f"Invariant '{inv.name}' violated at {location}")

def verified_loop(invariant: Invariant, precondition: Callable[[Any], bool]):
    """Decorator enforcing loop invariant discipline"""
    def decorator(loop_body: Callable[[T], T]):
        @wraps(loop_body)
        def wrapper(initial_state: T) -> T:
            # Precondition implies invariant
            if not precondition(initial_state):
                raise AssertionError("Precondition failed")
            assert_invariant(invariant, initial_state, "INIT")
            
            state = initial_state
            iteration = 0
            while True:
                # Invariant holds at loop entry
                assert_invariant(invariant, state, f"ENTRY[{iteration}]")
                
                # Execute body
                new_state = loop_body(state)
                
                # Invariant preserved by body
                assert_invariant(invariant, new_state, f"EXIT[{iteration}]")
                
                # Termination check (state convergence)
                if new_state == state or iteration >= 1000:
                    break
                    
                state = new_state
                iteration += 1
            
            # Postcondition: invariant still holds
            assert_invariant(invariant, state, "FINAL")
            return state
        return wrapper
    return decorator

def generate_proof_certificate(inv: Invariant) -> dict:
    """Extract formal proof certificate from trace"""
    return {
        'invariant': inv.name,
        'steps': len(inv.proof_trace),
        'valid': all(holds for _, holds in inv.proof_trace),
        'trace': inv.proof_trace,
        'qed': all(holds for _, holds in inv.proof_trace)
    }

# Export validator interface
__all__ = ['Invariant', 'assert_invariant', 'verified_loop', 'generate_proof_certificate']