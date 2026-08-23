#!/usr/bin/env python3
"""Functional Module Registry - Algebraic Capability Composition"""

from typing import Callable, TypeVar, Generic, NamedTuple, Tuple
from dataclasses import dataclass
from functools import reduce

A = TypeVar('A')
B = TypeVar('B')
C = TypeVar('C')

@dataclass(frozen=True)
class Signature:
    """Immutable type signature"""
    input_type: str
    output_type: str
    
    def composable_with(self, other: 'Signature') -> bool:
        """Mathematical composition check: g ∘ f valid iff output(f) = input(g)"""
        return self.output_type == other.input_type

@dataclass(frozen=True)
class Module:
    """Pure functional module descriptor"""
    name: str
    sig: Signature
    transform: Callable
    
    def __call__(self, x):
        return self.transform(x)
    
    def compose(self, other: 'Module') -> 'Module':
        """Algebraic composition: (g ∘ f)(x) = g(f(x))"""
        if not self.sig.composable_with(other.sig):
            raise TypeError(f"Cannot compose {self.sig} with {other.sig}")
        return Module(
            name=f"{other.name}∘{self.name}",
            sig=Signature(self.sig.input_type, other.sig.output_type),
            transform=lambda x: other.transform(self.transform(x))
        )

class Registry:
    """Declarative module registry with algebraic reasoning"""
    
    def __init__(self):
        self._modules: dict[str, Module] = {}
    
    def register(self, module: Module) -> None:
        """Pure registration - no side effects"""
        self._modules = {**self._modules, module.name: module}
    
    def find_chain(self, from_type: str, to_type: str) -> list[Module]:
        """Find valid composition chain using type algebra"""
        if from_type == to_type:
            return []
        
        valid = [m for m in self._modules.values() if m.sig.input_type == from_type]
        
        for mod in valid:
            if mod.sig.output_type == to_type:
                return [mod]
            chain = self.find_chain(mod.sig.output_type, to_type)
            if chain is not None:
                return [mod] + chain
        return None
    
    def compose_chain(self, modules: list[Module]) -> Module:
        """Reduce list of modules to single composite via algebraic composition"""
        return reduce(lambda f, g: f.compose(g), modules)
    
    def auto_transform(self, data, from_type: str, to_type: str):
        """Declaratively find and execute transformation pipeline"""
        chain = self.find_chain(from_type, to_type)
        if not chain:
            raise ValueError(f"No path from {from_type} to {to_type}")
        composite = self.compose_chain(chain)
        return composite(data)