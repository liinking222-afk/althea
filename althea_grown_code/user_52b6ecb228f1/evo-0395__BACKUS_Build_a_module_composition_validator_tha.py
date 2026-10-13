#!/usr/bin/env python3
"""Module Composition Validator - Algebraic reasoning over Althea modules"""

import re
from typing import Dict, List, Set, Tuple, Optional
from dataclasses import dataclass

@dataclass
class ModuleSignature:
    name: str
    inputs: Set[str]
    outputs: Set[str]
    effects: Set[str]
    
    def compose(self, other: 'ModuleSignature') -> Optional['ModuleSignature']:
        """Algebraic composition: f ∘ g where outputs of g feed inputs of f"""
        if not self.inputs.intersection(other.outputs):
            return None
        return ModuleSignature(
            name=f"{other.name}→{self.name}",
            inputs=(self.inputs - other.outputs) | other.inputs,
            outputs=self.outputs | (other.outputs - self.inputs),
            effects=self.effects | other.effects
        )

def extract_signature(code: str, name: str) -> ModuleSignature:
    """Parse code to extract algebraic signature"""
    inputs = set(re.findall(r'input[:\[][\'"]([\w-]+)', code))
    outputs = set(re.findall(r'output[:\[][\'"]([\w-]+)', code))
    effects = set(re.findall(r'effect[:\[][\'"]([\w-]+)', code))
    
    # Heuristic extraction from variable usage
    imports = set(re.findall(r'from ([\w.]+) import', code))
    inputs.update(imports)
    
    return ModuleSignature(name, inputs, outputs, effects)

def validate_composition_chain(modules: List[Tuple[str, str]]) -> Dict:
    """Validate that modules form a valid composition chain"""
    signatures = [extract_signature(code, name) for name, code in modules]
    
    result = {"valid": True, "composition": None, "errors": []}
    
    composed = signatures[0]
    for i, sig in enumerate(signatures[1:], 1):
        next_composed = composed.compose(sig)
        if next_composed is None:
            result["valid"] = False
            result["errors"].append(f"Composition break at step {i}: {composed.name} ∘ {sig.name}")
            return result
        composed = next_composed
    
    result["composition"] = {
        "name": composed.name,
        "inputs": list(composed.inputs),
        "outputs": list(composed.outputs),
        "effects": list(composed.effects)
    }
    return result

if __name__ == "__main__":
    # Self-validation test
    test_modules = [
        ("fractal-render", "# input: 'coordinates'\n# output: 'image-data'"),
        ("image-encode", "# input: 'image-data'\n# output: 'base64'")
    ]
    print(validate_composition_chain(test_modules))