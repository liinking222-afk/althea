#!/usr/bin/env python3
import re
import sys
from typing import Iterator, Dict, Any
import json

class StreamPatternExtractor:
    """Pragmatic regex-based pattern extractor for Althea's log streams."""
    
    PATTERNS = {
        'autosynth': r'\[AUTOSYNTH\s+([^\]]+)\]\s+([^(]+)\(([^)]+)\)\.\s+(.+?)(?:\s+—|$)',
        'growth': r'\[GROWTH\s+([^\]]+)\]\s+([^(]+)\(([^)]+)\)\.(.+)',
        'evo': r'\[EVO\s+#(\d+)\s+(\w+)\s+v([\d.]+)→([\d.]+)\]\s+(.+?)(?:\s+—|$)',
        'system_map': r'\[SYSTEM-MAP\]\s+(.+)',
        'metric': r'(\w+):\s*([\d.]+)',
        'module_path': r'/([a-z-]+(?:/[a-z-]+)*)',
        'testid': r'testid:\s*([a-z-]+)',
    }
    
    def __init__(self):
        self.compiled = {k: re.compile(p) for k, p in self.PATTERNS.items()}
    
    def extract(self, line: str) -> Iterator[Dict[str, Any]]:
        """Duck-typed extraction: yield whatever matches."""
        line = line.strip()
        if not line:
            return
        
        if m := self.compiled['autosynth'].search(line):
            yield {
                'type': 'autosynth',
                'path': m.group(1),
                'name': m.group(2).strip(),
                'domain': m.group(3),
                'description': m.group(4).strip()
            }
        
        if m := self.compiled['growth'].search(line):
            yield {
                'type': 'growth',
                'path': m.group(1),
                'name': m.group(2).strip(),
                'domain': m.group(3),
                'description': m.group(4).strip()
            }
        
        if m := self.compiled['evo'].search(line):
            yield {
                'type': 'evo',
                'number': int(m.group(1)),
                'archetype': m.group(2),
                'from_version': m.group(3),
                'to_version': m.group(4),
                'description': m.group(5).strip()
            }
    
    def process_stream(self, stream=sys.stdin) -> None:
        """Process input stream, emit JSON per match."""
        for line in stream:
            for match in self.extract(line):
                print(json.dumps(match), flush=True)

if __name__ == '__main__':
    extractor = StreamPatternExtractor()
    extractor.process_stream()