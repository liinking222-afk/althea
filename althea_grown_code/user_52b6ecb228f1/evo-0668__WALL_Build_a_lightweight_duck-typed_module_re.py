#!/usr/bin/env python3
import re
import json
import sys
from pathlib import Path
from typing import Dict, List, Any

def parse_module_header(content: str, filepath: str) -> Dict[str, Any]:
    """Extract INTENT/LANGUAGE/DELTA from any text file via regex."""
    intent_match = re.search(r'(?:^|\n)INTENT:\s*(.+?)(?:\n|$)', content, re.MULTILINE)
    lang_match = re.search(r'(?:^|\n)LANGUAGE:\s*(\w+)', content, re.MULTILINE)
    delta_match = re.search(r'(?:^|\n)DELTA:\s*(.+?)(?:\n|$)', content, re.MULTILINE)
    
    # Also try to extract module name from common patterns
    module_match = re.search(r'/([a-z0-9-]+(?:-\d+)?)\]', content)
    if not module_match:
        module_match = re.search(r'def\s+(\w+)|class\s+(\w+)|module\.exports\s*=.*?(\w+)', content)
    
    return {
        'path': str(filepath),
        'name': module_match.group(1) if module_match else Path(filepath).stem,
        'intent': intent_match.group(1).strip() if intent_match else None,
        'language': lang_match.group(1).lower() if lang_match else None,
        'delta': delta_match.group(1).strip() if delta_match else None,
        'valid': bool(intent_match and lang_match and delta_match)
    }

def scan_modules(paths: List[str]) -> List[Dict[str, Any]]:
    """Duck-typed scanner: reads any text-like file."""
    modules = []
    for path_str in paths:
        path = Path(path_str)
        if path.is_dir():
            files = list(path.rglob('*'))
        else:
            files = [path]
        
        for f in files:
            if f.is_file() and f.suffix in ['.py', '.js', '.ts', '.sh', '.md', '.txt', '.rs', '.go']:
                try:
                    content = f.read_text(encoding='utf-8', errors='ignore')
                    module = parse_module_header(content, f)
                    modules.append(module)
                except Exception:
                    pass  # Pragmatic: skip unreadable files
    
    return modules

def main():
    paths = sys.argv[1:] if len(sys.argv) > 1 else ['.']
    catalog = scan_modules(paths)
    
    print(json.dumps({
        'total': len(catalog),
        'valid': len([m for m in catalog if m['valid']]),
        'modules': catalog
    }, indent=2))

if __name__ == '__main__':
    main()