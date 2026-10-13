from typing import Callable, TypeVar, Any
from dataclasses import dataclass

T = TypeVar('T')

@dataclass
class LoopContract:
    """Dijkstra-style loop contract: invariant must hold before, during, after."""
    invariant: Callable[[Any], bool]
    precondition: Callable[[Any], bool]
    postcondition: Callable[[Any], bool]
    variant: Callable[[Any], int]  # Must decrease each iteration (termination proof)

class InvariantViolation(Exception):
    """Raised when loop invariant is violated."""
    pass

def verified_iteration(
    initial_state: T,
    contract: LoopContract,
    step: Callable[[T], T],
    max_iterations: int = 1000
) -> T:
    """
    Execute iterative transformation with formal verification.
    Dijkstra: 'Program correctness can and should be a mathematical concern.'
    """
    state = initial_state
    
    # PRE: Precondition must hold
    if not contract.precondition(state):
        raise InvariantViolation("Precondition violated at entry")
    
    # PRE: Invariant must hold initially
    if not contract.invariant(state):
        raise InvariantViolation("Invariant violated at initialization")
    
    iteration = 0
    prev_variant = contract.variant(state)
    
    # LOOP: Invariant preserved, variant decreases
    while iteration < max_iterations:
        if contract.variant(state) <= 0:
            break
            
        state = step(state)
        iteration += 1
        
        # INV: Check invariant holds after step
        if not contract.invariant(state):
            raise InvariantViolation(f"Invariant violated at iteration {iteration}")
        
        # VARIANT: Must strictly decrease (termination proof)
        current_variant = contract.variant(state)
        if current_variant >= prev_variant:
            raise InvariantViolation(f"Variant not decreasing: {prev_variant} -> {current_variant}")
        prev_variant = current_variant
    
    # POST: Postcondition must hold
    if not contract.postcondition(state):
        raise InvariantViolation("Postcondition violated at exit")
    
    return state