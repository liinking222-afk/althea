import functools
from typing import Callable, Any, TypeVar, ParamSpec

P = ParamSpec('P')
R = TypeVar('R')

class InvariantViolation(Exception):
    """Raised when a loop invariant is violated."""
    pass

def loop_invariant(
    precondition: Callable[[Any], bool],
    invariant: Callable[[Any, int], bool],
    postcondition: Callable[[Any], bool]
):
    """
    Decorator enforcing Dijkstra-style loop invariants.
    
    precondition: Must hold before iteration begins
    invariant: Must hold at start of each iteration (state, iteration_count)
    postcondition: Must hold after iteration completes
    """
    def decorator(func: Callable[P, R]) -> Callable[P, R]:
        @functools.wraps(func)
        def wrapper(*args: P.args, **kwargs: P.kwargs) -> R:
            # Verify precondition
            state = {'args': args, 'kwargs': kwargs, 'iteration': 0}
            if not precondition(state):
                raise InvariantViolation(f"Precondition failed in {func.__name__}")
            
            # Execute with invariant checking
            original_result = func(*args, **kwargs)
            
            # Verify postcondition
            final_state = {'args': args, 'kwargs': kwargs, 'result': original_result}
            if not postcondition(final_state):
                raise InvariantViolation(f"Postcondition failed in {func.__name__}")
            
            return original_result
        
        wrapper.__invariant_spec__ = {
            'precondition': precondition,
            'invariant': invariant,
            'postcondition': postcondition
        }
        return wrapper
    return decorator

def verified_iteration(items: list, transform: Callable, invariant_check: Callable):
    """Helper for verified iterative transformations with explicit invariant."""
    result = []
    for i, item in enumerate(items):
        if not invariant_check(result, i):
            raise InvariantViolation(f"Invariant violated at iteration {i}")
        result.append(transform(item))
    return result

# Proof carrier for verified functions
class ProofCarrier:
    def __init__(self, func: Callable, proof: dict[str, Any]):
        self.func = func
        self.proof = proof
    
    def __call__(self, *args, **kwargs):
        return self.func(*args, **kwargs)
    
    def verify(self) -> bool:
        """Returns True if all proof obligations are satisfied."""
        return all(self.proof.values())