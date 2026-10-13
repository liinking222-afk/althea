#!/usr/bin/env python3
"""Module Composition Algebra - Backus-style declarative reasoning over modules"""

from dataclasses import dataclass
from typing import List, Set, Tuple, Dict
from functools import reduce
import re

@dataclass(frozen=True)
class ModuleSignature:
    inputs: frozenset
    outputs: frozenset
    domain: str
    
    def __hash__(self):
        return hash((self.inputs, self.outputs, self.domain))

def parse_module_signature(module_path: str) -> ModuleSignature:
    """Extract algebraic signature from module path"""
    domain = module_path.split('-')[-1] if '-' in module_path else "general"
    
    # Infer I/O from domain semantics
    io_map = {
        "weather": (frozenset(["location"]), frozenset(["temperature", "conditions"])),
        "orbital": (frozenset(["tle", "time"]), frozenset(["position", "velocity"])),
        "translation": (frozenset(["text", "lang_pair"]), frozenset(["translated_text"])),
        "recursion": (frozenset(["tree"]), frozenset(["inverted_tree"])),
    }
    
    for key, (ins, outs) in io_map.items():
        if key in module_path.lower():
            return ModuleSignature(ins, outs, key)
    
    return ModuleSignature(frozenset(), frozenset(), domain)

def compose(m1: ModuleSignature, m2: ModuleSignature) -> ModuleSignature:
    """f ∘ g: outputs of g feed inputs of f"""
    if not m2.outputs & m1.inputs:
        return None
    
    new_inputs = (m1.inputs - m2.outputs) | m2.inputs
    new_outputs = m1.outputs | (m2.outputs - m1.inputs)
    new_domain = f"{m2.domain}→{m1.domain}"
    
    return ModuleSignature(new_inputs, new_outputs, new_domain)

def find_composition_chains(modules: List[str]) -> List[Tuple[str, str, str]]:
    """Discover all valid f∘g compositions"""
    sigs = {m: parse_module_signature(m) for m in modules}
    chains = []
    
    for m1 in modules:
        for m2 in modules:
            if m1 != m2:
                composed = compose(sigs[m1], sigs[m2])
                if composed:
                    chains.append((m2, m1, f"{composed.domain}"))
    
    return chains

def algebraic_equivalence(m1: ModuleSignature, m2: ModuleSignature) -> bool:
    """Check if two modules are algebraically equivalent (same I/O signature)"""
    return m1.inputs == m2.inputs and m1.outputs == m2.outputs

if __name__ == "__main__":
    modules = [
        "/autonomous-weather-inquiry-8808",
        "/autonomous-orbital-propagation-8767",
        "/autonomous-linguistic-bridge-8744",
        "/autonomous-recursion-depth-inversion-61ed"
    ]
    
    chains = find_composition_chains(modules)
    
    print("COMPOSABLE MODULE CHAINS (f ∘ g):")
    for g, f, domain in chains:
        print(f"  {g.split('/')[-1][:20]} → {f.split('/')[-1][:20]} = {domain}")