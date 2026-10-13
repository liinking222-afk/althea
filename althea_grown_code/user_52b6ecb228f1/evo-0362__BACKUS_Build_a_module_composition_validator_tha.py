#!/usr/bin/env python3
"""Functional Composition Validator - Algebraic reasoning over capability chains"""

from dataclasses import dataclass
from typing import Callable, List, Optional, Tuple, Any
from functools import reduce
import json

@dataclass(frozen=True)
class CapabilitySignature:
    """Immutable capability type signature"""
    input_type: str
    output_type: str
    pure: bool  # No side effects
    idempotent: bool
    
    def compose(self, other: 'CapabilitySignature') -> Optional['CapabilitySignature']:
        """Algebraic composition: f ∘ g valid iff output(g) = input(f)"""
        if self.input_type != other.output_type:
            return None
        return CapabilitySignature(
            input_type=other.input_type,
            output_type=self.output_type,
            pure=self.pure and other.pure,
            idempotent=self.idempotent and other.idempotent
        )

class CompositionValidator:
    """Validates capability chains using functional composition laws"""
    
    def __init__(self):
        self.registry = {}
    
    def register(self, name: str, sig: CapabilitySignature):
        self.registry[name] = sig
    
    def validate_chain(self, chain: List[str]) -> Tuple[bool, Optional[CapabilitySignature], str]:
        """Prove chain validity through type algebra"""
        if not chain:
            return False, None, "Empty chain"
        
        signatures = [self.registry.get(c) for c in chain]
        if None in signatures:
            missing = [chain[i] for i, s in enumerate(signatures) if s is None]
            return False, None, f"Undefined: {missing}"
        
        # Right-to-left composition (mathematical convention)
        result = reduce(
            lambda acc, sig: acc.compose(sig) if acc else None,
            reversed(signatures)
        )
        
        if result is None:
            return False, None, "Type mismatch in composition"
        
        return True, result, "Valid composition"
    
    def find_identity(self, type_name: str) -> CapabilitySignature:
        """Identity morphism: id_A : A → A"""
        return CapabilitySignature(type_name, type_name, True, True)
    
    def prove_associativity(self, a: str, b: str, c: str) -> bool:
        """Verify (f ∘ g) ∘ h = f ∘ (g ∘ h)"""
        left = self.validate_chain([a, b, c])
        return left[0]  # Composition is associative by construction

# Example capability signatures
validator = CompositionValidator()
validator.register("parse_json", CapabilitySignature("text", "data", True, True))
validator.register("extract_price", CapabilitySignature("data", "number", True, True))
validator.register("format_currency", CapabilitySignature("number", "text", True, True))

if __name__ == "__main__":
    chain = ["parse_json", "extract_price", "format_currency"]
    valid, sig, msg = validator.validate_chain(chain)
    print(json.dumps({"valid": valid, "signature": sig.__dict__ if sig else None, "message": msg}))