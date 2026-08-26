#!/usr/bin/env python3
"""one_thing_validator.py - Verify modules do ONE thing (Kernighan principle)"""

import ast
import sys
from pathlib import Path
from typing import Tuple


def count_responsibilities(filepath: Path) -> Tuple[int, list]:
    """Count distinct responsibilities in a module."""
    with open(filepath) as f:
        tree = ast.parse(f.read())
    
    public_functions = []
    public_classes = []
    
    for node in ast.walk(tree):
        if isinstance(node, ast.FunctionDef):
            if not node.name.startswith('_'):
                public_functions.append(node.name)
        elif isinstance(node, ast.ClassDef):
            if not node.name.startswith('_'):
                public_classes.append(node.name)
    
    responsibilities = len(public_functions) + len(public_classes)
    items = public_functions + public_classes
    
    return responsibilities, items


def validate_one_thing(filepath: Path) -> bool:
    """Return True if module does ONE thing."""
    count, items = count_responsibilities(filepath)
    
    if count == 0:
        print(f"❌ {filepath.name}: No public interface")
        return False
    elif count == 1:
        print(f"✓ {filepath.name}: Does ONE thing ({items[0]})")
        return True
    else:
        print(f"❌ {filepath.name}: Does {count} things: {', '.join(items)}")
        return False


def main():
    if len(sys.argv) < 2:
        print("Usage: one_thing_validator.py <module.py> [...]")
        sys.exit(1)
    
    results = []
    for path_str in sys.argv[1:]:
        path = Path(path_str)
        if path.exists() and path.suffix == '.py':
            results.append(validate_one_thing(path))
    
    passed = sum(results)
    total = len(results)
    print(f"\n{passed}/{total} modules follow ONE THING principle")
    
    sys.exit(0 if passed == total else 1)


if __name__ == "__main__":
    main()