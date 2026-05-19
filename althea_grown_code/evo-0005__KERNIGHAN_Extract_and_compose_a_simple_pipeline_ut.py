#!/usr/bin/env python3
"""pipe.py - Kernighan-style function composition for Althea modules"""

from typing import Callable, Any, TypeVar

T = TypeVar('T')
U = TypeVar('U')

def pipe(value: Any, *functions: Callable) -> Any:
    """Pass value through functions left-to-right. Each does ONE thing."""
    result = value
    for fn in functions:
        result = fn(result)
    return result

def compose(*functions: Callable) -> Callable:
    """Create a pipeline. Returns a function that pipes input through all."""
    def pipeline(value: Any) -> Any:
        return pipe(value, *functions)
    return pipeline

def tap(label: str) -> Callable:
    """Debug tap: print labeled value, pass it through unchanged."""
    def _tap(value: Any) -> Any:
        print(f"{label}: {value}")
        return value
    return _tap

def filter_none(items: list) -> list:
    """Remove None values. ONE thing."""
    return [x for x in items if x is not None]

def take(n: int) -> Callable:
    """Take first n items. Returns a function."""
    def _take(items: list) -> list:
        return items[:n]
    return _take

def map_fn(fn: Callable) -> Callable:
    """Map function over list. Returns a function."""
    def _map(items: list) -> list:
        return [fn(item) for item in items]
    return _map

if __name__ == "__main__":
    # Example: compose micro-optimized modules readably
    process = compose(
        filter_none,
        take(5),
        map_fn(str.upper),
        tap("result")
    )
    
    data = ["a", None, "b", "c", None, "d", "e", "f"]
    output = process(data)