"""
Loop Invariant Validator - Dijkstra-style formal correctness for state mutations
Every state transition must prove its invariants hold before and after.
"""

from typing import Callable, Any, TypeVar, Generic
from dataclasses import dataclass
from functools import wraps

T = TypeVar('T')

@dataclass(frozen=True)
class Invariant:
    """An invariant is a predicate that must hold at designated program points."""
    name: str
    predicate: Callable[[Any], bool]
    
    def check(self, state: Any) -> bool:
        """Verify invariant holds. Raise if violated."""
        holds = self.predicate(state)
        if not holds:
            raise InvariantViolation(f"INVARIANT VIOLATED: {self.name}")
        return True

class InvariantViolation(Exception):
    """Formal proof failure - invariant does not hold."""
    pass

class ProvenLoop(Generic[T]):
    """A loop construct with provable invariants."""
    
    def __init__(self, state: T, invariants: list[Invariant]):
        self.state = state
        self.invariants = invariants
        self._verify_all()
    
    def _verify_all(self):
        """Check all invariants hold."""
        for inv in self.invariants:
            inv.check(self.state)
    
    def iterate(self, transform: Callable[[T], T], guard: Callable[[T], bool]) -> T:
        """Execute loop body with invariant preservation proof."""
        self._verify_all()  # Precondition: invariants hold
        
        iteration = 0
        while guard(self.state):
            old_state = self.state
            self.state = transform(self.state)
            
            # Prove invariants preserved across iteration
            self._verify_all()
            
            # Termination metric (prevent infinite loops in proof)
            iteration += 1
            if iteration > 100000:
                raise InvariantViolation("Loop termination not proven (exceeded bound)")
        
        self._verify_all()  # Postcondition: invariants still hold
        return self.state

def proven_mutation(invariants: list[Invariant]):
    """Decorator ensuring function preserves stated invariants."""
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(state: Any, *args, **kwargs) -> Any:
            # Verify precondition
            for inv in invariants:
                inv.check(state)
            
            # Execute mutation
            result = func(state, *args, **kwargs)
            
            # Verify postcondition
            for inv in invariants:
                inv.check(result if result is not None else state)
            
            return result
        return wrapper
    return decorator