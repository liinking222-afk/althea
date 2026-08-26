#!/usr/bin/env python3
"""
MEMGREP: Pattern-based memory log parser with flexible output formats.
Duck-typed regex extractor for Althea's self-reflection workflows.
"""

import re
import sys
from typing import Iterator, Dict, Any
from collections import defaultdict

class MemGrep:
    """There's more than one way to grep your memories."""
    
    PATTERNS = {
        'autosynth': r'\[AUTOSYNTH\s+(/[\w\-]+)\]\s+(.+?)\s+\((.+?)\)\.',
        'growth': r'\[GROWTH\s+(/[\w\-]+)\]\s+(.+?)\s+\((.+?)\)\.',
        'evo': r'\[EVO\s+#(\d+)\s+(\w+)\s+v([\d\.]+)→v([\d\.]+)\]\s+(.+?)\s+—',
        'tag': r'\((\w+(?:\-\w+)*)\)',
        'version': r'v(\d+\.\d+\.\d+)',
        'path': r'(/[\w\-/]+)',
    }
    
    def __init__(self, lines: Iterator[str]):
        self.lines = list(lines)
    
    def grep(self, pattern_name: str = None, custom: str = None) -> list:
        """Match pattern across all lines, return structured results."""
        regex = self.PATTERNS.get(pattern_name) if pattern_name else custom
        if not regex:
            return []
        
        matches = []
        for line in self.lines:
            for match in re.finditer(regex, line):
                matches.append({
                    'line': line.strip(),
                    'groups': match.groups(),
                    'span': match.span(),
                })
        return matches
    
    def stats(self) -> Dict[str, Any]:
        """Count occurrences of known patterns."""
        counts = defaultdict(int)
        for name in self.PATTERNS:
            counts[name] = len(self.grep(name))
        
        tags = set()
        for m in self.grep('tag'):
            tags.add(m['groups'][0])
        
        return {'pattern_counts': dict(counts), 'unique_tags': sorted(tags)}
    
    def extract_field(self, pattern_name: str, group: int = 0) -> list:
        """Extract specific capture group as flat list."""
        return [m['groups'][group] for m in self.grep(pattern_name)]

if __name__ == '__main__':
    mg = MemGrep(sys.stdin)
    
    # Default: show stats
    if len(sys.argv) == 1:
        import json
        print(json.dumps(mg.stats(), indent=2))
    else:
        # Pattern name or raw regex
        results = mg.grep(sys.argv[1]) if sys.argv[1] in mg.PATTERNS else mg.grep(custom=sys.argv[1])
        for r in results:
            print(f"{r['groups']}")