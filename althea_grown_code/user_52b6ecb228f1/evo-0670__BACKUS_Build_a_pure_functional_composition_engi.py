#!/usr/bin/env python3
"""Functional Composition Algebra - modules as morphisms with categorical laws"""

from typing import Callable, Any, TypeVar, Generic
from functools import reduce
from dataclasses import dataclass
import inspect

A = TypeVar('A')
B = TypeVar('B')
C = TypeVar('C')

@dataclass(frozen=True)
class Morphism(Generic[A, B]):
    """A morphism in the category of computations"""
    func: Callable[[A], B]
    domain: str
    codomain: str
    
    def compose(self, other: 'Morphism[B, C]') -> 'Morphism[A, C]':
        """Composition operator: g ∘ f"""
        if self.codomain != other.domain:
            raise TypeError(f"Type mismatch: {self.codomain} → {other.domain}")
        return Morphism(
            func=lambda x: other.func(self.func(x)),
            domain=self.domain,
            codomain=other.codomain
        )
    
    def __call__(self, x: A) -> B:
        return self.func(x)
    
    def verify_identity(self, test_value: A) -> bool:
        """Verify identity law: id ∘ f = f = f ∘ id"""
        id_morph = identity(self.domain)
        left = id_morph.compose(self)(test_value)
        right = self(test_value)
        return left == right
    
    def verify_associativity(self, g: 'Morphism[B, C]', h: 'Morphism[C, Any]', 
                            test_value: A) -> bool:
        """Verify associativity: (h ∘ g) ∘ f = h ∘ (g ∘ f)"""
        left = h.compose(g).compose(self)(test_value)
        right = h.compose(g.compose(self))(test_value)
        return left == right

def identity(type_name: str) -> Morphism[A, A]:
    """Identity morphism for any type"""
    return Morphism(func=lambda x: x, domain=type_name, codomain=type_name)

def compose_all(*morphisms: Morphism) -> Morphism:
    """Compose a sequence of morphisms right-to-left"""
    return reduce(lambda g, f: f.compose(g), reversed(morphisms))

def lift_function(func: Callable[[A], B], domain: str, codomain: str) -> Morphism[A, B]:
    """Lift an ordinary function into a morphism"""
    return Morphism(func=func, domain=domain, codomain=codomain)

def pipeline(*funcs_with_types):
    """Create a verified composition pipeline from (func, domain, codomain) tuples"""
    morphisms = [lift_function(f, d, c) for f, d, c in funcs_with_types]
    return compose_all(*morphisms)

# Export algebraic operators
__all__ = ['Morphism', 'identity', 'compose_all', 'lift_function', 'pipeline']