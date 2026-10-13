#!/usr/bin/env python3
import re
from typing import Dict, List, Tuple

def extract_functions(code: str) -> List[Dict[str, str]]:
    """Extract function definitions with their names and bodies."""
    pattern = r'def\s+([a-zA-Z_][a-zA-Z0-9_]*)\s*\([^)]*\):[^\n]*\n((?:\s+.*\n)*)'
    matches = re.findall(pattern, code)
    return [{"name": name, "body": body} for name, body in matches]

def count_responsibilities(body: str) -> int:
    """Count distinct responsibilities by counting branching and loops."""
    stripped = re.sub(r'#.*', '', body)
    conditionals = len(re.findall(r'\bif\b', stripped))
    loops = len(re.findall(r'\b(for|while)\b', stripped))
    returns = len(re.findall(r'\breturn\b', stripped))
    calls = len(set(re.findall(r'([a-zA-Z_][a-zA-Z0-9_]*)\s*\(', stripped)))
    return conditionals + loops + max(0, returns - 1) + max(0, calls - 3)

def name_clarity_score(name: str) -> float:
    """Score name clarity: verb_noun pattern, length, underscores."""
    if len(name) < 3:
        return 0.0
    has_verb = bool(re.match(r'^(get|set|is|has|make|create|build|find|parse|validate|extract|count|load|save|run|check|compute)', name))
    has_underscore = '_' in name
    length_ok = 4 <= len(name) <= 30
    return (0.5 if has_verb else 0.0) + (0.3 if has_underscore else 0.0) + (0.2 if length_ok else 0.0)

def analyze_function_purity(func: Dict[str, str]) -> Dict[str, any]:
    """Judge if function follows Kernighan principle."""
    name = func["name"]
    body = func["body"]
    responsibilities = count_responsibilities(body)
    clarity = name_clarity_score(name)
    lines = len([l for l in body.split('\n') if l.strip() and not l.strip().startswith('#')])
    
    return {
        "name": name,
        "responsibilities": responsibilities,
        "clarity": clarity,
        "lines": lines,
        "pure": responsibilities <= 2 and clarity >= 0.5 and lines <= 15,
        "verdict": "CLEAR" if responsibilities <= 2 and clarity >= 0.5 else "REFACTOR"
    }

def kernighan_audit(code: str) -> List[Dict[str, any]]:
    """Audit code for Kernighan compliance: one thing, clear names."""
    functions = extract_functions(code)
    return [analyze_function_purity(f) for f in functions]

def report(results: List[Dict[str, any]]) -> str:
    """Generate plain text audit report."""
    lines = ["KERNIGHAN AUDIT", "=" * 40]
    for r in results:
        status = "✓" if r["verdict"] == "CLEAR" else "✗"
        lines.append(f"{status} {r['name']}: {r['responsibilities']} tasks, clarity={r['clarity']:.1f}, {r['lines']}L")
    pure_count = sum(1 for r in results if r["pure"])
    lines.append(f"\n{pure_count}/{len(results)} functions follow the principle")
    return "\n".join(lines)