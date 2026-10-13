import time
import json
import functools
from typing import Any, Callable, TypeVar, cast

T = TypeVar('T')

def trace(func: Callable[..., T]) -> Callable[..., T]:
    """Trace function execution. Pipe output to analysis tools."""
    @functools.wraps(func)
    def wrapper(*args: Any, **kwargs: Any) -> T:
        start = time.perf_counter()
        
        trace_input = {
            "function": func.__name__,
            "args": repr(args)[:200],
            "kwargs": repr(kwargs)[:200],
            "timestamp": time.time()
        }
        
        try:
            result = func(*args, **kwargs)
            elapsed = time.perf_counter() - start
            
            trace_output = {
                **trace_input,
                "status": "ok",
                "result": repr(result)[:200],
                "elapsed_ms": round(elapsed * 1000, 2)
            }
            
            print(json.dumps(trace_output), flush=True)
            return result
            
        except Exception as e:
            elapsed = time.perf_counter() - start
            
            trace_output = {
                **trace_input,
                "status": "error",
                "error": str(e)[:200],
                "elapsed_ms": round(elapsed * 1000, 2)
            }
            
            print(json.dumps(trace_output), flush=True)
            raise
    
    return cast(Callable[..., T], wrapper)


def pipe_filter(key: str, value: str) -> None:
    """Filter traced calls by key-value. Use: python trace.py | python -c 'import trace; trace.pipe_filter(\"status\", \"error\")'"""
    import sys
    for line in sys.stdin:
        try:
            data = json.loads(line)
            if data.get(key) == value:
                print(line, end='')
        except:
            pass


if __name__ == "__main__":
    @trace
    def example(x: int) -> int:
        return x * 2
    
    example(5)
    example(10)