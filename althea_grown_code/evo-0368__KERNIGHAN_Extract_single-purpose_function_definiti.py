#!/usr/bin/env python3
import re
from dataclasses import dataclass
from typing import List, Tuple

@dataclass
class FunctionMetric:
    name: str
    complexity: int
    purpose_count: int
    is_pure: bool

def extract_functions(code: str) -> List[str]:
    """Extract function definitions from code."""
    pattern = r'(?:def|function|fn|func)\s+(\w+)\s*\([^)]*\)\s*(?:->?[^{:]*)?[{:]([^}]*)'
    return re.findall(pattern, code, re.DOTALL)

def count_branches(body: str) -> int:
    """Count decision points (if, for, while, case, &&, ||)."""
    branches = len(re.findall(r'\b(if|for|while|switch|case|&&|\|\|)\b', body))
    return branches + 1

def count_verbs(name: str) -> int:
    """Count action verbs in function name (and, or, then suggest multiple purposes)."""
    conjunctions = ['and', 'or', 'then', 'also', 'plus']
    name_lower = name.lower()
    return sum(1 for c in conjunctions if c in name_lower) + 1

def has_side_effects(body: str) -> bool:
    """Detect mutation keywords."""
    mutations = r'\b(global|nonlocal|self\.\w+\s*=|print|write|append|update|delete)\b'
    return bool(re.search(mutations, body))

def analyze_function(name: str, body: str) -> FunctionMetric:
    """Analyze single function for Kernighan compliance."""
    return FunctionMetric(
        name=name,
        complexity=count_branches(body),
        purpose_count=count_verbs(name),
        is_pure=not has_side_effects(body)
    )

def check_kernighan_compliance(code: str) -> List[Tuple[str, str]]:
    """Return list of (function_name, violation_reason) for non-compliant functions."""
    functions = extract_functions(code)
    violations = []
    
    for name, body in functions:
        metric = analyze_function(name, body)
        
        if metric.complexity > 4:
            violations.append((name, f"complexity={metric.complexity} (max 4)"))
        if metric.purpose_count > 1:
            violations.append((name, f"does {metric.purpose_count} things (max 1)"))
    
    return violations

def pipe_report(violations: List[Tuple[str, str]]) -> str:
    """Format violations as pipe-able text."""
    if not violations:
        return "PASS: All functions do one thing\n"
    
    lines = [f"{name}\t{reason}" for name, reason in violations]
    return "\n".join(lines) + "\n"

if __name__ == "__main__":
    import sys
    code = sys.stdin.read()
    violations = check_kernighan_compliance(code)
    sys.stdout.write(pipe_report(violations))