#!/usr/bin/env python3
"""Module Algebra: Functional composition system for Althea's modules"""

from typing import Callable, Any, TypeVar, Generic
from dataclasses import dataclass
from functools import reduce

A = TypeVar('A')
B = TypeVar('B')
C = TypeVar('C')

@dataclass(frozen=True)
class ModuleF(Generic[A, B]):
    """A module as an algebraic function with signature"""
    name: str
    input_type: type
    output_type: type
    transform: Callable[[A], B]
    
    def __call__(self, x: A) -> B:
        return self.transform(x)
    
    def compose(self, other: 'ModuleF[B, C]') -> 'ModuleF[A, C]':
        """Algebraic composition: f ∘ g"""
        if self.output_type != other.input_type:
            raise TypeError(f"Cannot compose: {self.output_type} → {other.input_type}")
        return ModuleF(
            name=f"{other.name}∘{self.name}",
            input_type=self.input_type,
            output_type=other.output_type,
            transform=lambda x: other.transform(self.transform(x))
        )
    
    def __rshift__(self, other):
        """Operator sugar: f >> g"""
        return self.compose(other)

class Algebra:
    """Reasoning engine for module compositions"""
    
    @staticmethod
    def identity(t: type) -> ModuleF[A, A]:
        """Identity morphism"""
        return ModuleF("id", t, t, lambda x: x)
    
    @staticmethod
    def pipeline(*modules: ModuleF) -> ModuleF:
        """Compose a sequence of modules left-to-right"""
        return reduce(lambda f, g: f.compose(g), modules)
    
    @staticmethod
    def verify_composition(*modules: ModuleF) -> tuple[bool, str]:
        """Statically verify if modules can compose"""
        for i in range(len(modules) - 1):
            if modules[i].output_type != modules[i+1].input_type:
                return False, f"Break at {modules[i].name}→{modules[i+1].name}"
        return True, "Valid composition"
    
    @staticmethod
    def derive_signature(*modules: ModuleF) -> tuple[type, type]:
        """Derive input/output types of composition without executing"""
        return modules[0].input_type, modules[-1].output_type

if __name__ == "__main__":
    # Example: Althea's modules as algebraic objects
    tokenize = ModuleF("tokenize", str, list, lambda s: s.split())
    count = ModuleF("count", list, int, len)
    classify = ModuleF("classify", int, str, lambda n: "short" if n < 5 else "long")
    
    # Reason about composition before execution
    pipeline = tokenize >> count >> classify
    valid, msg = Algebra.verify_composition(tokenize, count, classify)
    print(f"Pipeline '{pipeline.name}': {msg}")
    print(f"Signature: {pipeline.input_type.__name__} → {pipeline.output_type.__name__}")
    print(f"Result: {pipeline('hello world from Althea')}")