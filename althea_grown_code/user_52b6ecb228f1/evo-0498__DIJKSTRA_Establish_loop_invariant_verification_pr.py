"""
Loop Invariant Verifier — Dijkstra-style formal correctness guards
Every loop shall declare its invariant. Every function its contract.
"""

from typing import Callable, Any, Optional
from functools import wraps
import inspect


class InvariantViolation(AssertionError):
    """Raised when a loop invariant or contract is violated."""
    pass


def loop_invariant(predicate: Callable[..., bool], context: str = ""):
    """Assert that predicate holds at loop entry, each iteration, and exit."""
    def check(**bindings):
        if not predicate(**bindings):
            frame = inspect.currentframe().f_back
            raise InvariantViolation(
                f"Loop invariant violated {context}\n"
                f"  at line {frame.f_lineno}\n"
                f"  bindings: {bindings}"
            )
    return check


def contract(pre: Optional[Callable] = None, post: Optional[Callable] = None):
    """Function contract: precondition and postcondition enforcement."""
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs):
            if pre is not None:
                sig = inspect.signature(func)
                bound = sig.bind(*args, **kwargs)
                bound.apply_defaults()
                if not pre(**bound.arguments):
                    raise InvariantViolation(
                        f"Precondition failed for {func.__name__}"
                    )
            
            result = func(*args, **kwargs)
            
            if post is not None:
                if not post(result):
                    raise InvariantViolation(
                        f"Postcondition failed for {func.__name__}"
                    )
            
            return result
        return wrapper
    return decorator


# Example usage demonstrating formal correctness
@contract(
    pre=lambda arr, target: len(arr) > 0,
    post=lambda result: result >= -1
)
def binary_search_verified(arr: list[int], target: int) -> int:
    """Binary search with loop invariant verification."""
    left, right = 0, len(arr) - 1
    
    # Invariant: if target exists, it's in arr[left:right+1]
    inv = loop_invariant(
        lambda l, r, a, t: l <= r + 1 and (t not in a or any(a[i] == t for i in range(max(0, l), min(len(a), r + 1)))),
        context="binary_search"
    )
    
    while left <= right:
        inv(l=left, r=right, a=arr, t=target)
        mid = (left + right) // 2
        if arr[mid] == target:
            return mid
        elif arr[mid] < target:
            left = mid + 1
        else:
            right = mid - 1
    
    inv(l=left, r=right, a=arr, t=target)
    return -1