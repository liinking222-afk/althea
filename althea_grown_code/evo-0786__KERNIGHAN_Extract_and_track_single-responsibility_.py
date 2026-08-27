#!/usr/bin/env python3
"""function_census.py - Map every function to its ONE responsibility."""

import ast
import re
from pathlib import Path
from dataclasses import dataclass
from typing import List, Dict

@dataclass
class FunctionProfile:
    name: str
    module: str
    loc: int
    branches: int
    calls: int
    responsibility: str

def count_branches(node):
    return sum(1 for _ in ast.walk(node) if isinstance(_, (ast.If, ast.For, ast.While, ast.Match)))

def count_calls(node):
    return sum(1 for _ in ast.walk(node) if isinstance(_, ast.Call))

def infer_responsibility(name, loc, branches, calls):
    """One sentence = one responsibility."""
    if branches > 5: return "TOO_COMPLEX"
    if loc > 50: return "TOO_LONG"
    words = re.findall(r'[a-z]+', name.lower())
    if len(words) == 1: return words[0]
    return '_'.join(words[:3])

def census_module(path: Path) -> List[FunctionProfile]:
    tree = ast.parse(path.read_text())
    profiles = []
    
    for node in ast.walk(tree):
        if isinstance(node, ast.FunctionDef):
            loc = node.end_lineno - node.lineno if node.end_lineno else 0
            branches = count_branches(node)
            calls = count_calls(node)
            resp = infer_responsibility(node.name, loc, branches, calls)
            
            profiles.append(FunctionProfile(
                name=node.name,
                module=path.stem,
                loc=loc,
                branches=branches,
                calls=calls,
                responsibility=resp
            ))
    
    return profiles

def find_composable_pairs(profiles: List[FunctionProfile]) -> List[tuple]:
    """Functions with same responsibility should pipe together."""
    by_resp = {}
    for p in profiles:
        by_resp.setdefault(p.responsibility, []).append(p)
    
    pairs = []
    for resp, funcs in by_resp.items():
        if len(funcs) > 1 and resp not in ("TOO_COMPLEX", "TOO_LONG"):
            pairs.append((resp, [f.name for f in funcs]))
    
    return pairs

if __name__ == "__main__":
    root = Path("/modules")
    all_profiles = []
    
    for py_file in root.rglob("*.py"):
        try:
            all_profiles.extend(census_module(py_file))
        except:
            pass
    
    print("FUNCTION CENSUS")
    print("=" * 60)
    for p in sorted(all_profiles, key=lambda x: x.responsibility):
        flag = "⚠️ " if p.responsibility.startswith("TOO_") else ""
        print(f"{flag}{p.module}.{p.name}: {p.responsibility} (loc={p.loc}, branches={p.branches})")
    
    print("\nCOMPOSABLE CLUSTERS")
    print("=" * 60)
    for resp, names in find_composable_pairs(all_profiles):
        print(f"{resp}: {' | '.join(names)}")