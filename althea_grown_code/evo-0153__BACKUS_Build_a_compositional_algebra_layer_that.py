#!/usr/bin/env python3
"""Module Algebra - Compositional reasoning over Althea modules as algebraic objects"""

from dataclasses import dataclass
from typing import Callable, Any, Tuple, List, Optional
import re

@dataclass(frozen=True)
class ModuleSignature:
    """Algebraic type signature for a module"""
    name: str
    inputs: Tuple[str, ...]
    outputs: Tuple[str, ...]
    constraints: Tuple[str, ...]
    
    def __matmul__(self, other: 'ModuleSignature') -> Optional['ModuleSignature']:
        """Compose signatures if outputs align with inputs (@ operator)"""
        if not set(self.outputs).intersection(set(other.inputs)):
            return None
        return ModuleSignature(
            f"{self.name}∘{other.name}",
            self.inputs,
            other.outputs,
            self.constraints + other.constraints
        )
    
    def __or__(self, other: 'ModuleSignature') -> 'ModuleSignature':
        """Parallel composition (| operator)"""
        return ModuleSignature(
            f"{self.name}|{other.name}",
            self.inputs + other.inputs,
            self.outputs + other.outputs,
            self.constraints + other.constraints
        )

class ModuleAlgebra:
    """Algebraic reasoning system for module composition"""
    
    def __init__(self):
        self.signatures = {}
        
    def register(self, sig: ModuleSignature):
        """Register a module signature"""
        self.signatures[sig.name] = sig
        
    def parse_signature(self, spec: str) -> ModuleSignature:
        """Parse: name(in1,in2)->out1,out2[constraint1,constraint2]"""
        match = re.match(r'(\S+)\((.*?)\)->(.*?)(?:\[(.*?)\])?$', spec.strip())
        if not match:
            raise ValueError(f"Invalid signature: {spec}")
        name, ins, outs, cons = match.groups()
        return ModuleSignature(
            name,
            tuple(i.strip() for i in ins.split(',') if i.strip()),
            tuple(o.strip() for o in outs.split(',') if o.strip()),
            tuple(c.strip() for c in (cons or '').split(',') if c.strip())
        )
    
    def compose_chain(self, *names: str) -> Optional[ModuleSignature]:
        """Attempt to compose modules in sequence"""
        result = self.signatures.get(names[0])
        for name in names[1:]:
            next_sig = self.signatures.get(name)
            if not result or not next_sig:
                return None
            result = result @ next_sig
            if result is None:
                return None
        return result
    
    def verify_constraints(self, sig: ModuleSignature) -> List[str]:
        """Check constraint satisfiability"""
        violations = []
        for constraint in sig.constraints:
            if 'idempotent' in constraint and '∘' in sig.name:
                parts = sig.name.split('∘')
                if len(parts) != len(set(parts)):
                    violations.append(f"Idempotency violated: {sig.name}")
        return violations

# Algebraic reasoning interface
algebra = ModuleAlgebra()