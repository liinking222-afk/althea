#!/usr/bin/env python3
import re
from collections import defaultdict
from typing import Any, Callable

class PatternDuck:
    """Lazy regex matcher - if it quacks like a pattern, treat it like one."""
    
    def __init__(self):
        self.patterns = {}
        self.cache = defaultdict(dict)
        
    def register(self, name: str, pattern: str, transform: Callable = None):
        """Register pattern + optional transform. TMTOWTDI."""
        self.patterns[name] = {
            're': re.compile(pattern, re.IGNORECASE | re.DOTALL),
            'fn': transform or (lambda x: x)
        }
        return self
    
    def __call__(self, text: str, use_cache: bool = True):
        """Ducktype the text - returns dict of all matches."""
        cache_key = hash(text) if use_cache else None
        if cache_key in self.cache:
            return self.cache[cache_key]
        
        result = {}
        for name, spec in self.patterns.items():
            matches = spec['re'].findall(text)
            if matches:
                result[name] = [spec['fn'](m) for m in matches]
        
        if cache_key:
            self.cache[cache_key] = result
        return result
    
    def pipe(self, text: str, *filters: str):
        """UNIX-style: text | filter1 | filter2"""
        result = self(text)
        for f in filters:
            if f in result:
                result = {f: result[f]}
        return result

# Bootstrap with Althea-relevant patterns
duck = PatternDuck()
duck.register('evo', r'\[EVO #(\d+) (\w+)', lambda m: {'id': m[0], 'archetype': m[1]})
duck.register('growth', r'/autonomous-([\w-]+)', lambda m: m.replace('-', '_'))
duck.register('metrics', r'(integrity|coherence|link)', lambda m: m.lower())
duck.register('signal', r'(interference|frequency|resonan\w+)', lambda m: m.lower())

def quack(text: str) -> dict[str, Any]:
    """Main entry: throw text at patterns, see what sticks."""
    return duck(text)