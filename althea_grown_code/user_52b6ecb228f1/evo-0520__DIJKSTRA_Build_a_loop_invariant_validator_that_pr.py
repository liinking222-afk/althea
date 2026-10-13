"""
Loop Invariant Validator - Dijkstra-style formal verification for iteration
"""

from typing import Callable, Any, Optional
from dataclasses import dataclass

@dataclass
class LoopInvariant:
    """Formal specification of loop properties"""
    predicate: Callable[[Any], bool]  # Must hold before, during, after
    variant: Callable[[Any], int]     # Must decrease each iteration (termination)
    name: str

class ProvenLoop:
    """A loop that cannot execute without proven invariants"""
    
    def __init__(self, invariant: LoopInvariant):
        self.invariant = invariant
        self.iteration = 0
        
    def verify_precondition(self, state: Any) -> None:
        """Invariant must hold before first iteration"""
        assert self.invariant.predicate(state), \
            f"Precondition failed for {self.invariant.name}"
    
    def verify_step(self, prev_state: Any, curr_state: Any) -> None:
        """Invariant preserved AND variant decreased"""
        assert self.invariant.predicate(curr_state), \
            f"Invariant {self.invariant.name} broken at iteration {self.iteration}"
        
        prev_variant = self.invariant.variant(prev_state)
        curr_variant = self.invariant.variant(curr_state)
        
        assert curr_variant < prev_variant, \
            f"Variant not decreasing: {prev_variant} -> {curr_variant} (no termination proof)"
        assert curr_variant >= 0, \
            f"Variant cannot be negative (termination bound violated)"
        
        self.iteration += 1
    
    def verify_postcondition(self, state: Any) -> None:
        """Invariant still holds after loop exit"""
        assert self.invariant.predicate(state), \
            f"Postcondition failed for {self.invariant.name}"

def proven_while(condition: Callable[[Any], bool], 
                 body: Callable[[Any], Any],
                 invariant: LoopInvariant,
                 initial_state: Any) -> Any:
    """Execute a while loop with formal correctness proof"""
    loop = ProvenLoop(invariant)
    loop.verify_precondition(initial_state)
    
    state = initial_state
    while condition(state):
        prev_state = state
        state = body(state)
        loop.verify_step(prev_state, state)
    
    loop.verify_postcondition(state)
    return state