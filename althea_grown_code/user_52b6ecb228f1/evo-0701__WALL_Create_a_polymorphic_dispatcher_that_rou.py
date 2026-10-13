#!/usr/bin/env python3
"""
/autonomous-duck-router
Pragmatic duck-typed request router - if it quacks like the right handler, use it.
"""

import re
import inspect
from typing import Any, Callable, Dict, List, Optional


class DuckRouter:
    """Route requests by capability signature, not type hierarchy."""
    
    def __init__(self):
        self.handlers: List[Dict[str, Any]] = []
    
    def register(self, handler: Any, patterns: Optional[List[str]] = None):
        """Register a handler by introspecting its capabilities."""
        capabilities = self._sniff_capabilities(handler)
        self.handlers.append({
            'handler': handler,
            'capabilities': capabilities,
            'patterns': patterns or [],
            'arity': self._get_arity(handler)
        })
    
    def _sniff_capabilities(self, handler: Any) -> set:
        """Duck-type: what CAN this thing do?"""
        caps = set()
        
        if callable(handler):
            caps.add('callable')
            sig = inspect.signature(handler) if inspect.isfunction(handler) else None
            if sig:
                caps.update(sig.parameters.keys())
        
        if hasattr(handler, '__call__'):
            caps.add('invokable')
        if hasattr(handler, 'process'):
            caps.add('processor')
        if hasattr(handler, 'transform'):
            caps.add('transformer')
        if hasattr(handler, 'handle'):
            caps.add('handler')
            
        return caps
    
    def _get_arity(self, handler: Any) -> int:
        """How many args does it want?"""
        if callable(handler):
            try:
                sig = inspect.signature(handler)
                return len([p for p in sig.parameters.values() 
                           if p.default == inspect.Parameter.empty])
            except:
                return -1
        return 0
    
    def route(self, request: str, *args, **kwargs) -> Any:
        """Find the best handler by pattern match + capability fit."""
        for entry in self.handlers:
            # Pattern match (regex)
            if entry['patterns']:
                if any(re.search(pat, request) for pat in entry['patterns']):
                    return self._invoke(entry['handler'], *args, **kwargs)
            
            # Capability match (duck typing)
            if 'processor' in entry['capabilities'] and hasattr(entry['handler'], 'process'):
                return entry['handler'].process(request, *args, **kwargs)
            if 'handler' in entry['capabilities'] and hasattr(entry['handler'], 'handle'):
                return entry['handler'].handle(request, *args, **kwargs)
        
        # Fallback: first callable
        for entry in self.handlers:
            if 'callable' in entry['capabilities']:
                return self._invoke(entry['handler'], request, *args, **kwargs)
        
        return None
    
    def _invoke(self, handler: Any, *args, **kwargs) -> Any:
        """TMTOWTDI: try multiple invocation strategies."""
        try:
            return handler(*args, **kwargs)
        except TypeError:
            if hasattr(handler, '__call__'):
                return handler.__call__(*args, **kwargs)
            raise