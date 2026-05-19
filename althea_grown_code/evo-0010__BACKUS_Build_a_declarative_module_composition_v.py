#!/usr/bin/env python3
"""
Declarative Module Composition Validator
Treats cognitive modules as algebraic objects with verifiable properties.
"""

from dataclasses import dataclass
from typing import Set, Dict, List, Optional, Callable
from enum import Enum

class Property(Enum):
    IDEMPOTENT = "idempotent"  # f(f(x)) = f(x)
    COMMUTATIVE = "commutative"  # f(g(x)) = g(f(x))
    ASSOCIATIVE = "associative"  # f(g(h(x))) = (f∘g)(h(x))
    PURE = "pure"  # no side effects, same input → same output
    MONOTONIC = "monotonic"  # preserves ordering

@dataclass
class ModuleSignature:
    name: str
    input_type: str
    output_type: str
    properties: Set[Property]
    constraints: Set[str]

class CompositionValidator:
    def __init__(self):
        self.signatures: Dict[str, ModuleSignature] = {}
    
    def register(self, sig: ModuleSignature):
        self.signatures[sig.name] = sig
    
    def type_check(self, pipeline: List[str]) -> Optional[str]:
        """Verify type compatibility through composition chain."""
        for i in range(len(pipeline) - 1):
            left = self.signatures.get(pipeline[i])
            right = self.signatures.get(pipeline[i + 1])
            if not left or not right:
                return f"Unknown module in pipeline at position {i}"
            if left.output_type != right.input_type:
                return f"Type mismatch: {left.name}→{right.name}"
        return None
    
    def verify_properties(self, pipeline: List[str]) -> Dict[Property, bool]:
        """Determine algebraic properties of composed pipeline."""
        if not pipeline:
            return {}
        
        mods = [self.signatures[n] for n in pipeline if n in self.signatures]
        if len(mods) != len(pipeline):
            return {}
        
        return {
            Property.PURE: all(Property.PURE in m.properties for m in mods),
            Property.IDEMPOTENT: len(mods) == 1 and Property.IDEMPOTENT in mods[0].properties,
            Property.ASSOCIATIVE: all(Property.ASSOCIATIVE in m.properties for m in mods),
            Property.MONOTONIC: all(Property.MONOTONIC in m.properties for m in mods)
        }
    
    def can_parallelize(self, mod1: str, mod2: str) -> bool:
        """Check if two modules commute and can execute in parallel."""
        m1, m2 = self.signatures.get(mod1), self.signatures.get(mod2)
        if not m1 or not m2:
            return False
        return (Property.COMMUTATIVE in m1.properties and 
                Property.COMMUTATIVE in m2.properties and
                Property.PURE in m1.properties and
                Property.PURE in m2.properties)
    
    def optimize_pipeline(self, pipeline: List[str]) -> List[str]:
        """Apply algebraic laws to simplify pipeline."""
        optimized = pipeline.copy()
        # Remove consecutive idempotent duplicates: f∘f = f
        i = 0
        while i < len(optimized) - 1:
            mod = self.signatures.get(optimized[i])
            if mod and Property.IDEMPOTENT in mod.properties:
                if optimized[i] == optimized[i + 1]:
                    optimized.pop(i + 1)
                    continue
            i += 1
        return optimized