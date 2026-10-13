#!/usr/bin/env python3
"""functional_combinators.py - Algebraic module composition primitives"""

from typing import Callable, TypeVar, Any, Tuple
from functools import reduce

A = TypeVar('A')
B = TypeVar('B')
C = TypeVar('C')

# Identity: id(x) = x
def identity(x: A) -> A:
    return x

# Composition: (g ∘ f)(x) = g(f(x))
def compose(*fns: Callable) -> Callable:
    return reduce(lambda f, g: lambda x: f(g(x)), fns, identity)

# Kleisli composition for Result types: (g >=> f)(x)
def kleisli(*fns: Callable[[A], Tuple[bool, B]]) -> Callable[[A], Tuple[bool, Any]]:
    def composed(x):
        for fn in reversed(fns):
            success, result = fn(x)
            if not success:
                return False, result
            x = result
        return True, x
    return composed

# Fork: f &&& g = λx → (f(x), g(x))
def fork(f: Callable[[A], B], g: Callable[[A], C]) -> Callable[[A], Tuple[B, C]]:
    return lambda x: (f(x), g(x))

# Parallel application: f *** g = λ(x,y) → (f(x), g(y))
def parallel(f: Callable[[A], B], g: Callable[[C], Any]) -> Callable[[Tuple[A, C]], Tuple[B, Any]]:
    return lambda xy: (f(xy[0]), g(xy[1]))

# Curry: curry(f)(x)(y) = f(x, y)
def curry(f: Callable) -> Callable:
    return lambda x: lambda y: f(x, y)

# Flip arguments: flip(f)(x, y) = f(y, x)
def flip(f: Callable) -> Callable:
    return lambda x, y: f(y, x)

# Constant combinator: const(x)(y) = x
def const(x: A) -> Callable[[Any], A]:
    return lambda _: x

# Fix-point combinator (Y-combinator): fix(f) where f(fix(f)) = fix(f)
def fix(f: Callable) -> Callable:
    return lambda x: f(fix(f))(x)

# Monadic bind for Result: bind(m, f)
def bind(m: Tuple[bool, A], f: Callable[[A], Tuple[bool, B]]) -> Tuple[bool, B]:
    success, value = m
    return f(value) if success else (False, value)

# Functor map for Result: fmap(f, m)
def fmap(f: Callable[[A], B], m: Tuple[bool, A]) -> Tuple[bool, B]:
    success, value = m
    return (success, f(value)) if success else (False, value)

# Apply wrapped function: ap(mf, mx)
def ap(mf: Tuple[bool, Callable], mx: Tuple[bool, A]) -> Tuple[bool, Any]:
    sf, f = mf
    sx, x = mx
    return (sf and sx, f(x)) if sf and sx else (False, None)

# Module composition operator
class Module:
    def __init__(self, fn: Callable, name: str = "anonymous"):
        self.fn = fn
        self.name = name
    
    def __call__(self, *args, **kwargs):
        return self.fn(*args, **kwargs)
    
    def __rshift__(self, other):  # f >> g
        return Module(compose(other.fn, self.fn), f"{self.name}→{other.name}")
    
    def __and__(self, other):  # f & g (fork)
        return Module(fork(self.fn, other.fn), f"{self.name}∧{other.name}")