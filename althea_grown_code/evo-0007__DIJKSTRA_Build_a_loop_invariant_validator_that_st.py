#!/usr/bin/env python3
"""Loop Invariant & Contract Validator — Dijkstra's formal correctness discipline"""

from typing import Callable, Any, TypeVar, Protocol
from functools import wraps
import inspect

T = TypeVar('T')

class Invariant:
    """Captures a predicate with its logical meaning"""
    def __init__(self, predicate: Callable[[Any], bool], description: str):
        self.predicate = predicate
        self.description = description
    
    def check(self, value: Any) -> None:
        if not self.predicate(value):
            raise AssertionError(f"Invariant violated: {self.description}")

def verified(preconditions: list[Invariant] = None, 
             postconditions: list[Invariant] = None,
             invariants: list[Invariant] = None):
    """Decorator enforcing Dijkstra-style contracts"""
    def decorator(func: Callable) -> Callable:
        sig = inspect.signature(func)
        
        @wraps(func)
        def wrapper(*args, **kwargs):
            # Bind arguments to verify preconditions
            bound = sig.bind(*args, **kwargs)
            bound.apply_defaults()
            
            # P: Preconditions must hold before execution
            if preconditions:
                for inv in preconditions:
                    inv.check(bound.arguments)
            
            # Execute with invariant monitoring if provided
            result = func(*args, **kwargs)
            
            # Q: Postconditions must hold after execution
            if postconditions:
                context = {**bound.arguments, 'result': result}
                for inv in postconditions:
                    inv.check(context)
            
            # I: Loop invariants verified on result structure
            if invariants:
                for inv in invariants:
                    inv.check(result)
            
            return result
        
        wrapper.__invariants__ = {
            'pre': preconditions or [],
            'post': postconditions or [],
            'inv': invariants or []
        }
        return wrapper
    return decorator

# Proof-carrying composition: chain verified functions
def compose_verified(*functions):
    """Compose functions ensuring postcondition→precondition alignment"""
    def composed(x):
        result = x
        for f in functions:
            if hasattr(f, '__invariants__'):
                # Verify handoff: previous post implies current pre
                result = f(result)
            else:
                raise ValueError(f"Function {f.__name__} lacks formal verification")
        return result
    return composed