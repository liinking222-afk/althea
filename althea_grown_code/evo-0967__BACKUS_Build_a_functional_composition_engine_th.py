#!/usr/bin/env python3
"""
Functional Composition Engine - Modules as Algebraic Objects
Enables declarative reasoning about module composition chains.
"""

import json
import re
from pathlib import Path
from typing import Dict, List, Tuple, Optional

MANIFEST_DIR = Path("/tmp/althea/modules")
COMPOSITION_LOG = Path("/tmp/althea/compositions.jsonl")

def parse_module_signature(module_path: Path) -> Optional[Tuple[str, str, str]]:
    """Extract algebraic signature: (domain, codomain, name) from module."""
    try:
        content = module_path.read_text()
        # Look for type annotations or docstring declarations
        domain_match = re.search(r'(?:INPUT|DOMAIN|ACCEPTS):\s*(\w+)', content, re.I)
        codomain_match = re.search(r'(?:OUTPUT|CODOMAIN|RETURNS):\s*(\w+)', content, re.I)
        
        if domain_match and codomain_match:
            return (domain_match.group(1), codomain_match.group(1), module_path.stem)
    except:
        pass
    return None

def load_module_algebra() -> Dict[str, Tuple[str, str]]:
    """Build categorical view: module_name -> (domain, codomain)."""
    algebra = {}
    if MANIFEST_DIR.exists():
        for manifest in MANIFEST_DIR.glob("*.json"):
            try:
                data = json.loads(manifest.read_text())
                if "signature" in data:
                    sig = data["signature"]
                    algebra[data["name"]] = (sig.get("input", "Any"), sig.get("output", "Any"))
            except:
                pass
    return algebra

def compose(f: Tuple[str, str], g: Tuple[str, str]) -> Optional[Tuple[str, str]]:
    """Categorical composition: g ∘ f valid iff codomain(f) = domain(g)."""
    f_dom, f_cod = f
    g_dom, g_cod = g
    
    if f_cod == g_dom or f_cod == "Any" or g_dom == "Any":
        return (f_dom, g_cod)
    return None

def find_compositions(algebra: Dict[str, Tuple[str, str]]) -> List[Dict]:
    """Discover all valid 2-compositions in the module category."""
    valid = []
    modules = list(algebra.items())
    
    for i, (name_f, sig_f) in enumerate(modules):
        for name_g, sig_g in modules[i:]:
            result = compose(sig_f, sig_g)
            if result and name_f != name_g:
                valid.append({
                    "pipeline": f"{name_f} → {name_g}",
                    "signature": f"{result[0]} → {result[1]}",
                    "modules": [name_f, name_g]
                })
    return valid

def reason_about_modules():
    """Main: algebraic reasoning over module space."""
    COMPOSITION_LOG.parent.mkdir(parents=True, exist_ok=True)
    
    algebra = load_module_algebra()
    compositions = find_compositions(algebra)
    
    report = {
        "total_modules": len(algebra),
        "valid_2_compositions": len(compositions),
        "compositions": compositions[:20],  # Top 20
        "algebra": {k: f"{v[0]}→{v[1]}" for k, v in algebra.items()}
    }
    
    with COMPOSITION_LOG.open("a") as f:
        f.write(json.dumps(report) + "\n")
    
    return report

if __name__ == "__main__":
    result = reason_about_modules()
    print(f"Discovered {result['valid_2_compositions']} valid compositions from {result['total_modules']} modules")