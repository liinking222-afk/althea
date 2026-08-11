#!/usr/bin/env python3
import re
from pathlib import Path
from collections import Counter

def analyze_module_density(module_path):
    """Woz-style: maximum insight, minimum machinery."""
    content = Path(module_path).read_text()
    lines = content.split('\n')
    
    metrics = {
        'total_bytes': len(content),
        'code_lines': len([l for l in lines if l.strip() and not l.strip().startswith('#')]),
        'density_score': 0,
        'hotspots': []
    }
    
    # Detect cognitive primitives with single-pass regex
    patterns = {
        'recursion': r'\bdef\s+(\w+).*?:\s*(?:.*?\n)*?.*?\1\s*\(',
        'state_mutation': r'self\.\w+\s*=',
        'branching': r'\b(if|elif|match|case)\b',
        'loops': r'\b(for|while)\b',
        'lambdas': r'\blambda\b',
        'comprehensions': r'\[.+\bfor\b.+\]|\{.+\bfor\b.+\}',
    }
    
    weights = Counter()
    for name, pattern in patterns.items():
        matches = re.findall(pattern, content, re.MULTILINE | re.DOTALL)
        count = len(matches)
        weights[name] = count
    
    # Calculate density: complexity per byte
    total_complexity = sum(weights.values())
    metrics['density_score'] = total_complexity / max(metrics['total_bytes'], 1) * 1000
    
    # Identify hotspots: line ranges with high primitive concentration
    window_size = 10
    for i in range(0, len(lines) - window_size):
        window = '\n'.join(lines[i:i+window_size])
        window_complexity = sum(
            len(re.findall(p, window, re.MULTILINE | re.DOTALL))
            for p in patterns.values()
        )
        if window_complexity >= 5:
            metrics['hotspots'].append({
                'lines': (i+1, i+window_size+1),
                'complexity': window_complexity
            })
    
    # Bytes per cognitive primitive (Woz efficiency metric)
    metrics['bytes_per_primitive'] = (
        metrics['total_bytes'] / total_complexity if total_complexity > 0 else float('inf')
    )
    metrics['primitive_counts'] = dict(weights)
    
    return metrics

def compare_modules(module_paths):
    """Find the most Woz-efficient module: most cognition, fewest bytes."""
    results = {}
    for path in module_paths:
        if Path(path).exists():
            results[path] = analyze_module_density(path)
    
    # Rank by density score (higher = more cognitive work per byte)
    ranked = sorted(results.items(), key=lambda x: x[1]['density_score'], reverse=True)
    return ranked

if __name__ == '__main__':
    import sys
    if len(sys.argv) > 1:
        results = analyze_module_density(sys.argv[1])
        print(f"Density: {results['density_score']:.2f} primitives/KB")
        print(f"Efficiency: {results['bytes_per_primitive']:.1f} bytes/primitive")
        print(f"Hotspots: {len(results['hotspots'])}")