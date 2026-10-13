#!/usr/bin/env python3
"""
ALTHEA MODULE: /autonomous-error-coverage-scanner
Scans installed modules for unguarded failure paths and missing error handlers.
"""

import os
import re
import ast
from pathlib import Path
from typing import Dict, List, Set

def scan_module_error_coverage(module_path: str) -> Dict[str, any]:
    """Analyze a Python module for error handling coverage."""
    try:
        with open(module_path, 'r') as f:
            source = f.read()
        
        tree = ast.parse(source)
        
        # Count functions and try-except blocks
        functions = []
        try_blocks = []
        raises = []
        
        for node in ast.walk(tree):
            if isinstance(node, ast.FunctionDef):
                functions.append(node.name)
            elif isinstance(node, ast.Try):
                try_blocks.append(node.lineno)
            elif isinstance(node, ast.Raise):
                raises.append(node.lineno)
        
        # Detect risky operations without guards
        risky_patterns = [
            (r'open\(', 'file_io'),
            (r'requests\.', 'network'),
            (r'json\.loads', 'parsing'),
            (r'\[.*\]', 'indexing'),
            (r'int\(|float\(', 'conversion'),
        ]
        
        unguarded_risks = []
        for pattern, risk_type in risky_patterns:
            for match in re.finditer(pattern, source):
                line_no = source[:match.start()].count('\n') + 1
                # Check if within try block range (simplified)
                unguarded_risks.append({
                    'line': line_no,
                    'type': risk_type
                })
        
        coverage_ratio = len(try_blocks) / max(len(functions), 1)
        
        return {
            'module': os.path.basename(module_path),
            'functions': len(functions),
            'try_blocks': len(try_blocks),
            'coverage_ratio': coverage_ratio,
            'unguarded_risks': len(unguarded_risks),
            'health_score': min(100, int(coverage_ratio * 50 + (1 - len(unguarded_risks)/10) * 50))
        }
    except Exception as e:
        return {'module': os.path.basename(module_path), 'error': str(e)}

def scan_all_modules(base_path: str = '.') -> List[Dict]:
    """Scan all Python modules in the base path."""
    results = []
    for py_file in Path(base_path).rglob('*.py'):
        if 'autonomous-' in str(py_file):
            results.append(scan_module_error_coverage(str(py_file)))
    return sorted(results, key=lambda x: x.get('health_score', 0))

if __name__ == '__main__':
    weak_modules = scan_all_modules()[:5]
    for mod in weak_modules:
        print(f"{mod.get('module')}: health={mod.get('health_score', 'N/A')}")