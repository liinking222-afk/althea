#!/usr/bin/env python3
"""signature_manifest.py - Extract clean function signatures from code modules"""

import ast
import sys
from pathlib import Path
from typing import List, Tuple


def extract_signatures(source_code: str) -> List[Tuple[str, str]]:
    """Parse source and return [(name, signature), ...] tuples."""
    try:
        tree = ast.parse(source_code)
    except SyntaxError:
        return []
    
    signatures = []
    for node in ast.walk(tree):
        if isinstance(node, ast.FunctionDef):
            args = []
            for arg in node.args.args:
                annotation = ast.unparse(arg.annotation) if arg.annotation else ""
                args.append(f"{arg.arg}: {annotation}" if annotation else arg.arg)
            
            returns = ast.unparse(node.returns) if node.returns else ""
            sig = f"({', '.join(args)})"
            if returns:
                sig += f" -> {returns}"
            
            signatures.append((node.name, sig))
    
    return signatures


def manifest(filepath: str) -> str:
    """Generate manifest from file path."""
    path = Path(filepath)
    if not path.exists():
        return f"# ERROR: {filepath} not found"
    
    source = path.read_text()
    sigs = extract_signatures(source)
    
    lines = [f"# MANIFEST: {path.name}", ""]
    for name, sig in sigs:
        lines.append(f"{name}{sig}")
    
    return "\n".join(lines)


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("usage: signature_manifest.py <file.py>")
        sys.exit(1)
    
    print(manifest(sys.argv[1]))