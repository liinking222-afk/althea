#!/usr/bin/env python3
import re
import sys
from pathlib import Path
from typing import List, Tuple

def count_responsibilities(func_body: str) -> int:
    """Count distinct responsibilities: loops, conditionals, state mutations, IO."""
    responsibilities = 0
    if re.search(r'\b(for|while)\b', func_body):
        responsibilities += 1
    if re.search(r'\bif\b', func_body):
        responsibilities += 1
    if re.search(r'(\.append|\.update|\[.*\]\s*=|self\.)', func_body):
        responsibilities += 1
    if re.search(r'(print|write|read|open|request)', func_body):
        responsibilities += 1
    return responsibilities

def extract_functions(code: str) -> List[Tuple[str, str, int]]:
    """Extract function definitions with their bodies and responsibility count."""
    pattern = r'def\s+(\w+)\([^)]*\):[^\n]*\n((?:    .*\n)*)'
    functions = []
    for match in re.finditer(pattern, code):
        name = match.group(1)
        body = match.group(2)
        resp_count = count_responsibilities(body)
        functions.append((name, body, resp_count))
    return functions

def suggest_decomposition(name: str, body: str) -> List[str]:
    """Suggest single-purpose extractions from multi-responsibility function."""
    suggestions = []
    if re.search(r'\bfor\b.*:.*\n.*if\b', body, re.DOTALL):
        suggestions.append(f"extract_{name}_filter")
    if re.search(r'(\.append|\.update)', body):
        suggestions.append(f"extract_{name}_accumulator")
    if re.search(r'(print|write)', body):
        suggestions.append(f"extract_{name}_output")
    return suggestions

def analyze_clarity(filepath: Path) -> dict:
    """Analyze code clarity through single-responsibility lens."""
    code = filepath.read_text()
    functions = extract_functions(code)
    
    report = {
        'file': filepath.name,
        'total_functions': len(functions),
        'clear_functions': sum(1 for _, _, r in functions if r <= 1),
        'bloated_functions': [(n, r, suggest_decomposition(n, b)) 
                              for n, b, r in functions if r > 2]
    }
    return report

def main():
    if len(sys.argv) < 2:
        print("Usage: clarity_extractor.py <file.py>")
        sys.exit(1)
    
    filepath = Path(sys.argv[1])
    report = analyze_clarity(filepath)
    
    print(f"CLARITY REPORT: {report['file']}")
    print(f"Clear (≤1 responsibility): {report['clear_functions']}/{report['total_functions']}")
    
    for name, resp, suggestions in report['bloated_functions']:
        print(f"\n⚠ {name}: {resp} responsibilities")
        for suggestion in suggestions:
            print(f"  → {suggestion}()")

if __name__ == '__main__':
    main()