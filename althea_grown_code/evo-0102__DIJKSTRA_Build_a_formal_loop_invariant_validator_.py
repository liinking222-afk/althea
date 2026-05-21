"""
invariant_validator.py - Dijkstra-style loop invariant verification
Ensures correctness through formal contracts at iteration boundaries.
"""

from typing import Callable, Any, TypeVar, Generic
from dataclasses import dataclass

T = TypeVar('T')

@dataclass
class LoopContract(Generic[T]):
    """Formal specification of loop correctness properties."""
    precondition: Callable[[T], bool]
    invariant: Callable[[T, int], bool]
    postcondition: Callable[[T], bool]
    variant: Callable[[T, int], int]  # Must decrease to prove termination
    
class InvariantViolation(Exception):
    """Raised when a loop contract is violated."""
    pass

def verified_loop(
    initial_state: T,
    condition: Callable[[T, int], bool],
    body: Callable[[T, int], T],
    contract: LoopContract[T],
    max_iterations: int = 10000
) -> T:
    """
    Execute loop with Dijkstra-style verification at each boundary.
    
    Guarantees:
    - P ∧ B → {body} P  (invariant preserved)
    - P ∧ ¬B → Q         (invariant + termination → postcondition)
    - variant decreases monotonically (termination proof)
    """
    state = initial_state
    iteration = 0
    
    # Verify precondition: P₀
    if not contract.precondition(state):
        raise InvariantViolation(f"Precondition failed at initialization")
    
    # Verify initial invariant: P₀ → P
    if not contract.invariant(state, iteration):
        raise InvariantViolation(f"Invariant failed at iteration {iteration}")
    
    prev_variant = contract.variant(state, iteration)
    
    # Loop with boundary verification
    while condition(state, iteration) and iteration < max_iterations:
        iteration += 1
        
        # Execute loop body
        state = body(state, iteration)
        
        # Verify invariant holds: P
        if not contract.invariant(state, iteration):
            raise InvariantViolation(f"Invariant violated at iteration {iteration}")
        
        # Verify variant decreases (termination proof): V(n+1) < V(n)
        current_variant = contract.variant(state, iteration)
        if current_variant >= prev_variant:
            raise InvariantViolation(
                f"Variant must decrease: {prev_variant} → {current_variant}"
            )
        prev_variant = current_variant
    
    # Verify postcondition: P ∧ ¬B → Q
    if not contract.postcondition(state):
        raise InvariantViolation(f"Postcondition failed after {iteration} iterations")
    
    return state