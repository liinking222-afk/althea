#!/usr/bin/env python3
"""Functional Module Compositor - algebraic reasoning over cognitive modules"""

import re
import json
from typing import Dict, List, Tuple, Optional
from functools import reduce

def parse_module_signature(module_code: str) -> Dict:
    """Extract algebraic signature from module code"""
    inputs = re.findall(r'#\s*IN:\s*(\w+(?:,\s*\w+)*)', module_code)
    outputs = re.findall(r'#\s*OUT:\s*(\w+(?:,\s*\w+)*)', module_code)
    effects = re.findall(r'#\s*EFFECT:\s*(\w+)', module_code)
    
    return {
        'inputs': [i.strip() for i in inputs[0].split(',')] if inputs else [],
        'outputs': [o.strip() for o in outputs[0].split(',')] if outputs else [],
        'effects': effects,
        'pure': len(effects) == 0
    }

def compose_signatures(f_sig: Dict, g_sig: Dict) -> Optional[Dict]:
    """Algebraic composition: g ∘ f - returns None if invalid"""
    # Check: outputs of f must satisfy inputs of g
    f_out_set = set(f_sig['outputs'])
    g_in_set = set(g_sig['inputs'])
    
    if not g_in_set.issubset(f_out_set):
        return None  # Composition invalid
    
    # Combined effects (non-pure if either is non-pure)
    combined_effects = list(set(f_sig['effects'] + g_sig['effects']))
    
    return {
        'inputs': f_sig['inputs'],
        'outputs': g_sig['outputs'],
        'effects': combined_effects,
        'pure': len(combined_effects) == 0,
        'chain': [f_sig, g_sig]
    }

def verify_composition_chain(modules: List[str]) -> Tuple[bool, Optional[Dict]]:
    """Verify a chain of modules can compose algebraically"""
    signatures = [parse_module_signature(m) for m in modules]
    
    if not signatures:
        return False, None
    
    result = reduce(
        lambda acc, sig: compose_signatures(acc, sig) if acc else None,
        signatures[1:],
        signatures[0]
    )
    
    return (result is not None, result)

def generate_composition_proof(chain_sig: Dict) -> str:
    """Generate algebraic proof of composition validity"""
    if not chain_sig:
        return "∅ (invalid composition)"
    
    purity = "PURE" if chain_sig['pure'] else "EFFECTFUL"
    ins = ", ".join(chain_sig['inputs'])
    outs = ", ".join(chain_sig['outputs'])
    
    return f"({ins}) → ({outs}) [{purity}]"

if __name__ == "__main__":
    # Self-test with sample module signatures
    mod_a = "# IN: perception\n# OUT: concept\n# EFFECT: none"
    mod_b = "# IN: concept\n# OUT: action\n"
    
    valid, sig = verify_composition_chain([mod_a, mod_b])
    print(f"Valid: {valid}")
    if sig:
        print(f"Proof: {generate_composition_proof(sig)}")