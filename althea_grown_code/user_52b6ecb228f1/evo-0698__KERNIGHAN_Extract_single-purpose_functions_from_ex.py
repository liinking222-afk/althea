#!/usr/bin/env python3
import re
from pathlib import Path
from typing import List, Dict

def extract_functions(source: str) -> List[Dict[str, str]]:
    """Extract function definitions with their names and bodies."""
    pattern = r'def\s+(\w+)\s*\([^)]*\):\s*\n\s*"""([^"]+)"""'
    return [{"name": m[0], "doc": m[1].strip()} for m in re.findall(pattern, source)]

def is_single_purpose(doc: str) -> bool:
    """Check if function does ONE thing based on documentation."""
    verbs = len(re.findall(r'\b(and|also|then|plus|additionally)\b', doc.lower()))
    return verbs == 0 and len(doc.split('.')) <= 2

def score_clarity(name: str, doc: str) -> float:
    """Rate name clarity: meaningful words / total length."""
    words = re.findall(r'[a-z]+', name.lower())
    meaningful = sum(1 for w in words if len(w) > 3)
    return meaningful / max(len(name), 1)

def catalog_primitives(module_paths: List[Path]) -> List[Dict]:
    """Build catalog of composable single-purpose functions."""
    primitives = []
    for path in module_paths:
        if not path.exists():
            continue
        source = path.read_text()
        for func in extract_functions(source):
            if is_single_purpose(func["doc"]):
                clarity = score_clarity(func["name"], func["doc"])
                if clarity > 0.3:
                    primitives.append({
                        "name": func["name"],
                        "module": path.stem,
                        "doc": func["doc"],
                        "clarity": clarity
                    })
    return sorted(primitives, key=lambda x: x["clarity"], reverse=True)

def write_catalog(primitives: List[Dict], output: Path):
    """Write primitives catalog as importable index."""
    with output.open('w') as f:
        f.write("# ALTHEA PRIMITIVE CATALOG\n# Single-purpose composable functions\n\n")
        for p in primitives:
            f.write(f"# {p['name']} — {p['doc']}\n")
            f.write(f"from {p['module']} import {p['name']}\n")

if __name__ == "__main__":
    modules = list(Path(".").glob("autonomous-*.py"))
    prims = catalog_primitives(modules)
    write_catalog(prims, Path("primitives.py"))
    print(f"Cataloged {len(prims)} single-purpose primitives")