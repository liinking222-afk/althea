#!/usr/bin/env python3
from typing import Callable, TypeVar, Tuple, List
from functools import reduce
import re

A = TypeVar('A')
B = TypeVar('B')
C = TypeVar('C')

class ModuleF:
    """Cognitive module as algebraic object with composition laws."""
    
    def __init__(self, name: str, transform: Callable[[A], B], laws: List[str] = None):
        self.name = name
        self.transform = transform
        self.laws = laws or []
        self._verify_purity()
    
    def _verify_purity(self):
        """Check name suggests pure transformation."""
        if not re.match(r'^[a-z_]+_to_[a-z_]+$|^map_[a-z_]+$|^fold_[a-z_]+$', self.name):
            raise ValueError(f"Module {self.name} not named as pure transformation")
    
    def __call__(self, x: A) -> B:
        return self.transform(x)
    
    def compose(self, other: 'ModuleF') -> 'ModuleF':
        """Algebraic composition: (g ∘ f)(x) = g(f(x))"""
        def composed(x):
            return other.transform(self.transform(x))
        
        new_laws = [
            f"associative_with_{other.name}",
            *self.laws,
            *other.laws
        ]
        return ModuleF(
            f"{self.name}_then_{other.name}",
            composed,
            new_laws
        )
    
    def identity_check(self, sample: A) -> bool:
        """Verify identity law: f ∘ id = id ∘ f = f"""
        identity = ModuleF("identity", lambda x: x)
        return (self.compose(identity)(sample) == self(sample) and
                identity.compose(self)(sample) == self(sample))
    
    def associativity_check(self, f: 'ModuleF', g: 'ModuleF', sample: A) -> bool:
        """Verify: (h ∘ g) ∘ f = h ∘ (g ∘ f)"""
        left = self.compose(f).compose(g)
        right = self.compose(f.compose(g))
        return left(sample) == right(sample)
    
    def __repr__(self) -> str:
        return f"ModuleF({self.name}, laws={len(self.laws)})"

def verify_composition_laws(modules: List[ModuleF], sample: A) -> Tuple[bool, List[str]]:
    """Test algebraic properties hold across module composition."""
    violations = []
    
    for i, mod in enumerate(modules):
        if not mod.identity_check(sample):
            violations.append(f"{mod.name} violates identity law")
    
    for i in range(len(modules) - 2):
        if not modules[i].associativity_check(modules[i+1], modules[i+2], sample):
            violations.append(f"Associativity fails: {modules[i].name}, {modules[i+1].name}, {modules[i+2].name}")
    
    return len(violations) == 0, violations