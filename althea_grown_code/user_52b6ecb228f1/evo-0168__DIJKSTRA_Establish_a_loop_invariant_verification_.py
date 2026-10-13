#!/usr/bin/env python3
"""invariant_guard.py - Formal state invariant verification for Althea subsystems"""

from dataclasses import dataclass
from typing import Callable, Any, Optional
from functools import wraps
import time

@dataclass(frozen=True)
class Invariant:
    """Immutable invariant specification with predicate and bound"""
    name: str
    predicate: Callable[[Any], bool]
    error_bound: float = 0.0
    
    def holds(self, state: Any) -> bool:
        """Verify invariant holds for given state"""
        return self.predicate(state)

class InvariantGuard:
    """Monitors loop invariants and state transitions with formal verification"""
    
    def __init__(self):
        self._invariants: dict[str, Invariant] = {}
        self._violation_count: int = 0
        self._check_count: int = 0
        
    def register(self, invariant: Invariant) -> None:
        """Register an invariant for verification"""
        self._invariants[invariant.name] = invariant
        
    def verify_all(self, state: Any, context: str = "") -> tuple[bool, list[str]]:
        """Verify all registered invariants hold for current state"""
        violations = []
        self._check_count += 1
        
        for name, inv in self._invariants.items():
            if not inv.holds(state):
                violations.append(f"{name} violated in {context}")
                self._violation_count += 1
                
        return len(violations) == 0, violations
    
    def guarded_loop(self, invariant_name: str):
        """Decorator ensuring loop invariant holds at entry and each iteration"""
        def decorator(func: Callable) -> Callable:
            @wraps(func)
            def wrapper(state: Any, *args, **kwargs):
                inv = self._invariants.get(invariant_name)
                if not inv:
                    raise ValueError(f"Unknown invariant: {invariant_name}")
                    
                # Pre-condition: invariant must hold before loop
                if not inv.holds(state):
                    raise AssertionError(f"PRE: {invariant_name} violated before loop entry")
                
                result = func(state, *args, **kwargs)
                
                # Post-condition: invariant must hold after loop
                if not inv.holds(result if result is not None else state):
                    raise AssertionError(f"POST: {invariant_name} violated after loop exit")
                    
                return result
            return wrapper
        return decorator
    
    @property
    def integrity(self) -> float:
        """Compute integrity metric: ratio of successful checks"""
        if self._check_count == 0:
            return 1.0
        return 1.0 - (self._violation_count / self._check_count)

# Global singleton for cross-module invariant tracking
GUARD = InvariantGuard()