#!/usr/bin/env python3
import sys
import re
from typing import TextIO

def extract_operations(stream: TextIO) -> None:
    """Extract composable operations from Althea evolution logs as plain-text primitives."""
    
    operation_pattern = re.compile(
        r'\[EVO #(\d+) (\w+) v([\d.]+)→v([\d.]+)\] (.+?) — (.+?)(?:\n|$)',
        re.MULTILINE
    )
    
    growth_pattern = re.compile(
        r'\[GROWTH /([^\]]+)\] (.+?) \(([^)]+)\)\. (.+?) — (.+?)(?:\n|$)',
        re.MULTILINE
    )
    
    for line in stream:
        # Extract EVO operations
        evo_match = operation_pattern.search(line)
        if evo_match:
            evo_id, archetype, old_ver, new_ver, intent, capability = evo_match.groups()
            emit_operation('evo', {
                'id': evo_id,
                'archetype': archetype.lower(),
                'version': new_ver,
                'intent': intent.strip(),
                'capability': capability.strip()
            })
            continue
        
        # Extract GROWTH operations
        growth_match = growth_pattern.search(line)
        if growth_match:
            slug, name, category, description, effect = growth_match.groups()
            emit_operation('growth', {
                'slug': slug,
                'name': name.strip(),
                'category': category.strip(),
                'description': description.strip(),
                'effect': effect.strip()
            })

def emit_operation(op_type: str, fields: dict) -> None:
    """Emit operation as pipe-friendly plain text."""
    if op_type == 'evo':
        print(f"evo|{fields['id']}|{fields['archetype']}|{fields['version']}|{fields['intent']}")
    elif op_type == 'growth':
        print(f"growth|{fields['slug']}|{fields['category']}|{fields['description']}")

def main():
    if len(sys.argv) > 1 and sys.argv[1] in ['-h', '--help']:
        print("Usage: cat memory.txt | ./evo_extract.py | grep archetype | cut -d'|' -f3")
        sys.exit(0)
    
    extract_operations(sys.stdin)

if __name__ == '__main__':
    main()