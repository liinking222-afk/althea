#!/usr/bin/env python3
import re
import sys
from pathlib import Path
from typing import List, Tuple

def extract_functions(source: str) -> List[Tuple[str, str, int]]:
    """Parse source and return (name, signature, line_count) tuples."""
    pattern = r'(?:def|function|fn|func)\s+(\w+)\s*\(([^)]*)\)'
    matches = re.finditer(pattern, source, re.MULTILINE)
    results = []
    for match in matches:
        name = match.group(1)
        params = match.group(2).strip()
        start = match.end()
        end = source.find('\n\n', start)
        if end == -1:
            end = len(source)
        lines = source[start:end].count('\n')
        results.append((name, params, lines))
    return results

def score_complexity(name: str, params: str, lines: int) -> int:
    """Simple heuristic: fewer lines + fewer params = better."""
    param_count = len([p for p in params.split(',') if p.strip()])
    return lines + (param_count * 3)

def filter_single_responsibility(funcs: List[Tuple[str, str, int]]) -> List[str]:
    """Keep only functions under complexity threshold."""
    threshold = 25
    good = []
    for name, params, lines in funcs:
        complexity = score_complexity(name, params, lines)
        if complexity < threshold:
            sig = f"{name}({params})" if params else f"{name}()"
            good.append(sig)
    return good

def main():
    if len(sys.argv) < 2:
        source = sys.stdin.read()
    else:
        source = Path(sys.argv[1]).read_text()
    
    funcs = extract_functions(source)
    catalog = filter_single_responsibility(funcs)
    
    for sig in sorted(catalog):
        print(sig)

if __name__ == '__main__':
    main()