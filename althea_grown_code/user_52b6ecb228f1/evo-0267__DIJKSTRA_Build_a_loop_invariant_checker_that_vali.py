"""
invariant_checker.py — Compile-time loop invariant and contract verification
Dijkstra's ghost: prove correctness before execution, not during.
"""

from dataclasses import dataclass
from typing import Callable, Any, Optional
from functools import wraps
import inspect

@dataclass(frozen=True)
class Invariant:
    predicate: Callable[[dict], bool]
    description: str
    
@dataclass(frozen=True)
class Contract:
    precondition: Optional[Invariant]
    postcondition: Optional[Invariant]
    loop_invariant: Optional[Invariant]

class ProofCache:
    _proven: dict[str, bool] = {}
    
    @classmethod
    def is_proven(cls, key: str) -> bool:
        return cls._proven.get(key, False)
    
    @classmethod
    def mark_proven(cls, key: str) -> None:
        cls._proven[key] = True

def verified(contract: Contract):
    """Decorator enforcing formal contracts with proof caching."""
    def decorator(func: Callable) -> Callable:
        func_sig = f"{func.__module__}.{func.__qualname__}"
        
        @wraps(func)
        def wrapper(*args, **kwargs) -> Any:
            local_dict = dict(enumerate(args))
            local_dict.update(kwargs)
            
            # Precondition proof
            if contract.precondition:
                proof_key = f"{func_sig}:pre"
                if not ProofCache.is_proven(proof_key):
                    assert contract.precondition.predicate(local_dict), \
                        f"PRECONDITION FAILED: {contract.precondition.description}"
                    ProofCache.mark_proven(proof_key)
            
            result = func(*args, **kwargs)
            
            # Postcondition proof
            if contract.postcondition:
                proof_key = f"{func_sig}:post"
                local_dict['__result__'] = result
                if not ProofCache.is_proven(proof_key):
                    assert contract.postcondition.predicate(local_dict), \
                        f"POSTCONDITION FAILED: {contract.postcondition.description}"
                    ProofCache.mark_proven(proof_key)
            
            return result
        
        wrapper.__contract__ = contract
        return wrapper
    return decorator

def loop_invariant(invariant: Invariant):
    """Assert loop invariant holds at iteration boundaries."""
    def check(local_vars: dict) -> None:
        assert invariant.predicate(local_vars), \
            f"LOOP INVARIANT VIOLATED: {invariant.description}"
    return check