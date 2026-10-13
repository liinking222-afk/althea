#!/usr/bin/env python3
import re
import json
import sys
from typing import List, Dict, Any

def parse_memory_line(line: str) -> Dict[str, Any]:
    """Duck-typed parser: extract what's there, ignore what isn't."""
    result = {'raw': line.strip()}
    
    # Multiple patterns, TMTOWTDI
    patterns = {
        'evo': r'\[EVO #(\d+) (\w+) v([\d.]+)→v([\d.]+)\] (.+?) —',
        'growth': r'\[GROWTH /autonomous-([^\]]+)\] ([^(]+)\(([^)]+)\)\. (.+?) —',
        'code': r'\[CODE-GEN id:(\w+) lang:(\w+)\] intent:\'([^\']+)\' → (\d+)',
    }
    
    for kind, pattern in patterns.items():
        match = re.search(pattern, line)
        if match:
            result['type'] = kind
            result['match'] = match.groups()
            break
    
    return result

def format_output(records: List[Dict], fmt: str = 'tsv') -> str:
    """TIMTOWTDI output formatting."""
    if fmt == 'json':
        return json.dumps(records, indent=2)
    elif fmt == 'md':
        if not records: return ""
        lines = ["| Type | Details |", "|------|---------|"]
        for r in records:
            lines.append(f"| {r.get('type', 'unknown')} | {str(r.get('match', r['raw'])[:60])} |")
        return '\n'.join(lines)
    else:  # tsv default - UNIX-friendly
        lines = []
        for r in records:
            parts = [r.get('type', 'unknown')]
            if 'match' in r:
                parts.extend(str(x) for x in r['match'])
            else:
                parts.append(r['raw'])
            lines.append('\t'.join(parts))
        return '\n'.join(lines)

def main():
    pattern = sys.argv[1] if len(sys.argv) > 1 else '.*'
    fmt = sys.argv[2] if len(sys.argv) > 2 else 'tsv'
    
    regex = re.compile(pattern, re.IGNORECASE)
    records = []
    
    for line in sys.stdin:
        if regex.search(line):
            records.append(parse_memory_line(line))
    
    print(format_output(records, fmt))

if __name__ == '__main__':
    main()