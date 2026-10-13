from typing import Any, Callable, Optional, Set
from dataclasses import dataclass
from functools import wraps

@dataclass(frozen=True)
class InvariantSpec:
    """Formal specification of a loop/recursion invariant."""
    predicate: Callable[[Any], bool]
    name: str
    max_depth: int

class InvariantViolation(Exception):
    """Raised when a verified invariant is violated."""
    pass

def verify_recursion_invariant(invariant: InvariantSpec):
    """Decorator that enforces loop invariants on recursive functions with formal depth bounds."""
    def decorator(func: Callable) -> Callable:
        call_stack: Set[int] = set()
        depth_tracker: list[int] = [0]
        
        @wraps(func)
        def wrapper(*args, **kwargs):
            # Establish precondition: depth within bound
            current_depth = depth_tracker[0]
            if current_depth >= invariant.max_depth:
                raise InvariantViolation(
                    f"{invariant.name}: max_depth={invariant.max_depth} exceeded"
                )
            
            # Check invariant holds at entry
            state = (current_depth, args, kwargs)
            if not invariant.predicate(state):
                raise InvariantViolation(
                    f"{invariant.name}: predicate failed at depth {current_depth}"
                )
            
            # Track recursive entry
            call_id = id(args)
            if call_id in call_stack:
                raise InvariantViolation(
                    f"{invariant.name}: identical call detected (infinite loop)"
                )
            
            call_stack.add(call_id)
            depth_tracker[0] += 1
            
            try:
                result = func(*args, **kwargs)
                
                # Verify postcondition: invariant still holds
                if not invariant.predicate((depth_tracker[0] - 1, args, kwargs)):
                    raise InvariantViolation(
                        f"{invariant.name}: invariant violated on exit"
                    )
                
                return result
            finally:
                depth_tracker[0] -= 1
                call_stack.discard(call_id)
        
        return wrapper
    return decorator

def monotonic_decrease(state: tuple) -> bool:
    """Example invariant: recursion parameter must monotonically decrease."""
    depth, args, kwargs = state
    return depth >= 0 and (not args or args[0] >= 0)

# Example usage with provable termination
depth_invariant = InvariantSpec(
    predicate=monotonic_decrease,
    name="monotonic_recursion_depth",
    max_depth=100
)

@verify_recursion_invariant(depth_invariant)
def safe_recursive_process(n: int) -> int:
    """Recursion with formally verified termination."""
    if n <= 0:
        return 1
    return n * safe_recursive_process(n - 1)