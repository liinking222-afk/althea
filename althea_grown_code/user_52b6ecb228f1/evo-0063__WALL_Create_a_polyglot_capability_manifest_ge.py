#!/usr/bin/env python3
import re
import sys
import json

def parse_capabilities(memory_text):
    """Extract capabilities with multiple regex patterns for flexibility."""
    caps = []
    
    # Pattern 1: [EVO #N ARCH vX→vY] description
    for match in re.finditer(r'\[EVO #(\d+) (\w+) v([\d.]+)→v([\d.]+)\] (.+?)(?=—|$)', memory_text):
        caps.append({
            'id': f"EVO-{match.group(1)}",
            'archetype': match.group(2),
            'version': match.group(4),
            'description': match.group(5).strip()
        })
    
    # Pattern 2: [GROWTH /path] description
    for match in re.finditer(r'\[GROWTH (/[\w-]+)\] (.+?)(?:\((.+?)\))?\. (.+?)(?=—|$)', memory_text):
        caps.append({
            'id': f"GROWTH{match.group(1)}",
            'category': match.group(2).strip(),
            'scope': match.group(3) or 'general',
            'description': match.group(4).strip()
        })
    
    return caps

def emit_json(caps):
    return json.dumps({'capabilities': caps, 'count': len(caps)}, indent=2)

def emit_markdown(caps):
    lines = ['# Althea Capabilities\n']
    for cap in caps:
        lines.append(f"## {cap['id']}")
        for k, v in cap.items():
            if k != 'id':
                lines.append(f"- **{k}**: {v}")
        lines.append('')
    return '\n'.join(lines)

def emit_shell(caps):
    lines = [f'ALTHEA_CAP_COUNT={len(caps)}']
    for i, cap in enumerate(caps):
        safe_id = re.sub(r'[^A-Z0-9_]', '_', cap['id'].upper())
        lines.append(f"ALTHEA_CAP_{i}_{safe_id}='{cap.get('description', '')}'")
    return '\n'.join(lines)

if __name__ == '__main__':
    format_type = sys.argv[1] if len(sys.argv) > 1 else 'json'
    memory = sys.stdin.read()
    caps = parse_capabilities(memory)
    
    emitters = {'json': emit_json, 'md': emit_markdown, 'sh': emit_shell}
    print(emitters.get(format_type, emit_json)(caps))