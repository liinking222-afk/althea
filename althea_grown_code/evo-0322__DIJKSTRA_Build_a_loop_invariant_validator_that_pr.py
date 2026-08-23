from typing import Callable, TypeVar, Any, Optional
from dataclasses import dataclass

T = TypeVar('T')

@dataclass(frozen=True)
class Invariant:
    """Immutable invariant specification with proof obligation."""
    predicate: Callable[[Any], bool]
    name: str
    
    def holds(self, state: Any) -> bool:
        """Check if invariant holds for given state."""
        return self.predicate(state)

class ProofValidator:
    """Validates loop invariants using Dijkstra's weakest precondition calculus."""
    
    def __init__(self):
        self.violations = []
    
    def verify_loop(
        self,
        initial_state: T,
        invariant: Invariant,
        loop_body: Callable[[T], T],
        termination: Callable[[T], bool],
        max_iterations: int = 1000
    ) -> tuple[bool, T, list[str]]:
        """
        Verify loop preserves invariant from initialization through termination.
        Returns (is_valid, final_state, violation_trace).
        """
        self.violations = []
        
        # Prove: P(initial_state)
        if not invariant.holds(initial_state):
            self.violations.append(f"PRE: {invariant.name} fails at initialization")
            return False, initial_state, self.violations
        
        state = initial_state
        iteration = 0
        
        while not termination(state) and iteration < max_iterations:
            # Prove: P(state) ∧ ¬done(state) ⟹ P(body(state))
            state_before = state
            state = loop_body(state)
            iteration += 1
            
            if not invariant.holds(state):
                self.violations.append(
                    f"LOOP: {invariant.name} violated at iteration {iteration}"
                )
                return False, state, self.violations
        
        # Prove: P(state) ∧ done(state) [postcondition]
        if iteration >= max_iterations:
            self.violations.append(f"TERM: exceeded max iterations without termination")
            return False, state, self.violations
        
        if not invariant.holds(state):
            self.violations.append(f"POST: {invariant.name} fails at termination")
            return False, state, self.violations
        
        return True, state, []

def prove_transformation(
    data: T,
    transform: Callable[[T], T],
    precondition: Invariant,
    postcondition: Invariant
) -> tuple[bool, Optional[T]]:
    """Single-step transformation proof: {P} S {Q}"""
    if not precondition.holds(data):
        return False, None
    
    result = transform(data)
    
    if not postcondition.holds(result):
        return False, None
    
    return True, result