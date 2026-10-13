#!/usr/bin/env python3
import re
from typing import List, Tuple

def extract_functions(code: str) -> List[Tuple[str, List[str]]]:
    """Parse function definitions and their internal operations."""
    func_pattern = r'^def\s+(\w+)\([^)]*\):'
    functions = []
    current_func = None
    operations = []
    
    for line in code.split('\n'):
        match = re.match(func_pattern, line.strip())
        if match:
            if current_func:
                functions.append((current_func, operations))
            current_func = match.group(1)
            operations = []
        elif current_func and line.strip() and not line.strip().startswith('#'):
            operations.append(line.strip())
    
    if current_func:
        functions.append((current_func, operations))
    
    return functions

def count_concerns(operations: List[str]) -> int:
    """Count distinct concerns via verb diversity in operations."""
    verbs = set()
    for op in operations:
        tokens = re.findall(r'\w+', op)
        if tokens:
            verbs.add(tokens[0])
    return len(verbs)

def report_violations(code: str, threshold: int = 3) -> str:
    """Report functions exceeding concern threshold."""
    functions = extract_functions(code)
    violations = []
    
    for name, ops in functions:
        concerns = count_concerns(ops)
        if concerns > threshold:
            violations.append(f"{name}: {concerns} concerns (limit {threshold})")
    
    return '\n'.join(violations) if violations else "ALL_CLEAR"

if __name__ == '__main__':
    import sys
    code = sys.stdin.read()
    print(report_violations(code))