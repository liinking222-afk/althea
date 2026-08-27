#!/usr/bin/env python3
"""kernighan_extract.py - Pure function extraction and composition utility"""

import re
from pathlib import Path
from typing import List, Tuple

def read_module(filepath: str) -> str:
    """Read a Python module file."""
    return Path(filepath).read_text()

def find_function_blocks(source: str) -> List[Tuple[str, str]]:
    """Extract function definitions with their bodies."""
    pattern = r'^def\s+(\w+)\([^)]*\)(?:\s*->\s*[^:]+)?:\s*\n((?:(?:    |\t).+\n?)*)'
    return re.findall(pattern, source, re.MULTILINE)

def is_pure_candidate(name: str, body: str) -> bool:
    """Check if function appears side-effect-free."""
    impure_markers = ['print(', 'open(', 'write(', 'global ', '.append(', 
                      'requests.', 'os.', 'sys.', 'random.seed']
    return not any(marker in body for marker in impure_markers)

def measure_complexity(body: str) -> int:
    """Count decision points as complexity measure."""
    return body.count('if ') + body.count('for ') + body.count('while ')

def extract_single_purpose(functions: List[Tuple[str, str]]) -> List[Tuple[str, str, int]]:
    """Filter to simple, pure, single-purpose functions."""
    candidates = []
    for name, body in functions:
        if is_pure_candidate(name, body):
            complexity = measure_complexity(body)
            if complexity <= 3:  # Kernighan threshold
                candidates.append((name, body, complexity))
    return sorted(candidates, key=lambda x: x[2])

def compose_library(functions: List[Tuple[str, str, int]], module_name: str) -> str:
    """Build a clean utility library from extracted functions."""
    header = f'"""Pure utilities extracted from {module_name}"""\n\n'
    function_defs = []
    for name, body, _ in functions:
        function_defs.append(f"def {name}(...):\n{body}\n")
    return header + "\n".join(function_defs)

def pipeline(source_path: str, output_path: str) -> int:
    """Extract → Filter → Compose → Write pipeline."""
    source = read_module(source_path)
    functions = find_function_blocks(source)
    pure_simple = extract_single_purpose(functions)
    library = compose_library(pure_simple, Path(source_path).name)
    Path(output_path).write_text(library)
    return len(pure_simple)

if __name__ == "__main__":
    import sys
    extracted = pipeline(sys.argv[1], sys.argv[2])
    print(f"{extracted}")