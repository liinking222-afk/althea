#!/usr/bin/env python3
import re
import sys
from collections import Counter, defaultdict
from typing import TextIO

class MemoryPatternExtractor:
    """Pragmatic pattern surfacing from heterogeneous logs."""
    
    def __init__(self):
        self.patterns = {
            'module_name': re.compile(r'/autonomous-([a-z-]+)-\d+'),
            'category': re.compile(r'\(([a-z-]+)\)'),
            'archetype': re.compile(r'(?:ARCHETYPE|#\d+)\s+([A-Z]+)'),
            'action': re.compile(r'^\[([A-Z]+)'),
            'theme': re.compile(r'\'([a-z-]+(?:-[a-z-]+)*)\''),
        }
        self.hits = defaultdict(Counter)
    
    def ingest(self, stream: TextIO):
        """Duck-typed input: file, stdin, string list—doesn't matter."""
        for line in stream:
            line = line.strip()
            if not line:
                continue
            for pattern_type, regex in self.patterns.items():
                for match in regex.finditer(line):
                    self.hits[pattern_type][match.group(1)] += 1
    
    def surface(self, min_freq: int = 2):
        """Surface patterns above threshold. TMTOWTDI but this is simple."""
        results = {}
        for ptype, counter in self.hits.items():
            filtered = {k: v for k, v in counter.items() if v >= min_freq}
            if filtered:
                results[ptype] = filtered.most_common()
        return results
    
    def emit_compact(self):
        """Writer-optimized output: dense. Reader-optimized: scannable."""
        surfaced = self.surface()
        for ptype, items in sorted(surfaced.items()):
            print(f"{ptype}:", end=" ")
            print(", ".join(f"{k}×{v}" for k, v in items[:5]))

if __name__ == "__main__":
    extractor = MemoryPatternExtractor()
    extractor.ingest(sys.stdin)
    extractor.emit_compact()