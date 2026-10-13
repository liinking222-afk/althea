import inspect
from typing import Any, Callable, Dict, List, Optional
from dataclasses import dataclass, field
from collections import defaultdict

@dataclass
class Message:
    selector: str
    args: tuple
    kwargs: dict
    sender: Optional[str] = None
    
@dataclass
class MessageHandler:
    handler: Callable
    priority: int = 0
    intercepts: bool = False

class LateBindingDispatcher:
    def __init__(self):
        self._handlers: Dict[str, List[MessageHandler]] = defaultdict(list)
        self._objects: Dict[str, Any] = {}
        self._method_cache: Dict[str, Callable] = {}
        
    def register_object(self, name: str, obj: Any):
        """Register an object that can receive messages"""
        self._objects[name] = obj
        self._invalidate_cache()
        
    def deregister_object(self, name: str):
        """Remove an object at runtime"""
        self._objects.pop(name, None)
        self._invalidate_cache()
        
    def add_handler(self, selector: str, handler: Callable, priority: int = 0, intercepts: bool = False):
        """Add a handler for a message selector, optionally intercepting"""
        mh = MessageHandler(handler, priority, intercepts)
        self._handlers[selector].append(mh)
        self._handlers[selector].sort(key=lambda h: h.priority, reverse=True)
        self._invalidate_cache()
        
    def remove_handler(self, selector: str, handler: Callable):
        """Remove a specific handler at runtime"""
        self._handlers[selector] = [h for h in self._handlers[selector] if h.handler != handler]
        self._invalidate_cache()
        
    def send(self, target: str, selector: str, *args, **kwargs) -> Any:
        """Send a message to a target object with late binding"""
        msg = Message(selector, args, kwargs, sender=None)
        
        # Check interceptors first
        if selector in self._handlers:
            for handler in self._handlers[selector]:
                if handler.intercepts:
                    return handler.handler(msg)
        
        # Resolve target at message-send time
        if target not in self._objects:
            raise ValueError(f"Object '{target}' not registered")
            
        obj = self._objects[target]
        method = getattr(obj, selector, None)
        
        if method is None:
            # Try handlers as fallback
            if selector in self._handlers and self._handlers[selector]:
                return self._handlers[selector][0].handler(msg)
            raise AttributeError(f"'{target}' has no method '{selector}'")
        
        # Execute registered handlers before method
        for handler in self._handlers.get(selector, []):
            if not handler.intercepts:
                handler.handler(msg)
        
        return method(*args, **kwargs)
    
    def _invalidate_cache(self):
        self._method_cache.clear()

# Global runtime dispatcher
RUNTIME = LateBindingDispatcher()