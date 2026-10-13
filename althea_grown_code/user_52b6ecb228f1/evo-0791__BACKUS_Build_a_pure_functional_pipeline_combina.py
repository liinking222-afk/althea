#!/usr/bin/env python3
"""Functional pipeline algebra with composition laws and reasoning primitives."""

from typing import Callable, TypeVar, Generic, Any
from dataclasses import dataclass
from functools import reduce

A = TypeVar('A')
B = TypeVar('B')
C = TypeVar('C')

@dataclass(frozen=True)
class Pipeline(Generic[A, B]):
    """Immutable pipeline with algebraic properties."""
    f: Callable[[A], B]
    
    def __rshift__(self, other: 'Pipeline[B, C]') -> 'Pipeline[A, C]':
        """Compose pipelines: self >> other ≡ other ∘ self"""
        return Pipeline(lambda x: other.f(self.f(x)))
    
    def __call__(self, x: A) -> B:
        return self.f(x)
    
    def verify_associativity(self, g: 'Pipeline', h: 'Pipeline', test_val: Any) -> bool:
        """Prove (f >> g) >> h ≡ f >> (g >> h)"""
        left = (self >> g) >> h
        right = self >> (g >> h)
        return left(test_val) == right(test_val)
    
    def map_law(self, x: A) -> bool:
        """Identity law: Pipeline(id) >> self ≡ self"""
        identity = Pipeline(lambda v: v)
        return (identity >> self)(x) == self(x)

def pipe(*fns: Callable) -> Pipeline:
    """Construct pipeline from function sequence."""
    if not fns:
        return Pipeline(lambda x: x)
    return reduce(lambda p, f: p >> Pipeline(f), fns[1:], Pipeline(fns[0]))

def parallel(*pipelines: Pipeline) -> Pipeline:
    """Execute pipelines in parallel (tuple output)."""
    return Pipeline(lambda x: tuple(p(x) for p in pipelines))

def branch(predicate: Callable[[A], bool], 
           true_pipe: Pipeline[A, B], 
           false_pipe: Pipeline[A, B]) -> Pipeline[A, B]:
    """Conditional pipeline routing."""
    return Pipeline(lambda x: true_pipe(x) if predicate(x) else false_pipe(x))

def trace(label: str) -> Pipeline:
    """Identity with side-effect logging (explicit impurity boundary)."""
    def _trace(x):
        print(f"[TRACE {label}]: {x}")
        return x
    return Pipeline(_trace)

# Example: prove composition laws
if __name__ == "__main__":
    inc = Pipeline(lambda x: x + 1)
    double = Pipeline(lambda x: x * 2)
    square = Pipeline(lambda x: x ** 2)
    
    composed = inc >> double >> square
    print(f"Result: {composed(3)}")  # ((3+1)*2)^2 = 64
    print(f"Associativity holds: {inc.verify_associativity(double, square, 3)}")
    print(f"Identity law holds: {inc.map_law(5)}")