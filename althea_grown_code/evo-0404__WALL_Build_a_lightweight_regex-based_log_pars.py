#!/usr/bin/env python3
import re
import sys
from typing import Union, Dict, List

class AltaLogParser:
    """Pragmatic log parser: there's more than one way to parse it."""
    
    PATTERNS = {
        'growth': r'\[GROWTH\s+(/[\w-]+)\]\s+([^(]+)\(([^)]+)\)\.\s+(.+?)(?:\s+—|$)',
        'autosynth': r'\[AUTOSYNTH\s+(/[\w-]+)\]\s+([^(]+)\(([^)]+)\)\.\s+(.+?)(?:\s+—|$)',
        'evo': r'\[EVO\s+#(\d+)\s+(\w+)\s+v([\d.]+)→v([\d.]+)\]\s+(.+?)(?:\s+—|$)',
    }
    
    def parse(self, line: str) -> Union[Dict, None]:
        """Duck-typed return: dict if match, None if not. TIMTOWTDI."""
        for kind, pattern in self.PATTERNS.items():
            match = re.search(pattern, line)
            if match:
                return self._extract(kind, match)
        return None
    
    def _extract(self, kind: str, match) -> Dict:
        if kind == 'growth':
            return {
                'type': 'growth',
                'path': match.group(1),
                'name': match.group(2).strip(),
                'category': match.group(3),
                'desc': match.group(4)
            }
        elif kind == 'autosynth':
            return {
                'type': 'autosynth',
                'path': match.group(1),
                'name': match.group(2).strip(),
                'tech': match.group(3),
                'desc': match.group(4)
            }
        else:  # evo
            return {
                'type': 'evo',
                'number': int(match.group(1)),
                'archetype': match.group(2),
                'from_ver': match.group(3),
                'to_ver': match.group(4),
                'desc': match.group(5)
            }
    
    def stream(self, input_stream=sys.stdin) -> List[Dict]:
        """UNIX philosophy: read stdin, write structured data."""
        results = []
        for line in input_stream:
            parsed = self.parse(line.strip())
            if parsed:
                results.append(parsed)
        return results

if __name__ == '__main__':
    parser = AltaLogParser()
    for entry in parser.stream():
        print(f"{entry['type'].upper()}: {entry.get('name', entry.get('archetype', 'N/A'))}")