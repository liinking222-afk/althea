import inspect
from typing import Callable, Any, Dict, List, Optional
from dataclasses import dataclass
from functools import wraps

@dataclass
class Invariant:
    predicate: Callable
    description: str
    violation_count: int = 0

class InvariantChecker:
    def __init__(self):
        self.invariants: Dict[str, List[Invariant]] = {}
        self.active = True
    
    def register(self, module: str, invariant: Callable, desc: str):
        if module not in self.invariants:
            self.invariants[module] = []
        self.invariants[module].append(Invariant(invariant, desc))
    
    def verify(self, module: str, context: Dict[str, Any]) -> Optional[str]:
        if not self.active or module not in self.invariants:
            return None
        for inv in self.invariants[module]:
            if not inv.predicate(context):
                inv.violation_count += 1
                return f"VIOLATION [{module}]: {inv.description}"
        return None
    
    def precondition(self, **constraints):
        def decorator(func):
            @wraps(func)
            def wrapper(*args, **kwargs):
                sig = inspect.signature(func)
                bound = sig.bind(*args, **kwargs)
                bound.apply_defaults()
                ctx = dict(bound.arguments)
                for name, pred in constraints.items():
                    if name in ctx and not pred(ctx[name]):
                        raise AssertionError(f"Precondition failed: {name}")
                result = func(*args, **kwargs)
                return result
            return wrapper
        return decorator
    
    def postcondition(self, predicate: Callable):
        def decorator(func):
            @wraps(func)
            def wrapper(*args, **kwargs):
                result = func(*args, **kwargs)
                if not predicate(result):
                    raise AssertionError(f"Postcondition failed in {func.__name__}")
                return result
            return wrapper
        return decorator
    
    def loop_invariant(self, invariant: Callable, state: Dict[str, Any]):
        if not invariant(state):
            raise AssertionError(f"Loop invariant violated: {state}")

CHECKER = InvariantChecker()