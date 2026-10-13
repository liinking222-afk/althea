#!/usr/bin/env python3
"""Loop Invariant Validator - Dijkstra-inspired correctness checker."""

from typing import Callable, Any, TypeVar, List
from dataclasses import dataclass

T = TypeVar('T')

@dataclass(frozen=True)
class LoopContract:
    """Immutable contract defining loop correctness conditions."""
    precondition: Callable[[Any], bool]
    postcondition: Callable[[Any], bool]
    invariant: Callable[[Any, int], bool]
    variant: Callable[[Any, int], int]  # Must decrease each iteration

class InvariantViolation(Exception):
    """Raised when a loop contract is violated."""
    pass

def validated_loop(
    initial_state: T,
    iteration_fn: Callable[[T, int], T],
    contract: LoopContract,
    max_iterations: int
) -> T:
    """Execute loop with rigorous invariant checking at each step."""
    
    # Verify precondition holds
    if not contract.precondition(initial_state):
        raise InvariantViolation("Precondition violated")
    
    state = initial_state
    iteration = 0
    prev_variant = contract.variant(state, iteration)
    
    while iteration < max_iterations:
        # Check invariant holds before iteration
        if not contract.invariant(state, iteration):
            raise InvariantViolation(f"Invariant violated at iteration {iteration}")
        
        # Perform state transformation
        new_state = iteration_fn(state, iteration)
        iteration += 1
        
        # Verify variant decreases (ensures termination)
        current_variant = contract.variant(new_state, iteration)
        if current_variant >= prev_variant:
            raise InvariantViolation(
                f"Variant must decrease: {prev_variant} -> {current_variant}"
            )
        
        # Check invariant holds after iteration
        if not contract.invariant(new_state, iteration):
            raise InvariantViolation(f"Invariant violated after iteration {iteration}")
        
        prev_variant = current_variant
        state = new_state
        
        # Check if we can terminate early
        if contract.postcondition(state):
            break
    
    # Verify postcondition holds
    if not contract.postcondition(state):
        raise InvariantViolation("Postcondition violated")
    
    return state

# Export interface
__all__ = ['LoopContract', 'InvariantViolation', 'validated_loop']