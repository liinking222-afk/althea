from dataclasses import dataclass
from typing import Callable, TypeVar, Generic, List, Optional, Tuple
from functools import reduce

A = TypeVar('A')
B = TypeVar('B')
C = TypeVar('C')

@dataclass(frozen=True)
class ModuleType(Generic[A, B]):
    """Algebraic type representing a module as a morphism A -> B"""
    input_type: type
    output_type: type
    module_path: str
    
    def compose(self, other: 'ModuleType[B, C]') -> 'ModuleType[A, C]':
        """Categorical composition: if self: A->B and other: B->C, return A->C"""
        if self.output_type != other.input_type:
            raise TypeError(f"Type mismatch: {self.output_type} != {other.input_type}")
        return ModuleType(
            input_type=self.input_type,
            output_type=other.output_type,
            module_path=f"{self.module_path} |> {other.module_path}"
        )
    
    def __rshift__(self, other):
        """Syntactic sugar: mod1 >> mod2 means compose"""
        return self.compose(other)

class ModuleAlgebra:
    """Registry treating modules as algebraic objects"""
    
    def __init__(self):
        self.modules: List[ModuleType] = []
    
    def register(self, input_t: type, output_t: type, path: str) -> ModuleType:
        mod = ModuleType(input_t, output_t, path)
        self.modules.append(mod)
        return mod
    
    def find_path(self, from_type: type, to_type: type) -> Optional[List[ModuleType]]:
        """Find composable chain from_type -> to_type using BFS"""
        if from_type == to_type:
            return []
        
        queue = [(from_type, [])]
        visited = {from_type}
        
        while queue:
            current_type, path = queue.pop(0)
            
            for mod in self.modules:
                if mod.input_type == current_type and mod.output_type not in visited:
                    new_path = path + [mod]
                    if mod.output_type == to_type:
                        return new_path
                    queue.append((mod.output_type, new_path))
                    visited.add(mod.output_type)
        
        return None
    
    def compose_chain(self, chain: List[ModuleType]) -> ModuleType:
        """Reduce chain via composition"""
        return reduce(lambda acc, mod: acc >> mod, chain)

algebra = ModuleAlgebra()