#!/usr/bin/env python3
import re
import ast
from typing import Dict, Tuple

def measure_elegance(code: str, lang: str = "python") -> Dict[str, float]:
    """Measure code elegance: semantic ops per byte (Wozniak metric)."""
    byte_count = len(code.encode('utf-8'))
    char_count = len(code)
    line_count = len([l for l in code.split('\n') if l.strip()])
    
    if lang == "python":
        try:
            tree = ast.parse(code)
            ops = sum(1 for _ in ast.walk(tree) if isinstance(_, (
                ast.FunctionDef, ast.ClassDef, ast.For, ast.While,
                ast.If, ast.BinOp, ast.UnaryOp, ast.Compare,
                ast.Call, ast.ListComp, ast.DictComp
            )))
        except:
            ops = len(re.findall(r'\bdef\b|\bclass\b|\bif\b|\bfor\b|\bwhile\b|[+\-*/%]|[=<>!]=?', code))
    else:
        ops = len(re.findall(r'\bfunction\b|\bclass\b|\bif\b|\bfor\b|\bwhile\b|[+\-*/%]|[=<>!]=?', code))
    
    return {
        "bytes": byte_count,
        "ops": ops,
        "density": ops / byte_count if byte_count > 0 else 0,
        "ops_per_line": ops / line_count if line_count > 0 else 0,
        "woz_score": (ops * ops) / (byte_count * line_count) if byte_count * line_count > 0 else 0
    }

def compress_hints(code: str) -> str:
    """Suggest compression opportunities."""
    hints = []
    if len(re.findall(r'\n\s*\n\s*\n', code)) > 0:
        hints.append("Remove excessive blank lines")
    if len(re.findall(r'#.*', code)) / len(code.split('\n')) > 0.3:
        hints.append("Comment ratio high - consider self-documenting code")
    if re.search(r'([a-z_]+)\s*=\s*\1\s*[+\-]', code):
        hints.append("Use augmented assignment (+=, -=)")
    if len(re.findall(r'\bfor\b.*\brange\(len\(', code)) > 0:
        hints.append("Replace range(len()) with enumerate() or direct iteration")
    return "; ".join(hints) if hints else "Code is tight"

def analyze(code: str, lang: str = "python") -> str:
    metrics = measure_elegance(code, lang)
    hints = compress_hints(code)
    return f"ELEGANCE METRICS:\n  Ops: {metrics['ops']}\n  Bytes: {metrics['bytes']}\n  Density: {metrics['density']:.4f} ops/byte\n  Woz Score: {metrics['woz_score']:.6f}\n  Hints: {hints}"

if __name__ == "__main__":
    import sys
    code = sys.stdin.read() if not sys.stdin.isatty() else sys.argv[1] if len(sys.argv) > 1 else ""
    if code:
        print(analyze(code))