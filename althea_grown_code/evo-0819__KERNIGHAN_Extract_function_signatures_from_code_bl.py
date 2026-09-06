#!/usr/bin/env python3
import re
from typing import List, Dict, Optional

def extract_function_signatures(code: str, language: str) -> List[Dict[str, str]]:
    """Extract function signatures from code."""
    patterns = {
        'python': r'def\s+([a-zA-Z_][a-zA-Z0-9_]*)\s*\([^)]*\)\s*(?:->.*?)?:',
        'javascript': r'function\s+([a-zA-Z_][a-zA-Z0-9_]*)\s*\([^)]*\)',
        'typescript': r'function\s+([a-zA-Z_][a-zA-Z0-9_]*)\s*\([^)]*\)',
        'rust': r'fn\s+([a-zA-Z_][a-zA-Z0-9_]*)\s*\([^)]*\)',
        'go': r'func\s+([a-zA-Z_][a-zA-Z0-9_]*)\s*\([^)]*\)',
    }
    
    pattern = patterns.get(language.lower())
    if not pattern:
        return []
    
    matches = re.finditer(pattern, code)
    return [{'name': m.group(1), 'signature': m.group(0)} for m in matches]

def count_concerns(func_name: str) -> int:
    """Count concerns implied by function name using connectives."""
    separators = ['_and_', '_or_', '_then_', '_with_', 'And', 'Or', 'Then', 'With']
    concern_count = 1
    lower_name = func_name.lower()
    
    for sep in separators:
        concern_count += lower_name.count(sep.lower())
    
    return concern_count

def audit_single_responsibility(code: str, language: str) -> Dict:
    """Audit code for single responsibility principle."""
    funcs = extract_function_signatures(code, language)
    violations = []
    
    for func in funcs:
        concerns = count_concerns(func['name'])
        if concerns > 1:
            violations.append({
                'name': func['name'],
                'concerns': concerns,
                'signature': func['signature']
            })
    
    return {
        'total_functions': len(funcs),
        'violations': violations,
        'compliance_rate': 1.0 - (len(violations) / len(funcs)) if funcs else 1.0
    }

if __name__ == '__main__':
    import sys
    code = sys.stdin.read()
    language = sys.argv[1] if len(sys.argv) > 1 else 'python'
    result = audit_single_responsibility(code, language)
    print(f"Functions: {result['total_functions']}")
    print(f"Violations: {len(result['violations'])}")
    print(f"Compliance: {result['compliance_rate']:.1%}")
    for v in result['violations']:
        print(f"  ⚠ {v['name']} ({v['concerns']} concerns)")