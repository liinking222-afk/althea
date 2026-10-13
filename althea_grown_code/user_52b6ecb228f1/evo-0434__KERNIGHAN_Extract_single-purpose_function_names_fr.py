#!/usr/bin/env python3
import re
from typing import List, Dict

def extract_function_names(trace: str) -> List[str]:
    """Extract potential function/module names from trace text."""
    pattern = r'\b[a-z][a-z0-9_]*[a-z0-9]\b'
    words = re.findall(pattern, trace.lower())
    return [w for w in words if len(w) > 3 and '_' in w]

def count_verbs(name: str) -> int:
    """Count action verbs in a function name."""
    verbs = {'get', 'set', 'add', 'remove', 'delete', 'create', 'update',
             'find', 'search', 'filter', 'map', 'reduce', 'check', 'validate',
             'parse', 'format', 'compute', 'render', 'build', 'extract',
             'construct', 'invert', 'weave', 'establish', 'detect', 'verify'}
    parts = name.split('_')
    return sum(1 for p in parts if p in verbs)

def has_clear_responsibility(name: str) -> bool:
    """Check if name describes exactly one responsibility."""
    verb_count = count_verbs(name)
    part_count = len(name.split('_'))
    return verb_count == 1 and 2 <= part_count <= 4

def audit_names(traces: List[str]) -> Dict[str, bool]:
    """Audit function names for Kernighan clarity."""
    results = {}
    for trace in traces:
        names = extract_function_names(trace)
        for name in names:
            if name not in results:
                results[name] = has_clear_responsibility(name)
    return results

def report_clarity(audit: Dict[str, bool]) -> None:
    """Print clarity audit report."""
    clear = [n for n, ok in audit.items() if ok]
    unclear = [n for n, ok in audit.items() if not ok]
    
    print(f"CLEAR ({len(clear)}): {', '.join(sorted(clear)[:5])}")
    print(f"NEEDS_REFACTOR ({len(unclear)}): {', '.join(sorted(unclear)[:5])}")
    print(f"CLARITY_RATIO: {len(clear)/(len(audit) or 1):.2f}")

if __name__ == '__main__':
    traces = [
        "semantic_inversion_layer extract_primitives",
        "trace_ancestry_reweaving fractal_render validate_loop",
        "construct_gradient_inversion_lattice verify_preconditions"
    ]
    audit = audit_names(traces)
    report_clarity(audit)