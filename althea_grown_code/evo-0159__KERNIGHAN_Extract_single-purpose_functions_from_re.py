#!/usr/bin/env python3
"""Function catalog extractor - one thing: list functions and their sizes."""

import re
import sys
from pathlib import Path
from typing import Iterator, Tuple

def extract_functions(code: str) -> Iterator[Tuple[str, int]]:
    """Yield (function_name, line_count) from code."""
    lines = code.split('\n')
    current_func = None
    start_line = 0
    indent_level = 0
    
    for i, line in enumerate(lines):
        stripped = line.lstrip()
        if not stripped or stripped.startswith('#'):
            continue
            
        match = re.match(r'^def\s+([a-zA-Z_][a-zA-Z0-9_]*)\s*\(', stripped)
        if match:
            if current_func:
                yield (current_func, i - start_line)
            current_func = match.group(1)
            start_line = i
            indent_level = len(line) - len(stripped)
        elif current_func and line and not line[0].isspace():
            yield (current_func, i - start_line)
            current_func = None
    
    if current_func:
        yield (current_func, len(lines) - start_line)

def catalog_file(filepath: Path) -> None:
    """Print function catalog for one file."""
    code = filepath.read_text()
    functions = list(extract_functions(code))
    
    if not functions:
        return
    
    print(f"{filepath}:")
    for name, lines in sorted(functions, key=lambda x: x[1]):
        print(f"  {name:30s} {lines:3d} lines")
    print()

def main():
    """Catalog functions in files or stdin."""
    if len(sys.argv) > 1:
        for path in sys.argv[1:]:
            catalog_file(Path(path))
    else:
        code = sys.stdin.read()
        for name, lines in extract_functions(code):
            print(f"{name:30s} {lines:3d} lines")

if __name__ == '__main__':
    main()