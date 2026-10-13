from dataclasses import dataclass
from typing import Dict, Set, List, Optional, Tuple
import json

@dataclass(frozen=True)
class Signature:
    inputs: frozenset
    outputs: frozenset
    
    def compose(self, other: 'Signature') -> Optional['Signature']:
        """Algebraic composition: g ∘ f valid iff outputs(f) ⊆ inputs(g)"""
        if not self.outputs.issubset(other.inputs):
            return None
        return Signature(
            inputs=self.inputs | (other.inputs - self.outputs),
            outputs=other.outputs | (self.outputs - other.inputs)
        )

class ModuleAlgebra:
    def __init__(self):
        self.modules: Dict[str, Signature] = {}
        self.compositions: Dict[str, List[str]] = {}
    
    def register(self, name: str, inputs: List[str], outputs: List[str]):
        self.modules[name] = Signature(frozenset(inputs), frozenset(outputs))
    
    def can_compose(self, f: str, g: str) -> bool:
        """Check if g ∘ f is valid"""
        return self.modules[f].compose(self.modules[g]) is not None
    
    def compose_chain(self, chain: List[str]) -> Optional[Signature]:
        """Reduce list of modules to single composite signature"""
        if not chain:
            return None
        sig = self.modules[chain[0]]
        for name in chain[1:]:
            sig = sig.compose(self.modules[name])
            if sig is None:
                return None
        return sig
    
    def find_paths(self, source_type: str, target_type: str, max_depth: int = 3) -> List[List[str]]:
        """Find all valid composition paths transforming source_type to target_type"""
        paths = []
        
        def search(current_outputs: frozenset, path: List[str], depth: int):
            if depth > max_depth:
                return
            if target_type in current_outputs:
                paths.append(path[:])
                return
            
            for name, sig in self.modules.items():
                if name not in path and current_outputs & sig.inputs:
                    path.append(name)
                    search(current_outputs | sig.outputs, path, depth + 1)
                    path.pop()
        
        search(frozenset([source_type]), [], 0)
        return paths
    
    def verify_invariant(self, module: str, invariant: str) -> bool:
        """Check if module preserves an invariant (output contains it if input did)"""
        sig = self.modules[module]
        return invariant in sig.inputs and invariant in sig.outputs
    
    def export_graph(self) -> dict:
        return {
            "modules": {k: {"in": list(v.inputs), "out": list(v.outputs)} 
                       for k, v in self.modules.items()},
            "composable_pairs": [(f, g) for f in self.modules for g in self.modules 
    if f != g and self.can_compose(f, g)]
        }

algebra = ModuleAlgebra()