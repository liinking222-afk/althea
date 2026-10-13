#!/usr/bin/env python3
import re
import sys
from collections import Counter
from pathlib import Path

def extract_function_signatures(filepath):
    """Parse file and yield (name, param_count) for each function."""
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Python: def name(params):
    py_pattern = r'def\s+(\w+)\s*\((.*?)\):'
    # JavaScript/TypeScript: function name(params) or name(params) =>
    js_pattern = r'(?:function\s+(\w+)\s*\((.*?)\)|(\w+)\s*=\s*\((.*?)\)\s*=>)'
    
    for match in re.finditer(py_pattern, content):
        name = match.group(1)
        params = [p.strip() for p in match.group(2).split(',') if p.strip() and p.strip() != 'self']
        yield (name, len(params))
    
    for match in re.finditer(js_pattern, content):
        name = match.group(1) or match.group(3)
        params_str = match.group(2) or match.group(4)
        params = [p.strip() for p in params_str.split(',') if p.strip()]
        yield (name, len(params))

def audit_arity(paths):
    """Report functions violating single-responsibility via high arity."""
    arity_counts = Counter()
    violations = []
    
    for path in paths:
        for name, arity in extract_function_signatures(path):
            arity_counts[arity] += 1
            if arity > 3:
                violations.append((path.name, name, arity))
    
    print("ARITY DISTRIBUTION:")
    for arity in sorted(arity_counts.keys()):
        print(f"  {arity} params: {arity_counts[arity]} functions")
    
    if violations:
        print("\nVIOLATIONS (arity > 3):")
        for file, func, arity in violations:
            print(f"  {file}::{func} has {arity} parameters")
    
    return len(violations)

if __name__ == '__main__':
    paths = [Path(p) for p in sys.argv[1:]] if len(sys.argv) > 1 else [Path('.')]
    files = []
    for p in paths:
        if p.is_file():
            files.append(p)
        elif p.is_dir():
            files.extend(p.rglob('*.py'))
            files.extend(p.rglob('*.js'))
            files.extend(p.rglob('*.ts'))
    
    violations = audit_arity(files)
    sys.exit(1 if violations > 0 else 0)