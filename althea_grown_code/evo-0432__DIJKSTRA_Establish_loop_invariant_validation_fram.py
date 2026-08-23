"""
Loop Invariant Validator - Dijkstra formal correctness module
Validates that loop invariants hold: initialization, maintenance, termination
"""

from typing import Callable, Any, TypeVar, List
from dataclasses import dataclass

T = TypeVar('T')

@dataclass
class Invariant:
    """Encapsulates a loop invariant predicate"""
    name: str
    predicate: Callable[[Any], bool]
    
class InvariantViolation(Exception):
    """Raised when loop invariant is violated"""
    pass

def validated_loop(
    initial_state: T,
    invariant: Invariant,
    condition: Callable[[T], bool],
    body: Callable[[T], T],
    max_iterations: int = 10000
) -> T:
    """
    Execute loop with formal invariant checking at each phase:
    1. Initialization: invariant(initial_state) must be True
    2. Maintenance: invariant holds before and after each iteration
    3. Termination: invariant holds at exit
    """
    # Phase 1: Initialization
    if not invariant.predicate(initial_state):
        raise InvariantViolation(
            f"Invariant '{invariant.name}' violated at initialization"
        )
    
    state = initial_state
    iterations = 0
    
    # Phase 2: Maintenance
    while condition(state):
        if iterations >= max_iterations:
            raise InvariantViolation(f"Loop exceeded {max_iterations} iterations")
        
        # Pre-condition check
        if not invariant.predicate(state):
            raise InvariantViolation(
                f"Invariant '{invariant.name}' violated before iteration {iterations}"
            )
        
        state = body(state)
        
        # Post-condition check
        if not invariant.predicate(state):
            raise InvariantViolation(
                f"Invariant '{invariant.name}' violated after iteration {iterations}"
            )
        
        iterations += 1
    
    # Phase 3: Termination
    if not invariant.predicate(state):
        raise InvariantViolation(
            f"Invariant '{invariant.name}' violated at termination"
        )
    
    return state

# Example: Validated accumulation with bounds invariant
def validated_accumulate(items: List[int]) -> int:
    inv = Invariant(
        "accumulator_bounds",
        lambda s: 0 <= s['sum'] <= sum(items) and 0 <= s['idx'] <= len(items)
    )
    return validated_loop(
        {'sum': 0, 'idx': 0},
        inv,
        lambda s: s['idx'] < len(items),
        lambda s: {'sum': s['sum'] + items[s['idx']], 'idx': s['idx'] + 1}
    )['sum']