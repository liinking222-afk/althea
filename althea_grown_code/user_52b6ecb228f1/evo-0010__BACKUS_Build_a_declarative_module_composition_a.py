#!/usr/bin/env python3
from dataclasses import dataclass
from typing import Callable, TypeVar, Generic, Union
from enum import Enum

S = TypeVar('S')  # State type
T = TypeVar('T')  # Target type

class CompositionOp(Enum):
    SEQ = ";"      # Sequential composition
    PAR = "||"     # Parallel composition
    ALT = "|"      # Alternative/choice

@dataclass(frozen=True)
class ModuleSignature(Generic[S, T]):
    """Algebraic signature: input_state -> output_state"""
    name: str
    input_type: type
    output_type: type
    transform: Callable[[S], T]
    
    def __rshift__(self, other: 'ModuleSignature') -> 'ComposedModule':
        """Sequential: self >> other (algebraic ;)"""
        if self.output_type != other.input_type:
            raise TypeError(f"Type mismatch: {self.output_type} != {other.input_type}")
        return ComposedModule(self, other, CompositionOp.SEQ)
    
    def __or__(self, other: 'ModuleSignature') -> 'ComposedModule':
        """Alternative: self | other (algebraic choice)"""
        if self.input_type != other.input_type or self.output_type != other.output_type:
            raise TypeError(f"Alternative requires same signature")
        return ComposedModule(self, other, CompositionOp.ALT)
    
    def __and__(self, other: 'ModuleSignature') -> 'ComposedModule':
        """Parallel: self & other (algebraic product)"""
        return ComposedModule(self, other, CompositionOp.PAR)
    
    def __call__(self, state: S) -> T:
        return self.transform(state)

@dataclass
class ComposedModule:
    """Represents algebraic composition of modules"""
    left: Union[ModuleSignature, 'ComposedModule']
    right: Union[ModuleSignature, 'ComposedModule']
    op: CompositionOp
    
    def typecheck(self) -> bool:
        """Verify composition is well-typed"""
        if self.op == CompositionOp.SEQ:
            return self.left.output_type == self.right.input_type
        elif self.op == CompositionOp.ALT:
            return (self.left.input_type == self.right.input_type and 
                    self.left.output_type == self.right.output_type)
        return True  # PAR always valid
    
    def execute(self, state):
        """Execute composed computation"""
        if not self.typecheck():
            raise TypeError("Composition type error")
        if self.op == CompositionOp.SEQ:
            return self.right(self.left(state))
        elif self.op == CompositionOp.PAR:
            return (self.left(state), self.right(state))
        else:  # ALT - execute left, fallback to right
            try:
                return self.left(state)
            except:
                return self.right(state)
    
    def __call__(self, state):
        return self.execute(state)

def identity(name: str, state_type: type) -> ModuleSignature:
    """Identity morphism in module category"""
    return ModuleSignature(name, state_type, state_type, lambda x: x)