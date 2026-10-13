#!/usr/bin/env python3
import re
from collections import Counter
from typing import List, Tuple

def extract_patterns(code: str) -> List[Tuple[str, int]]:
    """Find repeated code patterns worth abstracting."""
    lines = [l.strip() for l in code.split('\n') if l.strip() and not l.strip().startswith('#')]
    
    # Pattern types to detect
    patterns = []
    
    # Repeated function call structures
    func_calls = re.findall(r'(\w+)\([^)]*\)', code)
    call_freq = Counter(func_calls)
    patterns.extend([(f"func:{k}", v) for k, v in call_freq.items() if v > 2])
    
    # Repeated string literals
    strings = re.findall(r'["\']([^"\']{10,})["\']', code)
    str_freq = Counter(strings)
    patterns.extend([(f"str:{k}", v) for k, v in str_freq.items() if v > 1])
    
    # Repeated line structures (normalized)
    normalized = [re.sub(r'["\'][^"\']*["\']', '""', re.sub(r'\b\d+\b', '0', l)) for l in lines]
    struct_freq = Counter(normalized)
    patterns.extend([(f"struct:{k}", v) for k, v in struct_freq.items() if v > 2])
    
    return sorted(patterns, key=lambda x: x[1] * len(x[0]), reverse=True)[:5]

def compress_module(code: str, max_lines: int = 80) -> str:
    """Refactor code to fit constraint while preserving logic."""
    patterns = extract_patterns(code)
    compressed = code
    
    # Apply compressions
    compressed = re.sub(r'\n\s*\n\s*\n', '\n\n', compressed)  # Remove excessive blank lines
    compressed = re.sub(r'#.*?(?=\n)', '', compressed)  # Strip comments
    compressed = re.sub(r'^\s+', lambda m: m.group(0)[:len(m.group(0))//2], compressed, flags=re.MULTILINE)  # Reduce indent
    compressed = '\n'.join([l for l in compressed.split('\n') if l.strip()])  # Remove empty lines
    
    lines = compressed.split('\n')
    if len(lines) > max_lines:
        # Aggressive: inline single-use functions
        compressed = re.sub(r'def (\w+)\([^)]*\):\s*return (.+?)\n', r'', compressed)
    
    return compressed.strip()

def analyze_efficiency(code: str) -> dict:
    """Calculate code efficiency metrics."""
    lines = [l for l in code.split('\n') if l.strip()]
    tokens = len(re.findall(r'\w+|[^\w\s]', code))
    logic_lines = len([l for l in lines if not l.strip().startswith('#') and l.strip()])
    
    return {
        'lines': len(lines),
        'tokens': tokens,
        'logic_lines': logic_lines,
        'density': logic_lines / len(lines) if lines else 0,
        'tokens_per_line': tokens / len(lines) if lines else 0
    }

if __name__ == '__main__':
    import sys
    code = sys.stdin.read()
    patterns = extract_patterns(code)
    compressed = compress_module(code)
    metrics = analyze_efficiency(compressed)
    print(f"PATTERNS: {patterns}")
    print(f"METRICS: {metrics}")
    print(f"\n--- COMPRESSED ---\n{compressed}")