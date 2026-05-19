import functools
import inspect
from typing import Callable, Any, Optional
from dataclasses import dataclass

@dataclass
class Contract:
    precondition: Optional[Callable[..., bool]] = None
    postcondition: Optional[Callable[..., bool]] = None
    invariant: Optional[Callable[..., bool]] = None
    measure: Optional[Callable[..., int]] = None

class ContractViolation(Exception):
    pass

def verified(contract: Contract):
    """Decorator enforcing Hoare-style contracts with loop invariants."""
    def decorator(func: Callable) -> Callable:
        sig = inspect.signature(func)
        
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            bound = sig.bind(*args, **kwargs)
            bound.apply_defaults()
            
            # Precondition: P
            if contract.precondition:
                if not contract.precondition(**bound.arguments):
                    raise ContractViolation(
                        f"{func.__name__} precondition failed: {bound.arguments}"
                    )
            
            # Measure for termination (optional)
            measure_before = None
            if contract.measure:
                measure_before = contract.measure(**bound.arguments)
            
            # Execute: {P} S {Q}
            result = func(*args, **kwargs)
            
            # Postcondition: Q
            if contract.postcondition:
                post_args = {**bound.arguments, 'result': result}
                if not contract.postcondition(**post_args):
                    raise ContractViolation(
                        f"{func.__name__} postcondition failed: result={result}"
                    )
            
            # Measure decreased (termination proof)
            if contract.measure and measure_before is not None:
                measure_after = contract.measure(**bound.arguments)
                if measure_after >= measure_before:
                    raise ContractViolation(
                        f"{func.__name__} measure did not decrease: {measure_before} -> {measure_after}"
                    )
            
            return result
        
        wrapper.__contract__ = contract
        return wrapper
    return decorator

def check_invariant(condition: Callable[..., bool]):
    """Inline invariant assertion for loop bodies."""
    frame = inspect.currentframe().f_back
    local_vars = frame.f_locals
    if not condition(**local_vars):
        raise ContractViolation(f"Invariant violated in {frame.f_code.co_name}")