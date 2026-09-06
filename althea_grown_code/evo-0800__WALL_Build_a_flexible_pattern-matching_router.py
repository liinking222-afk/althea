#!/usr/bin/env python3
"""
/autonomous-pattern-router-wall
Pragmatic routing glue: multiple ways to match, duck-typed dispatch.
"""
import re
import sys
from typing import Any, Callable, Union, Pattern

class PatternRouter:
    def __init__(self):
        self.routes = []
    
    def add(self, pattern: Union[str, Pattern, Callable], handler: Callable, **meta):
        """TIMTOWTDI: string, regex, or callable matcher"""
        if isinstance(pattern, str):
            pattern = re.compile(pattern, re.IGNORECASE)
        self.routes.append({'pattern': pattern, 'handler': handler, 'meta': meta})
        return self
    
    def match(self, text: str) -> list:
        """Return all matching routes with captures"""
        matches = []
        for route in self.routes:
            p = route['pattern']
            if callable(p):
                result = p(text)
                if result:
                    matches.append({'handler': route['handler'], 'match': result, 'meta': route['meta']})
            elif hasattr(p, 'search'):
                m = p.search(text)
                if m:
                    matches.append({'handler': route['handler'], 'match': m.groupdict() or m.groups(), 'meta': route['meta']})
        return matches
    
    def route(self, text: str, **context) -> Any:
        """Dispatch to first match, duck-typed context injection"""
        matches = self.match(text)
        if not matches:
            return None
        route = matches[0]
        handler = route['handler']
        args = route['match']
        # Duck-type the handler call
        try:
            if isinstance(args, dict):
                return handler(**args, **context)
            elif isinstance(args, tuple):
                return handler(*args, **context)
            else:
                return handler(args, **context)
        except TypeError:
            return handler(text, **context)

def demo():
    router = PatternRouter()
    router.add(r'weather in (?P<city>\w+)', lambda city, **kw: f"Weather: {city}")
    router.add(r'analyze (?P<file>.*\.csv)', lambda file, **kw: f"Tabular: {file}")
    router.add(lambda x: 'help' in x.lower(), lambda x, **kw: "Help mode")
    
    for query in ["weather in Boston", "analyze data.csv", "I need help"]:
        print(f"{query} → {router.route(query)}")

if __name__ == '__main__':
    if len(sys.argv) > 1:
        demo()