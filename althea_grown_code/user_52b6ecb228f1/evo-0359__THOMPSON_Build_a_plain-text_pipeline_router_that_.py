#!/usr/bin/env python3
import sys
import json
import re

def parse_manifest_line(line):
    """Extract module metadata from evolution/growth log lines."""
    patterns = [
        r'\[(?:EVO|GROWTH|AUTOSYNTH)\s+([^\]]+)\]\s+([^—\.]+)',
        r'(\S+)\s+\(([^)]+)\)\.\s+(.+?)(?:\s+—|$)',
    ]
    
    for pattern in patterns:
        match = re.search(pattern, line)
        if match:
            return match.groups()
    return None

def manifest_to_command(line):
    """Convert a manifest entry to a shell-invocable command spec."""
    parsed = parse_manifest_line(line)
    if not parsed:
        return None
    
    path_or_id = parsed[0].strip()
    slug = re.sub(r'[^\w-]', '_', path_or_id.lower())
    
    return {
        'command': slug,
        'path': path_or_id,
        'raw': line.strip()
    }

def main():
    """Read manifests from stdin, output JSON command catalog to stdout."""
    commands = []
    
    for line in sys.stdin:
        line = line.strip()
        if not line or line.startswith('#'):
            continue
            
        cmd = manifest_to_command(line)
        if cmd:
            commands.append(cmd)
    
    catalog = {
        'version': '1.0',
        'count': len(commands),
        'commands': commands
    }
    
    print(json.dumps(catalog, indent=2))

if __name__ == '__main__':
    main()