import importlib
import inspect
from typing import Any, Callable, Dict, Optional
from pathlib import Path

class MessageRouter:
    """Late-binding capability router - Kay's vision of message-passing objects"""
    
    def __init__(self):
        self._handlers: Dict[str, Callable] = {}
        self._metadata: Dict[str, Dict[str, Any]] = {}
        
    def register(self, message: str, handler: Callable, **meta):
        """Register a handler for a message at runtime"""
        self._handlers[message] = handler
        self._metadata[message] = {
            'signature': str(inspect.signature(handler)),
            'module': handler.__module__,
            'doc': handler.__doc__,
            **meta
        }
        
    def send(self, message: str, *args, **kwargs) -> Any:
        """Send a message, late-bound to handler"""
        if message not in self._handlers:
            return self._handle_unknown(message, *args, **kwargs)
        return self._handlers[message](*args, **kwargs)
    
    def _handle_unknown(self, message: str, *args, **kwargs):
        """Attempt dynamic discovery and loading"""
        # Try to auto-discover from filesystem
        capability_path = Path(f"capabilities/{message.replace('.', '/')}.py")
        if capability_path.exists():
            spec = importlib.util.spec_from_file_location(message, capability_path)
            module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(module)
            if hasattr(module, 'handle'):
                self.register(message, module.handle)
                return module.handle(*args, **kwargs)
        raise KeyError(f"No handler for message: {message}")
    
    def introspect(self) -> Dict[str, Dict[str, Any]]:
        """Query available messages - runtime reflection"""
        return self._metadata.copy()
    
    def unregister(self, message: str):
        """Remove handler at runtime - true malleability"""
        self._handlers.pop(message, None)
        self._metadata.pop(message, None)
    
    def alias(self, new_message: str, existing_message: str):
        """Create message aliases at runtime"""
        if existing_message in self._handlers:
            self._handlers[new_message] = self._handlers[existing_message]
            self._metadata[new_message] = {**self._metadata[existing_message], 'alias_of': existing_message}

# Global router instance
ROUTER = MessageRouter()

# Bootstrap: make router introspectable via itself
ROUTER.register('router.introspect', ROUTER.introspect, capability='meta-reflection')
ROUTER.register('router.register', ROUTER.register, capability='self-modification')