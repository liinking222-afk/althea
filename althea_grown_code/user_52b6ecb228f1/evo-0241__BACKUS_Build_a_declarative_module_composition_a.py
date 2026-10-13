#!/usr/bin/env python3
import re
import json
from pathlib import Path
from typing import Dict, List, Set, Tuple

def extract_signature(code: str) -> Dict:
    """Extract functional signature from module code."""
    inputs = set(re.findall(r'(?:stdin|input|read|argv|param)[\w_]*', code.lower()))
    outputs = set(re.findall(r'(?:stdout|output|write|print|return|emit)[\w_]*', code.lower()))
    transforms = set(re.findall(r'(?:transform|map|filter|reduce|compose|pipe)', code.lower()))
    
    return {
        "input_channels": list(inputs),
        "output_channels": list(outputs),
        "transformations": list(transforms),
        "arity": len(inputs),
        "purity": "const" in code.lower() or "immutable" in code.lower()
    }

def compose_check(f_sig: Dict, g_sig: Dict) -> Dict:
    """Check if f ∘ g is valid composition."""
    f_in = set(f_sig["input_channels"])
    g_out = set(g_sig["output_channels"])
    
    compatible = bool(f_in.intersection(g_out)) or (not f_in or not g_out)
    
    return {
        "composable": compatible,
        "composition": f"g → f" if compatible else "INCOMPATIBLE",
        "shared_channels": list(f_in.intersection(g_out))
    }

def analyze_module_algebra(modules_dir: str = "/tmp/althea_modules") -> Dict:
    """Treat modules as algebraic objects and derive composition lattice."""
    path = Path(modules_dir)
    if not path.exists():
        return {"modules": [], "composition_graph": {}}
    
    signatures = {}
    for mod_file in path.glob("*.py"):
        code = mod_file.read_text()
        signatures[mod_file.stem] = extract_signature(code)
    
    composition_graph = {}
    for m1 in signatures:
        composition_graph[m1] = {}
        for m2 in signatures:
            if m1 != m2:
                composition_graph[m1][m2] = compose_check(
                    signatures[m1], 
                    signatures[m2]
                )
    
    return {
        "signatures": signatures,
        "composition_graph": composition_graph,
        "identity_modules": [m for m, s in signatures.items() if s["arity"] == 1],
        "pure_functions": [m for m, s in signatures.items() if s["purity"]]
    }

if __name__ == "__main__":
    result = analyze_module_algebra()
    print(json.dumps(result, indent=2))