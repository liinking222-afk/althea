#!/usr/bin/env python3
"""Function extractor - splits multi-purpose modules into single-responsibility units."""

import ast
import sys
from pathlib import Path


def extract_function(code: str, func_name: str) -> str:
    """Extract one function with its dependencies into standalone module."""
    tree = ast.parse(code)
    imports = [n for n in ast.walk(tree) if isinstance(n, (ast.Import, ast.ImportFrom))]
    funcs = [n for n in tree.body if isinstance(n, ast.FunctionDef)]
    
    target = next((f for f in funcs if f.name == func_name), None)
    if not target:
        return ""
    
    lines = code.split('\n')
    extracted = [ast.unparse(imp) for imp in imports]
    extracted.append("")
    extracted.append(ast.unparse(target))
    
    return '\n'.join(extracted)


def list_functions(code: str) -> list[str]:
    """Return names of all top-level functions."""
    tree = ast.parse(code)
    return [n.name for n in tree.body if isinstance(n, ast.FunctionDef)]


def pipe_extract(source_path: str, target_func: str, output_path: str) -> None:
    """Read source, extract function, write to output - one purpose."""
    code = Path(source_path).read_text()
    extracted = extract_function(code, target_func)
    Path(output_path).write_text(extracted)


if __name__ == "__main__":
    if len(sys.argv) == 2:
        funcs = list_functions(Path(sys.argv[1]).read_text())
        print('\n'.join(funcs))
    elif len(sys.argv) == 4:
        pipe_extract(sys.argv[1], sys.argv[2], sys.argv[3])
    else:
        print("Usage: extract.py SOURCE [FUNC OUTPUT]")