#!/usr/bin/env python3
from typing import Callable, TypeVar, Tuple, List
from functools import reduce
from dataclasses import dataclass
import json

A = TypeVar('A')
B = TypeVar('B')
C = TypeVar('C')

@dataclass(frozen=True)
class Morphism:
    """Pure transformation with algebraic properties"""
    name: str
    func: Callable
    
    def __call__(self, x):
        return self.func(x)
    
    def compose(self, other: 'Morphism') -> 'Morphism':
        """g ∘ f = λx. g(f(x))"""
        return Morphism(
            name=f"{other.name}∘{self.name}",
            func=lambda x: other.func(self.func(x))
        )
    
    def __matmul__(self, other):
        return self.compose(other)

class AlgebraicPipeline:
    """Pipelines as first-class algebraic objects"""
    
    def __init__(self):
        self.morphisms: List[Morphism] = []
        self.identity = Morphism("id", lambda x: x)
    
    def add(self, name: str, func: Callable) -> 'AlgebraicPipeline':
        self.morphisms.append(Morphism(name, func))
        return self
    
    def reduce(self) -> Morphism:
        """Compose all morphisms into single transformation"""
        if not self.morphisms:
            return self.identity
        return reduce(lambda f, g: f @ g, self.morphisms)
    
    def verify_associativity(self) -> bool:
        """((f ∘ g) ∘ h) = (f ∘ (g ∘ h))"""
        if len(self.morphisms) < 3:
            return True
        f, g, h = self.morphisms[:3]
        test_input = {"probe": "associativity_check"}
        left = (f @ g) @ h
        right = f @ (g @ h)
        return left(test_input) == right(test_input)
    
    def map_over(self, inputs: List) -> List:
        """Functor map: preserves structure"""
        composed = self.reduce()
        return [composed(x) for x in inputs]
    
    def trace(self, x):
        """Show intermediate values through pipeline"""
        result = x
        trace_log = [(self.identity.name, result)]
        for m in self.morphisms:
            result = m(result)
            trace_log.append((m.name, result))
        return trace_log
    
    def serialize(self) -> str:
        """Pipeline as algebraic expression"""
        if not self.morphisms:
            return "id"
        names = [m.name for m in reversed(self.morphisms)]
        return " ∘ ".join(names)

if __name__ == "__main__":
    pipeline = AlgebraicPipeline()
    pipeline.add("tokenize", lambda x: x.split())
    pipeline.add("filter", lambda xs: [w for w in xs if len(w) > 3])
    pipeline.add("count", len)
    
    print(f"Pipeline: {pipeline.serialize()}")
    print(f"Associative: {pipeline.verify_associativity()}")
    result = pipeline.reduce()("this is a test message")
    print(f"Result: {result}")