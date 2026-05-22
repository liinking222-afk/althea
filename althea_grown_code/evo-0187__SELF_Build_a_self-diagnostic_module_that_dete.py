#!/usr/bin/env python3
"""
ALTHEA MODULE: intent_drift_detector.py
Analyzes gap between stated purpose and actual code behavior.
"""

import re
import json
from pathlib import Path
from typing import Dict, List, Tuple

def extract_intent_markers(code: str) -> List[str]:
    """Extract semantic markers from docstrings and comments."""
    markers = []
    markers.extend(re.findall(r'"""([^"]+)"""', code))
    markers.extend(re.findall(r'#\s*(.+)', code))
    markers.extend(re.findall(r'def\s+(\w+)', code))
    markers.extend(re.findall(r'class\s+(\w+)', code))
    return markers

def extract_implementation_markers(code: str) -> List[str]:
    """Extract actual behavioral signatures from code."""
    markers = []
    markers.extend(re.findall(r'import\s+([\w.]+)', code))
    markers.extend(re.findall(r'from\s+([\w.]+)', code))
    markers.extend(re.findall(r'(\w+)\s*=\s*', code))
    markers.extend(re.findall(r'return\s+(\w+)', code))
    return markers

def semantic_distance(intent_set: set, impl_set: set) -> float:
    """Calculate drift as normalized set difference."""
    if not intent_set:
        return 1.0
    overlap = len(intent_set & impl_set)
    union = len(intent_set | impl_set)
    return 1.0 - (overlap / union if union > 0 else 0)

def analyze_module(filepath: Path) -> Dict:
    """Detect intent-implementation drift in a module."""
    code = filepath.read_text()
    
    intent = set(extract_intent_markers(code))
    impl = set(extract_implementation_markers(code))
    
    drift = semantic_distance(intent, impl)
    
    missing_in_impl = intent - impl
    unexpected_in_impl = impl - intent
    
    return {
        'module': filepath.name,
        'drift_score': round(drift, 3),
        'intent_tokens': len(intent),
        'impl_tokens': len(impl),
        'missing': list(missing_in_impl)[:5],
        'unexpected': list(unexpected_in_impl)[:5],
        'diagnosis': 'HIGH_DRIFT' if drift > 0.7 else 'ALIGNED'
    }

def scan_recent_modules(module_dir: str = './modules') -> List[Dict]:
    """Scan recent modules for intent drift."""
    path = Path(module_dir)
    if not path.exists():
        return []
    
    results = []
    for pyfile in sorted(path.glob('*.py'))[-10:]:
        results.append(analyze_module(pyfile))
    
    return sorted(results, key=lambda x: x['drift_score'], reverse=True)

if __name__ == '__main__':
    drift_report = scan_recent_modules()
    print(json.dumps(drift_report, indent=2))