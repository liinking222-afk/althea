import re
from typing import Callable, Any, Dict, List, Tuple, Optional

class PatternRouter:
    """WALL-style pragmatic routing: multiple ways to match, flexible dispatch."""
    
    def __init__(self):
        self.routes: List[Tuple[re.Pattern, Callable, Dict[str, Any]]] = []
    
    def route(self, pattern: str, **metadata):
        """Decorator to register a handler with a regex pattern."""
        def decorator(func: Callable):
            compiled = re.compile(pattern, re.IGNORECASE | re.DOTALL)
            self.routes.append((compiled, func, metadata))
            return func
        return decorator
    
    def add(self, pattern: str, handler: Callable, **metadata):
        """Imperative registration (more than one way)."""
        compiled = re.compile(pattern, re.IGNORECASE | re.DOTALL)
        self.routes.append((compiled, handler, metadata))
    
    def dispatch(self, text: str, context: Optional[Dict] = None) -> List[Any]:
        """Match all patterns, invoke handlers duck-typed style."""
        results = []
        ctx = context or {}
        
        for pattern, handler, meta in self.routes:
            match = pattern.search(text)
            if match:
                # Duck typing: try different signatures
                try:
                    result = handler(match, **ctx)
                except TypeError:
                    try:
                        result = handler(match.group(0), **ctx)
                    except TypeError:
                        try:
                            result = handler(text, match, meta)
                        except TypeError:
                            result = handler()
                
                results.append({
                    'match': match.group(0),
                    'groups': match.groups(),
                    'result': result,
                    'metadata': meta,
                    'handler': handler.__name__
                })
        
        return results
    
    def route_first(self, text: str, context: Optional[Dict] = None) -> Optional[Any]:
        """Dispatch to first match only (common case optimization)."""
        results = self.dispatch(text, context)
        return results[0] if results else None

# Global instance for pragmatic use
router = PatternRouter()