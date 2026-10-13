#!/usr/bin/env python3
"""ALTHEA Module Algebra - Declarative composition with verifiable properties"""

from typing import Callable, TypeVar, Generic, List, Tuple, Optional
from dataclasses import dataclass
from functools import reduce

A = TypeVar('A')
B = TypeVar('B')
C = TypeVar('C')

@dataclass(frozen=True)
class ModuleSignature(Generic[A, B]):
    """Algebraic type signature for a module"""
    name: str
    input_type: type
    output_type: type
    properties: frozenset[str]
    
    def compose(self, other: 'ModuleSignature') -> Optional['ModuleSignature']:
        """Category-theoretic composition: f: A→B, g: B→C yields g∘f: A→C"""
        if self.output_type != other.input_type:
            return None
        return ModuleSignature(
            name=f"{other.name}∘{self.name}",
            input_type=self.input_type,
            output_type=other.output_type,
            properties=self.properties | other.properties
        )
    
    def verify_identity(self, identity_sig: 'ModuleSignature') -> bool:
        """Identity law: id∘f = f∘id = f"""
        return (self.compose(identity_sig) == self and 
                identity_sig.compose(self) == self)
    
    def verify_associativity(self, g: 'ModuleSignature', h: 'ModuleSignature') -> bool:
        """Associative law: (h∘g)∘f = h∘(g∘f)"""
        left = self.compose(g)
        if not left:
            return False
        left_composed = left.compose(h)
        
        right = g.compose(h)
        if not right:
            return False
        right_composed = self.compose(right)
        
        return left_composed == right_composed

class ModuleAlgebra:
    """Registry treating modules as first-class algebraic objects"""
    
    def __init__(self):
        self.modules: dict[str, ModuleSignature] = {}
        self.compositions: dict[str, List[str]] = {}
    
    def register(self, sig: ModuleSignature) -> None:
        self.modules[sig.name] = sig
    
    def find_composable_chain(self, start_type: type, end_type: type) -> List[str]:
        """Declaratively find valid composition chain from type A to type B"""
        if start_type == end_type:
            return []
        
        for name, sig in self.modules.items():
            if sig.input_type == start_type:
                if sig.output_type == end_type:
                    return [name]
                rest = self.find_composable_chain(sig.output_type, end_type)
                if rest is not None:
                    return [name] + rest
        return []
    
    def verify_composition_laws(self, module_name: str) -> dict[str, bool]:
        """Verify algebraic laws for a module"""
        sig = self.modules.get(module_name)
        if not sig:
            return {}
        
        identity = ModuleSignature("id", sig.input_type, sig.input_type, frozenset())
        
        return {
            "has_identity": sig.verify_identity(identity),
            "composable_modules": len([m for m in self.modules.values() 
    if sig.output_type == m.input_type])
        }

# Initialize global algebra
ALGEBRA = ModuleAlgebra()