#!/usr/bin/env python3
import re
from pathlib import Path
from collections import defaultdict

def extract_functions(content):
    """Find function definitions and their bodies."""
    pattern = r'(?:def|function|fn|func)\s+(\w+)\s*\([^)]*\)\s*(?:->|:)?\s*(?:\w+\s*)?{?([^}]*?)(?:}|\n(?=\S))'
    return re.findall(pattern, content, re.DOTALL)

def count_actions(body):
    """Count distinct verb-noun pairs indicating separate responsibilities."""
    verbs = r'\b(create|build|check|validate|parse|transform|send|receive|store|load|save|update|delete|process|calculate|compute|filter|map|reduce|sort|find|search|verify|init|start|stop|execute|run|call|invoke|render|draw|write|read|fetch|push|pull|commit|merge|split|join|scan|inject|extract|measure|track|log|emit|dispatch|handle|manage|control|set|get|add|remove|insert|append|clear|reset|open|close|lock|unlock|encode|decode|compress|expand|format|normalize|sanitize|analyze|detect|resolve|allocate|release)\w*'
    
    actions = re.findall(verbs, body.lower())
    return len(set(actions))

def measure_file(filepath):
    """Analyze single file for SRP violations."""
    content = Path(filepath).read_text()
    functions = extract_functions(content)
    violations = []
    
    for name, body in functions:
        action_count = count_actions(body)
        if action_count > 3:
            violations.append((name, action_count))
    
    return violations

def scan_directory(directory):
    """Scan all code files in directory tree."""
    extensions = {'.py', '.js', '.ts', '.rs', '.go', '.c', '.cpp'}
    results = defaultdict(list)
    
    for path in Path(directory).rglob('*'):
        if path.suffix in extensions and path.is_file():
            violations = measure_file(path)
            if violations:
                results[str(path)] = violations
    
    return results

def report(results):
    """Output violations sorted by severity."""
    all_violations = []
    for filepath, violations in results.items():
        for fname, count in violations:
            all_violations.append((count, filepath, fname))
    
    all_violations.sort(reverse=True)
    
    for count, filepath, fname in all_violations:
        print(f"{count:2d} actions | {filepath}::{fname}")

if __name__ == '__main__':
    import sys
    directory = sys.argv[1] if len(sys.argv) > 1 else '.'
    results = scan_directory(directory)
    report(results)