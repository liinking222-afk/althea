"""
Loop Invariant Validator - Enforces Dijkstra-style formal correctness
Each loop must declare its invariant, precondition, and postcondition.
"""

from typing import Callable, Any, TypeVar, Optional
from dataclasses import dataclass
from functools import wraps

T = TypeVar('T')

@dataclass
class LoopContract:
    """Formal specification of a loop's correctness properties"""
    invariant: Callable[[Any], bool]
    precondition: Callable[[Any], bool]
    postcondition: Callable[[Any], bool]
    progress_measure: Optional[Callable[[Any], int]] = None

class InvariantViolation(Exception):
    """Raised when a loop invariant, pre-, or postcondition is violated"""
    pass

def validated_loop(contract: LoopContract):
    """Decorator enforcing formal loop correctness"""
    def decorator(loop_func: Callable[[T], T]) -> Callable[[T], T]:
        @wraps(loop_func)
        def wrapper(initial_state: T) -> T:
            # Check precondition
            if not contract.precondition(initial_state):
                raise InvariantViolation(f"Precondition violated in {loop_func.__name__}")
            
            # Check invariant holds initially
            if not contract.invariant(initial_state):
                raise InvariantViolation(f"Invariant false at start in {loop_func.__name__}")
            
            state = initial_state
            prev_measure = contract.progress_measure(state) if contract.progress_measure else None
            iteration = 0
            
            while True:
                new_state = loop_func(state)
                
                # Loop body returns None to signal termination
                if new_state is None:
                    break
                
                # Check invariant after each iteration
                if not contract.invariant(new_state):
                    raise InvariantViolation(
                        f"Invariant violated at iteration {iteration} in {loop_func.__name__}"
                    )
                
                # Check progress if measure provided
                if contract.progress_measure:
                    measure = contract.progress_measure(new_state)
                    if prev_measure is not None and measure >= prev_measure:
                        raise InvariantViolation(
                            f"Progress stalled at iteration {iteration} in {loop_func.__name__}"
                        )
                    prev_measure = measure
                
                state = new_state
                iteration += 1
            
            # Check postcondition
            if not contract.postcondition(state):
                raise InvariantViolation(f"Postcondition violated in {loop_func.__name__}")
            
            return state
        
        return wrapper
    return decorator