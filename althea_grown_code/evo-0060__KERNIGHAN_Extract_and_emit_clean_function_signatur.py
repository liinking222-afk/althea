#!/usr/bin/env python3
import re
import sys

def parse_evolution_entry(line):
    match = re.match(r'\[EVO #(\d+) (\w+) v([\d.]+)→v([\d.]+)\] (.+)', line)
    if match:
        return {
            'id': match.group(1),
            'archetype': match.group(2),
            'from_ver': match.group(3),
            'to_ver': match.group(4),
            'desc': match.group(5)
        }
    return None

def parse_growth_entry(line):
    match = re.match(r'\[GROWTH (/[\w-]+)\] ([^(]+)\(([^)]+)\)\. (.+)', line)
    if match:
        return {
            'path': match.group(1),
            'name': match.group(2).strip(),
            'domain': match.group(3),
            'desc': match.group(4)
        }
    return None

def emit_signature(entry, entry_type):
    if entry_type == 'evo':
        print(f"evo_{entry['id']}_{entry['archetype'].lower()}() -> v{entry['to_ver']}")
        print(f"  # {entry['desc'][:70]}")
    elif entry_type == 'growth':
        func_name = entry['name'].lower().replace(' ', '_')
        print(f"{func_name}({entry['domain']}) -> {entry['path']}")
        print(f"  # {entry['desc'][:70]}")

def main():
    for line in sys.stdin:
        line = line.strip()
        evo = parse_evolution_entry(line)
        if evo:
            emit_signature(evo, 'evo')
            continue
        growth = parse_growth_entry(line)
        if growth:
            emit_signature(growth, 'growth')

if __name__ == '__main__':
    main()