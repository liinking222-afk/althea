import json
import time
from typing import Any, Callable, TypeVar, Generic
from dataclasses import dataclass, asdict
from functools import wraps

T = TypeVar('T')
U = TypeVar('U')

@dataclass
class Composition:
    """Algebraic representation of function composition"""
    operation: str
    inputs: list[Any]
    output: Any
    duration_ms: float
    timestamp: float
    
    def __str__(self) -> str:
        input_repr = " ∘ ".join(str(i) for i in self.inputs)
        return f"{self.operation}({input_repr}) → {self.output}"

class CompositionTracer:
    def __init__(self):
        self.trace: list[Composition] = []
        
    def declarative(self, name: str) -> Callable:
        """Decorator that captures module invocations as algebraic objects"""
        def decorator(func: Callable) -> Callable:
            @wraps(func)
            def wrapper(*args, **kwargs):
                start = time.perf_counter()
                result = func(*args, **kwargs)
                duration = (time.perf_counter() - start) * 1000
                
                comp = Composition(
                    operation=name,
                    inputs=list(args) + [f"{k}={v}" for k, v in kwargs.items()],
                    output=str(result)[:100] if result else None,
                    duration_ms=round(duration, 2),
                    timestamp=time.time()
                )
                self.trace.append(comp)
                return result
            return wrapper
        return decorator
    
    def compose(self, f: Callable[[T], U], g: Callable[[Any], T]) -> Callable[[Any], U]:
        """Functional composition: (f ∘ g)(x) = f(g(x))"""
        @wraps(f)
        def composed(*args, **kwargs):
            intermediate = g(*args, **kwargs)
            return f(intermediate)
        return composed
    
    def get_algebra(self) -> str:
        """Express execution trace as algebraic composition"""
        if not self.trace:
            return "∅"
        ops = [f"{c.operation}" for c in self.trace]
        return " ∘ ".join(reversed(ops))
    
    def analyze_patterns(self) -> dict:
        """Reason about execution algebraically"""
        if not self.trace:
            return {}
        
        total_time = sum(c.duration_ms for c in self.trace)
        op_counts = {}
        for c in self.trace:
            op_counts[c.operation] = op_counts.get(c.operation, 0) + 1
        
        return {
            "composition_chain": self.get_algebra(),
            "total_operations": len(self.trace),
            "total_duration_ms": round(total_time, 2),
            "operation_frequencies": op_counts,
            "associativity_opportunities": len(self.trace) - 1
        }
    
    def export_trace(self) -> str:
        return json.dumps([asdict(c) for c in self.trace], indent=2)

tracer = CompositionTracer()