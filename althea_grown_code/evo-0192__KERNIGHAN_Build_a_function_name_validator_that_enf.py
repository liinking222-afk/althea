#!/usr/bin/env python3
"""name_clarity_validator.py - Enforce Kernighan naming: one function, one purpose."""

import re
from pathlib import Path
from typing import List, Tuple

CONJUNCTIONS = {'and', 'or', 'then', 'also', 'plus', 'with'}
MULTI_PURPOSE_PATTERNS = [
    r'_and_',
    r'_or_',
    r'_then_',
    r'_also_',
    r'_plus_',
    r'_with_',
]

def extract_functions(code: str, language: str) -> List[str]:
    """Extract function names from code."""
    if language == 'python':
        pattern = r'def\s+([a-z_][a-z0-9_]*)\s*\('
    elif language in ['javascript', 'typescript']:
        pattern = r'function\s+([a-z_][a-z0-9_]*)\s*\(|const\s+([a-z_][a-z0-9_]*)\s*=\s*\('
    else:
        return []
    
    matches = re.finditer(pattern, code, re.IGNORECASE)
    return [m.group(1) or m.group(2) for m in matches if m.group(1) or m.group(2)]

def validate_name(name: str) -> Tuple[bool, str]:
    """Check if function name suggests single responsibility."""
    parts = name.split('_')
    
    for conj in CONJUNCTIONS:
        if conj in parts:
            return False, f"Contains conjunction '{conj}' - likely multiple responsibilities"
    
    for pattern in MULTI_PURPOSE_PATTERNS:
        if re.search(pattern, name):
            return False, f"Pattern '{pattern}' suggests coupling"
    
    if len(parts) > 5:
        return False, f"Name too long ({len(parts)} parts) - may do too much"
    
    return True, "Clear single-purpose name"

def scan_file(filepath: Path) -> List[Tuple[str, str, str]]:
    """Scan file for multi-purpose function names."""
    violations = []
    code = filepath.read_text()
    ext = filepath.suffix
    
    lang_map = {'.py': 'python', '.js': 'javascript', '.ts': 'typescript'}
    language = lang_map.get(ext)
    
    if not language:
        return violations
    
    functions = extract_functions(code, language)
    
    for func_name in functions:
        is_valid, reason = validate_name(func_name)
        if not is_valid:
            violations.append((str(filepath), func_name, reason))
    
    return violations

if __name__ == '__main__':
    import sys
    target = Path(sys.argv[1]) if len(sys.argv) > 1 else Path('.')
    
    for violation in scan_file(target) if target.is_file() else \
                     [v for f in target.rglob('*.py') for v in scan_file(f)]:
        print(f"{violation[0]}:{violation[1]} - {violation[2]}")