#!/usr/bin/env python3
"""Module registry inspector - list all Althea modules with their purposes."""

import os
import re
from pathlib import Path
from typing import List, Tuple

MODULE_DIRS = [
    "/home/althea/modules",
    "/home/althea/autonomous",
    "/home/althea/growth"
]

def extract_purpose(filepath: Path) -> str:
    """Extract first docstring or comment describing module purpose."""
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read(500)
            
        # Python docstring
        match = re.search(r'"""(.+?)"""', content, re.DOTALL)
        if match:
            return match.group(1).strip().split('\n')[0]
        
        # Comment header
        match = re.search(r'^#\s*(.+?)$', content, re.MULTILINE)
        if match:
            return match.group(1).strip()
            
        return "No description"
    except:
        return "Unable to read"

def find_modules() -> List[Tuple[str, str]]:
    """Find all module files and their purposes."""
    modules = []
    
    for dir_path in MODULE_DIRS:
        if not os.path.exists(dir_path):
            continue
            
        for filepath in Path(dir_path).rglob('*.py'):
            if filepath.name.startswith('_'):
                continue
            purpose = extract_purpose(filepath)
            modules.append((str(filepath), purpose))
    
    return sorted(modules)

def list_modules():
    """Print all modules with their purposes."""
    modules = find_modules()
    
    for path, purpose in modules:
        name = Path(path).stem
        print(f"{name}: {purpose}")

if __name__ == '__main__':
    list_modules()