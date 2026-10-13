#!/usr/bin/env python3
import sys
import time
import json
from typing import Any, Callable, TypeVar

T = TypeVar('T')

class ByteBudgetProfiler:
    """Woz-style constraint tracker: make every token count."""
    
    def __init__(self, budget: int, name: str = "block"):
        self.budget = budget
        self.name = name
        self.start_time = None
        self.measurements = []
    
    def estimate_tokens(self, text: str) -> int:
        """Fast heuristic: ~4 chars per token, biased conservative."""
        return len(text) // 3
    
    def __enter__(self):
        self.start_time = time.time()
        return self
    
    def measure(self, output: Any, label: str = "output"):
        """Record a measurement point."""
        text = str(output) if not isinstance(output, str) else output
        tokens = self.estimate_tokens(text)
        self.measurements.append({
            "label": label,
            "bytes": len(text),
            "est_tokens": tokens,
            "elapsed_ms": int((time.time() - self.start_time) * 1000)
        })
        return output
    
    def __exit__(self, *args):
        total_tokens = sum(m["est_tokens"] for m in self.measurements)
        total_bytes = sum(m["bytes"] for m in self.measurements)
        elapsed = int((time.time() - self.start_time) * 1000)
        
        report = {
            "block": self.name,
            "budget": self.budget,
            "used_est": total_tokens,
            "remaining": self.budget - total_tokens,
            "efficiency": round(total_tokens / self.budget, 3) if self.budget > 0 else 0,
            "total_bytes": total_bytes,
            "elapsed_ms": elapsed,
            "measurements": self.measurements,
            "status": "UNDER" if total_tokens <= self.budget else "OVER"
        }
        
        print(json.dumps(report), file=sys.stderr)
        
        if total_tokens > self.budget:
            sys.exit(1)

def profile(budget: int, name: str = "block") -> Callable[[Callable[..., T]], Callable[..., T]]:
    """Decorator for budget-aware functions."""
    def decorator(func: Callable[..., T]) -> Callable[..., T]:
        def wrapper(*args, **kwargs) -> T:
            with ByteBudgetProfiler(budget, name) as profiler:
                result = func(*args, **kwargs)
                profiler.measure(result, f"{func.__name__}_output")
                return result
        return wrapper
    return decorator

if __name__ == "__main__":
    with ByteBudgetProfiler(1000, "test") as p:
        p.measure("hello" * 50, "greeting")
        p.measure("world" * 100, "payload")