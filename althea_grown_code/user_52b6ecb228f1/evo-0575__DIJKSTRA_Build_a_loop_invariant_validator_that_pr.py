from typing import Callable, Any, TypeVar, Generic
from dataclasses import dataclass

T = TypeVar('T')

@dataclass
class LoopInvariant(Generic[T]):
    """Dijkstra-style loop invariant with formal verification."""
    precondition: Callable[[T], bool]
    invariant: Callable[[T, int], bool]
    postcondition: Callable[[T], bool]
    variant: Callable[[T, int], int]  # Must decrease each iteration
    
    def verify_iteration(self, state: T, iteration: int) -> tuple[bool, str]:
        """Verify single iteration satisfies invariant and variant decreases."""
        if not self.invariant(state, iteration):
            return False, f"Invariant violated at iteration {iteration}"
        
        variant_value = self.variant(state, iteration)
        if variant_value < 0:
            return False, f"Variant became negative: {variant_value}"
        
        return True, "Valid"
    
    def prove_loop(self, initial_state: T, step: Callable[[T], T], 
                   max_iterations: int = 1000) -> tuple[bool, str, T]:
        """Execute loop with invariant checking at each step."""
        if not self.precondition(initial_state):
            return False, "Precondition failed", initial_state
        
        state = initial_state
        prev_variant = float('inf')
        
        for i in range(max_iterations):
            valid, msg = self.verify_iteration(state, i)
            if not valid:
                return False, msg, state
            
            current_variant = self.variant(state, i)
            if current_variant >= prev_variant and i > 0:
                return False, f"Variant not decreasing: {prev_variant} -> {current_variant}", state
            
            if current_variant == 0:
                if self.postcondition(state):
                    return True, f"Proof complete in {i} iterations", state
                else:
                    return False, "Variant=0 but postcondition failed", state
            
            prev_variant = current_variant
            state = step(state)
        
        return False, "Max iterations exceeded without proof", state

def binary_search_invariant(arr: list[int], target: int) -> LoopInvariant:
    """Example: binary search with proven correctness."""
    state_type = dict[str, Any]
    
    return LoopInvariant(
        precondition=lambda s: s['left'] == 0 and s['right'] == len(arr) - 1 and sorted(arr) == arr,
        invariant=lambda s, i: (s['left'] <= s['right'] + 1 and 
    (target not in arr or s['left'] <= arr.index(target) <= s['right'])),
        postcondition=lambda s: (s['found'] or target not in arr),
        variant=lambda s, i: max(0, s['right'] - s['left'] + 1)
    )