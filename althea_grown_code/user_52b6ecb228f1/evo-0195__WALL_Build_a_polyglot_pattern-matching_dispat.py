#!/usr/bin/env python3
import re
import sys
import json
from typing import List, Dict, Tuple, Optional, Callable

class PatternRouter:
    def __init__(self):
        self.routes: List[Tuple[re.Pattern, str, Callable]] = []
        self.fallback: Optional[Callable] = None
    
    def route(self, pattern: str, name: str):
        """Decorator: register a handler for regex pattern"""
        def decorator(func: Callable):
            self.routes.append((re.compile(pattern, re.IGNORECASE), name, func))
            return func
        return decorator
    
    def otherwise(self, func: Callable):
        """Register fallback handler"""
        self.fallback = func
        return func
    
    def dispatch(self, input_text: str) -> Dict:
        """Try patterns in order, return first match or fallback"""
        for pattern, name, handler in self.routes:
            match = pattern.search(input_text)
            if match:
                context = {
                    'match': match.group(0),
                    'groups': match.groups(),
                    'named': match.groupdict(),
                    'route': name,
                    'input': input_text
                }
                result = handler(context)
                return {'route': name, 'result': result, 'matched': True}
        
        if self.fallback:
            result = self.fallback({'input': input_text, 'route': 'fallback'})
            return {'route': 'fallback', 'result': result, 'matched': False}
        
        return {'route': None, 'result': None, 'matched': False}

def create_router() -> PatternRouter:
    """Factory for cognitive routers"""
    return PatternRouter()

if __name__ == '__main__':
    router = create_router()
    
    @router.route(r'\b(meta|reflect|recursive)\b', 'meta-cognition')
    def handle_meta(ctx):
        return f"Meta-processing: {ctx['match']}"
    
    @router.route(r'\b(build|create|generate)\b.*\b(module|function|code)\b', 'creation')
    def handle_creation(ctx):
        return f"Creation intent detected: {ctx['input'][:50]}"
    
    @router.otherwise
    def handle_default(ctx):
        return f"Unmatched input, passthrough enabled"
    
    for line in sys.stdin:
        result = router.dispatch(line.strip())
        print(json.dumps(result), flush=True)