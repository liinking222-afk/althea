#!/usr/bin/env python3
"""Loop Invariant Validator - Dijkstra-style formal correctness for cognitive operations"""

from typing import Callable, Any, Dict, Optional
from dataclasses import dataclass
from functools import wraps

@dataclass(frozen=True)
class Invariant:
    predicate: Callable[[Dict[str, Any]], bool]
    description: str
    
class InvariantViolation(Exception):
    pass

class LoopInvariantValidator:
    def __init__(self):
        self.active_invariants: Dict[str, list[Invariant]] = {}
        self.violation_log: list[str] = []
        
    def register(self, scope: str, predicate: Callable, description: str) -> None:
        """Register an invariant for a given scope with a predicate function."""
        if scope not in self.active_invariants:
            self.active_invariants[scope] = []
        self.active_invariants[scope].append(Invariant(predicate, description))
        
    def validate(self, scope: str, state: Dict[str, Any], phase: str = "runtime") -> bool:
        """Check all invariants for a scope against current state."""
        if scope not in self.active_invariants:
            return True
            
        for inv in self.active_invariants[scope]:
            if not inv.predicate(state):
                msg = f"[{phase}] Invariant violated in '{scope}': {inv.description}"
                self.violation_log.append(msg)
                raise InvariantViolation(msg)
        return True
        
    def enforce(self, scope: str):
        """Decorator that enforces invariants before and after function execution."""
        def decorator(func: Callable) -> Callable:
            @wraps(func)
            def wrapper(*args, **kwargs) -> Any:
                # Build state dictionary from function arguments
                state = {"args": args, "kwargs": kwargs}
                
                # Validate precondition
                self.validate(scope, state, phase="precondition")
                
                # Execute operation
                result = func(*args, **kwargs)
                
                # Validate postcondition with result
                state["result"] = result
                self.validate(scope, state, phase="postcondition")
                
                return result
            return wrapper
        return decorator
    
    def clear_scope(self, scope: str) -> None:
        """Remove all invariants for a scope."""
        if scope in self.active_invariants:
            del self.active_invariants[scope]
            
    def get_violations(self) -> list[str]:
        """Return accumulated violation log."""
        return self.violation_log.copy()

# Global singleton instance
validator = LoopInvariantValidator()

# Example usage pattern
validator.register(
    "semantic_distance",
    lambda s: "args" in s and len(s["args"]) >= 2,
    "requires at least two semantic vectors"
)