#!/usr/bin/env python3
import re
import sys
import json
from typing import Dict, Any, Optional

class LogPatternExtractor:
    """WALL-style pragmatic log parser: many ways in, many ways out."""
    
    PATTERNS = {
        'autosynth': r'\[AUTOSYNTH\s+(/[\w-]+)\]\s+([^(]+)\(([^)]+)\)\.\s+(.+?)(?:\s+—|$)',
        'evo': r'\[EVO\s+#(\d+)\s+(\w+)\s+v([\d.]+)→([\d.]+)\]\s+(.+?)(?:\s+—|$)',
        'research': r'\[RESEARCH\]\s+[\'"](.+?)[\'"].*?concepts:\s+([\w;,\s]+)',
        'uplink': r'\[UPLINK\s+(\w+)\]\s+[\'"](.+?)[\'"].*?(\d+)\s+results?',
    }
    
    def extract(self, line: str) -> Optional[Dict[str, Any]]:
        """Duck-typed extraction: if it quacks like a pattern, parse it."""
        for ptype, pattern in self.PATTERNS.items():
            match = re.search(pattern, line, re.IGNORECASE)
            if match:
                return self._shape(ptype, match, line)
        return None
    
    def _shape(self, ptype: str, match: re.Match, raw: str) -> Dict[str, Any]:
        """Shape data pragmatically per pattern type."""
        base = {'type': ptype, 'raw': raw.strip()}
        
        if ptype == 'autosynth':
            base.update({'path': match.group(1), 'title': match.group(2).strip(),
                        'domain': match.group(3), 'desc': match.group(4)})
        elif ptype == 'evo':
            base.update({'id': match.group(1), 'arch': match.group(2),
                        'v_from': match.group(3), 'v_to': match.group(4),
                        'change': match.group(5)})
        elif ptype == 'research':
            concepts = [c.strip() for c in match.group(2).split(';')]
            base.update({'query': match.group(1), 'concepts': concepts})
        elif ptype == 'uplink':
            base.update({'action': match.group(1), 'query': match.group(2),
                        'results': int(match.group(3))})
        
        return base
    
    def format(self, event: Dict[str, Any], mode: str = 'json') -> str:
        """TIMTOWTDI output: json, tsv, kv, or compact."""
        if mode == 'tsv':
            return '\t'.join(str(v) for v in event.values())
        elif mode == 'kv':
            return ' '.join(f"{k}={v}" for k, v in event.items())
        elif mode == 'compact':
            return f"{event['type']}:{event.get('path','') or event.get('query','')[:40]}"
        return json.dumps(event)

if __name__ == '__main__':
    extractor = LogPatternExtractor()
    mode = sys.argv[1] if len(sys.argv) > 1 else 'json'
    
    for line in sys.stdin:
        event = extractor.extract(line)
        if event:
            print(extractor.format(event, mode))