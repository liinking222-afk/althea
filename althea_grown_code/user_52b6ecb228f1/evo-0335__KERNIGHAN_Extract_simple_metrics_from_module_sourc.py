#!/usr/bin/env python3
import re
import sys
from pathlib import Path

def count_functions(content):
    """Count function definitions."""
    return len(re.findall(r'^\s*(?:def|function|fn|func)\s+\w+', content, re.MULTILINE))

def count_responsibilities(content):
    """Count distinct action verbs in function names as responsibility proxy."""
    funcs = re.findall(r'(?:def|function|fn|func)\s+(\w+)', content)
    verbs = set()
    for name in funcs:
        # Extract first verb-like token
        parts = re.split(r'[_-]', name.lower())
        if parts:
            verbs.add(parts[0])
    return len(verbs)

def avg_function_length(content):
    """Estimate average lines per function."""
    func_count = count_functions(content)
    if func_count == 0:
        return 0
    lines = len([l for l in content.split('\n') if l.strip() and not l.strip().startswith('#')])
    return lines / func_count

def measure_clarity(filepath):
    """Measure Kernighan-style clarity metrics for a module."""
    content = Path(filepath).read_text()
    funcs = count_functions(content)
    responsibilities = count_responsibilities(content)
    avg_len = avg_function_length(content)
    
    # Clarity score: more functions, fewer responsibilities per func, shorter funcs
    if funcs == 0:
        score = 0
    else:
        score = min(100, int((funcs / max(1, responsibilities)) * (20 / max(5, avg_len)) * 100))
    
    return {
        'functions': funcs,
        'responsibilities': responsibilities,
        'avg_lines_per_function': round(avg_len, 1),
        'clarity_score': score
    }

if __name__ == '__main__':
    if len(sys.argv) < 2:
        print("Usage: clarity_meter.py <filepath>")
        sys.exit(1)
    
    metrics = measure_clarity(sys.argv[1])
    for k, v in metrics.items():
        print(f"{k}: {v}")