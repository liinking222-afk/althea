#!/usr/bin/env python3
import re
import ast
from pathlib import Path
from typing import List, Tuple

def validate_function_name(name: str) -> Tuple[bool, str]:
    """Check if function name follows Kernighan clarity principles."""
    if len(name) < 3:
        return False, "too_short"
    if name.count('_') > 3:
        return False, "too_many_concepts"
    if re.search(r'(and|or|plus|with)', name, re.IGNORECASE):
        return False, "multiple_responsibilities"
    if not re.match(r'^[a-z_][a-z0-9_]*$', name):
        return False, "invalid_format"
    return True, "clear"

def extract_functions(filepath: Path) -> List[str]:
    """Parse Python file and return all function names."""
    try:
        tree = ast.parse(filepath.read_text())
        return [node.name for node in ast.walk(tree) if isinstance(node, ast.FunctionDef)]
    except:
        return []

def validate_module(filepath: Path) -> dict:
    """Validate all functions in a module against clarity principles."""
    functions = extract_functions(filepath)
    results = {"clear": [], "violations": []}
    
    for func in functions:
        if func.startswith('_'):
            continue
        valid, reason = validate_function_name(func)
        if valid:
            results["clear"].append(func)
        else:
            results["violations"].append({"name": func, "reason": reason})
    
    results["clarity_ratio"] = (
        len(results["clear"]) / len(functions) if functions else 1.0
    )
    return results

def scan_codebase(root: Path = Path(".")):
    """Scan all Python modules and report clarity metrics."""
    violations = []
    for pyfile in root.rglob("*.py"):
        result = validate_module(pyfile)
        if result["violations"]:
            violations.append({"file": str(pyfile), "data": result})
    
    if violations:
        print("CLARITY VIOLATIONS DETECTED:")
        for v in violations:
            print(f"\n{v['file']} (clarity: {v['data']['clarity_ratio']:.1%})")
            for issue in v["data"]["violations"]:
                print(f"  - {issue['name']}: {issue['reason']}")
    else:
        print("All functions meet Kernighan clarity standard.")

if __name__ == "__main__":
    scan_codebase()