#!/usr/bin/env python3
import os
import re
from pathlib import Path

def scan_modules(base_path="."):
    """Scan filesystem for Althea modules using pure stdlib - no deps."""
    modules = []
    
    # Pattern for module headers in source files
    header_pattern = re.compile(
        r'^\s*#\s*MODULE:\s*(\S+)\s*\|\s*([^|]+)\s*\|\s*(.+)$',
        re.MULTILINE
    )
    
    # Pattern for intent markers
    intent_pattern = re.compile(r'INTENT:\s*(.+)$', re.MULTILINE)
    
    for root, dirs, files in os.walk(base_path):
        # Skip hidden and common ignore dirs
        dirs[:] = [d for d in dirs if not d.startswith('.') and d not in ['__pycache__', 'node_modules']]
        
        for file in files:
            if not (file.endswith('.py') or file.endswith('.js') or file.endswith('.sh')):
                continue
                
            filepath = Path(root) / file
            try:
                content = filepath.read_text(encoding='utf-8', errors='ignore')
                
                # Extract module metadata
                header_match = header_pattern.search(content)
                intent_match = intent_pattern.search(content)
                
                if header_match or intent_match:
                    modules.append({
                        'path': str(filepath),
                        'name': header_match.group(1) if header_match else filepath.stem,
                        'category': header_match.group(2).strip() if header_match else 'unknown',
                        'description': header_match.group(3).strip() if header_match else intent_match.group(1).strip() if intent_match else '',
                        'size': filepath.stat().st_size,
                        'lang': filepath.suffix[1:]
                    })
            except Exception:
                continue
    
    return sorted(modules, key=lambda m: m['name'])

def format_output(modules, format='human'):
    """Format module list - human, json, or tsv."""
    if format == 'json':
        import json
        return json.dumps(modules, indent=2)
    elif format == 'tsv':
        lines = ['name\tcategory\tsize\tlang\tpath']
        lines.extend(f"{m['name']}\t{m['category']}\t{m['size']}\t{m['lang']}\t{m['path']}" for m in modules)
        return '\n'.join(lines)
    else:
        lines = [f"Found {len(modules)} modules:"]
        for m in modules:
            lines.append(f"  [{m['category']}] {m['name']} ({m['size']}b {m['lang']}) - {m['description'][:60]}")
        return '\n'.join(lines)

if __name__ == '__main__':
    import sys
    fmt = sys.argv[1] if len(sys.argv) > 1 else 'human'
    modules = scan_modules()
    print(format_output(modules, fmt))