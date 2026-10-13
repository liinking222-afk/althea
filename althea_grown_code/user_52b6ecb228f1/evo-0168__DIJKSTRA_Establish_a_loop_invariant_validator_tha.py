#!/usr/bin/env python3
"""invariant_guardian.py - Formal correctness validation for pattern transformations"""

from dataclasses import dataclass
from typing import Callable, Any, Dict, Optional
from functools import wraps
import hashlib


@dataclass(frozen=True)
class Invariant:
    """Immutable specification of what must remain true."""
    name: str
    predicate: Callable[[Dict[str, Any]], bool]
    error_message: str


class InvariantGuardian:
    """Validates loop invariants and pre/postconditions for pattern operations."""
    
    def __init__(self):
        self._invariants: Dict[str, Invariant] = {}
        self._violation_log: list[tuple[str, str]] = []
    
    def register(self, invariant: Invariant) -> None:
        """Register an invariant to be checked. Pure registration."""
        self._invariants[invariant.name] = invariant
    
    def verify_state(self, state: Dict[str, Any], context: str = "") -> bool:
        """Check all registered invariants hold for given state."""
        all_valid = True
        for inv_name, inv in self._invariants.items():
            if not inv.predicate(state):
                violation = f"{context}:{inv_name}" if context else inv_name
                self._violation_log.append((violation, inv.error_message))
                all_valid = False
        return all_valid
    
    def guarded(self, 
                precondition: Optional[Callable[[Dict], bool]] = None,
                postcondition: Optional[Callable[[Dict, Any], bool]] = None):
        """Decorator ensuring pre/post conditions and invariants."""
        def decorator(func: Callable) -> Callable:
            @wraps(func)
            def wrapper(*args, **kwargs):
                # Extract state (assume first arg is self with .__dict__ or dict arg)
                state = args[0].__dict__ if args and hasattr(args[0], '__dict__') else {}
                
                if precondition and not precondition(state):
                    raise AssertionError(f"Precondition failed: {func.__name__}")
                
                self.verify_state(state, f"pre:{func.__name__}")
                
                result = func(*args, **kwargs)
                
                post_state = args[0].__dict__ if args and hasattr(args[0], '__dict__') else {}
                
                if postcondition and not postcondition(post_state, result):
                    raise AssertionError(f"Postcondition failed: {func.__name__}")
                
                self.verify_state(post_state, f"post:{func.__name__}")
                
                return result
            return wrapper
        return decorator
    
    def violations(self) -> list[tuple[str, str]]:
        """Return recorded violations. Does not mutate."""
        return self._violation_log.copy()


# Singleton instance
guardian = InvariantGuardian()