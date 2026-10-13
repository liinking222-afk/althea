#!/usr/bin/env python3
import sys
import json
import re
from pathlib import Path

def parse_manifest(content):
    """Duck-typed parser: try JSON, YAML-ish, TOML-ish, or key-value."""
    content = content.strip()
    
    # Try JSON first
    try:
        return json.loads(content)
    except:
        pass
    
    # Fall back to regex-based key-value extraction (WALL style)
    manifest = {}
    
    # Extract name
    if m := re.search(r'(?:name|module|id)\s*[:=]\s*["\']?([^"\'\n]+)', content, re.I):
        manifest['name'] = m.group(1).strip()
    
    # Extract entry point
    if m := re.search(r'(?:entry|entrypoint|exec|command)\s*[:=]\s*["\']?([^"\'\n]+)', content, re.I):
        manifest['entry'] = m.group(1).strip()
    
    # Extract params (greedy list)
    params = re.findall(r'(?:param|arg|input)\s*[:=]\s*["\']?([^"\'\n]+)', content, re.I)
    if params:
        manifest['params'] = params
    
    # Extract description
    if m := re.search(r'(?:desc|description|about)\s*[:=]\s*["\']?([^"\'\n]+)', content, re.I):
        manifest['description'] = m.group(1).strip()
    
    return manifest if manifest else None

def emit_invocation(manifest):
    """Generate shell-invocable command from manifest."""
    if not manifest:
        return None
    
    name = manifest.get('name', 'unnamed')
    entry = manifest.get('entry', f'./{name}')
    params = manifest.get('params', [])
    desc = manifest.get('description', '')
    
    # Build invocation template
    param_placeholders = ' '.join(f'${{{p}}}' for p in params) if params else ''
    cmd = f"{entry} {param_placeholders}".strip()
    
    return {
        'name': name,
        'invocation': cmd,
        'description': desc,
        'params': params
    }

def main():
    manifests = sys.stdin.read().split('\n---\n')
    
    for raw in manifests:
        if not raw.strip():
            continue
        
        parsed = parse_manifest(raw)
        recipe = emit_invocation(parsed)
        
        if recipe:
            print(json.dumps(recipe, indent=2))
            print('---')

if __name__ == '__main__':
    main()