import functools
import inspect
from typing import Callable, Any, Dict, Optional
from dataclasses import dataclass

@dataclass
class Invariant:
    """Formal invariant specification with proof obligation."""
    name: str
    predicate: Callable[[Dict[str, Any]], bool]
    error_msg: str

class InvariantViolation(Exception):
    """Raised when a proven invariant is violated."""
    pass

def with_invariants(
    pre: Optional[list[Invariant]] = None,
    post: Optional[list[Invariant]] = None,
    loop_inv: Optional[Invariant] = None
):
    """
    Decorator enforcing formal correctness via invariant checking.
    Preconditions verified before execution.
    Postconditions verified after execution.
    Loop invariants must be manually asserted within iteration bodies.
    """
    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            # Construct verification context from arguments
            sig = inspect.signature(func)
            bound = sig.bind(*args, **kwargs)
            bound.apply_defaults()
            context = dict(bound.arguments)
            
            # Verify preconditions
            if pre:
                for inv in pre:
                    if not inv.predicate(context):
                        raise InvariantViolation(
                            f"Precondition '{inv.name}' failed: {inv.error_msg}"
                        )
            
            # Execute with loop invariant in closure
            if loop_inv:
                context['_assert_loop_invariant'] = lambda ctx: _check_inv(loop_inv, ctx)
            
            result = func(*args, **kwargs)
            
            # Verify postconditions
            if post:
                context['_result'] = result
                for inv in post:
                    if not inv.predicate(context):
                        raise InvariantViolation(
                            f"Postcondition '{inv.name}' failed: {inv.error_msg}"
                        )
            
            return result
        
        wrapper._invariants = {'pre': pre or [], 'post': post or [], 'loop': loop_inv}
        return wrapper
    return decorator

def _check_inv(inv: Invariant, ctx: Dict[str, Any]) -> None:
    """Assert loop invariant holds at iteration boundary."""
    if not inv.predicate(ctx):
        raise InvariantViolation(f"Loop invariant '{inv.name}' violated: {inv.error_msg}")

# Export for module system
__all__ = ['with_invariants', 'Invariant', 'InvariantViolation']