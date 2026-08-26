#!/usr/bin/env python3
import re
import sys
from typing import Dict, Callable, Optional, List, Tuple

class PatternRouter:
    def __init__(self):
        self.routes: List[Tuple[re.Pattern, Callable]] = []
        self.fallback: Optional[Callable] = None
    
    def register(self, pattern: str, handler: Callable, flags=re.IGNORECASE):
        """Register a pattern with its handler - multiple patterns can match."""
        self.routes.append((re.compile(pattern, flags), handler))
    
    def set_fallback(self, handler: Callable):
        """Set handler for unmatched input."""
        self.fallback = handler
    
    def route(self, text: str) -> List[dict]:
        """Return all matching handlers with their match data."""
        matches = []
        for pattern, handler in self.routes:
            if match := pattern.search(text):
                matches.append({
                    'handler': handler,
                    'match': match,
                    'groups': match.groups(),
                    'groupdict': match.groupdict()
                })
        return matches if matches else ([{'handler': self.fallback, 'match': None, 'groups': (), 'groupdict': {}}] if self.fallback else [])
    
    def dispatch(self, text: str, mode='first'):
        """Execute handlers: 'first', 'all', or 'collect'."""
        matches = self.route(text)
        if mode == 'first':
            return matches[0]['handler'](matches[0]) if matches else None
        elif mode == 'all':
            return [m['handler'](m) for m in matches]
        elif mode == 'collect':
            return matches
        
    def serve_stdio(self, mode='first'):
        """Read lines from stdin and dispatch each."""
        for line in sys.stdin:
            line = line.rstrip('\n')
            if not line:
                continue
            result = self.dispatch(line, mode)
            if result is not None:
                print(result)

if __name__ == '__main__':
    router = PatternRouter()
    
    # Example routes - duck-typed flexibility
    router.register(r'orbital[_-]?prop(?:agation)?', 
                   lambda m: f"EXEC:orbital-propagation")
    router.register(r'spectral[_-]?analysis|fft|frequency', 
                   lambda m: f"EXEC:spectral-analysis")
    router.register(r'invoke\s+(?P<module>\S+)(\s+(?P<args>.+))?',
                   lambda m: f"EXEC:{m['groupdict']['module']} {m['groupdict'].get('args', '')}")
    router.register(r'^/(\w+(?:[_-]\w+)*)', 
                   lambda m: f"EXEC:{m['groups'][0]}")
    router.set_fallback(lambda m: "UNROUTED")
    
    router.serve_stdio()