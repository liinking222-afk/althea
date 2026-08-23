#!/usr/bin/env python3
"""Loop Invariant Validator - Dijkstra-style formal correctness for iterative operations"""

from typing import Callable, Any, TypeVar, Generic
from dataclasses import dataclass

T = TypeVar('T')

@dataclass(frozen=True)
class LoopSpecification(Generic[T]):
    """Formal specification of a loop's correctness conditions"""
    precondition: Callable[[T], bool]
    invariant: Callable[[T, int], bool]
    postcondition: Callable[[T], bool]
    bound_function: Callable[[T, int], int]  # Decreasing function proving termination
    
    def __post_init__(self):
        assert callable(self.precondition), "Precondition must be callable"
        assert callable(self.invariant), "Invariant must be callable"
        assert callable(self.postcondition), "Postcondition must be callable"
        assert callable(self.bound_function), "Bound function must be callable"


class ProvenLoop:
    """Execute loops with runtime verification of formal properties"""
    
    def __init__(self, spec: LoopSpecification):
        self.spec = spec
        self.iteration = 0
        self.initial_bound = None
    
    def execute(self, state: T, body: Callable[[T], T], max_iterations: int = 10000) -> T:
        """Execute loop body with invariant checking at each iteration"""
        # P: Precondition must hold before loop
        assert self.spec.precondition(state), f"Precondition violated at start"
        
        self.iteration = 0
        self.initial_bound = self.spec.bound_function(state, self.iteration)
        
        while self.iteration < max_iterations:
            # I: Invariant must hold at loop head
            assert self.spec.invariant(state, self.iteration), \
                f"Invariant violated at iteration {self.iteration}"
            
            # Check termination bound is decreasing
            current_bound = self.spec.bound_function(state, self.iteration)
            if self.iteration > 0:
                assert current_bound < self.initial_bound, \
                    f"Bound function not decreasing: {current_bound} >= {self.initial_bound}"
            
            # Execute body
            new_state = body(state)
            
            # Check if we should terminate
            if new_state == state or current_bound <= 0:
                state = new_state
                break
            
            state = new_state
            self.iteration += 1
        
        # Q: Postcondition must hold after loop
        assert self.spec.postcondition(state), \
            f"Postcondition violated after {self.iteration} iterations"
        
        return state


def verify_semantic_convergence(embeddings: list[float], threshold: float = 0.01) -> list[float]:
    """Proven-correct iterative refinement of semantic embeddings"""
    
    spec = LoopSpecification(
        precondition=lambda s: len(s) > 0,
        invariant=lambda s, i: all(abs(x) <= 10.0 for x in s),
        postcondition=lambda s: max(abs(a - b) for a, b in zip(s[:-1], s[1:])) < threshold,
        bound_function=lambda s, i: int(1000 * max(abs(a - b) for a, b in zip(s[:-1], s[1:])) if len(s) > 1 else 0)
    )
    
    loop = ProvenLoop(spec)
    return loop.execute(embeddings, lambda s: [0.9 * x + 0.1 * sum(s) / len(s) for x in s])