import inspect
from typing import Callable, Dict, Any, Optional
from dataclasses import dataclass, field
from datetime import datetime

@dataclass
class MessageHandler:
    """Late-bound handler that can be modified at runtime."""
    func: Callable
    metadata: Dict[str, Any] = field(default_factory=dict)
    version: int = 1
    created_at: datetime = field(default_factory=datetime.now)

class RuntimeDispatcher:
    """Kay-style message-passing system with runtime modification."""
    
    def __init__(self):
        self._handlers: Dict[str, MessageHandler] = {}
        self._middleware: list[Callable] = []
        self._message_log: list[Dict] = []
    
    def register(self, pattern: str, handler: Callable, **metadata) -> None:
        """Register or replace a handler at runtime."""
        existing = self._handlers.get(pattern)
        version = existing.version + 1 if existing else 1
        self._handlers[pattern] = MessageHandler(handler, metadata, version)
    
    def unregister(self, pattern: str) -> Optional[MessageHandler]:
        """Remove handler, returning it for potential restoration."""
        return self._handlers.pop(pattern, None)
    
    def send(self, pattern: str, message: Any) -> Any:
        """Send message to handler via late binding."""
        handler = self._handlers.get(pattern)
        if not handler:
            return self._default_handler(pattern, message)
        
        # Apply middleware chain
        processed = message
        for mw in self._middleware:
            processed = mw(pattern, processed)
        
        # Log before execution
        self._message_log.append({
            'pattern': pattern,
            'timestamp': datetime.now(),
            'version': handler.version
        })
        
        return handler.func(processed)
    
    def _default_handler(self, pattern: str, message: Any) -> Any:
        """Fallback when no handler registered."""
        return {'unhandled': pattern, 'message': message}
    
    def modify_handler(self, pattern: str, transform: Callable) -> bool:
        """Modify existing handler function at runtime."""
        if pattern not in self._handlers:
            return False
        handler = self._handlers[pattern]
        handler.func = transform(handler.func)
        handler.version += 1
        return True
    
    def add_middleware(self, func: Callable) -> None:
        """Insert message transformation in the pipeline."""
        self._middleware.append(func)
    
    def introspect(self, pattern: str) -> Optional[Dict]:
        """Examine handler at runtime."""
        handler = self._handlers.get(pattern)
        if not handler:
            return None
        return {
            'version': handler.version,
            'source': inspect.getsource(handler.func),
            'metadata': handler.metadata,
            'created_at': handler.created_at.isoformat()
        }

# Global dispatcher instance
dispatcher = RuntimeDispatcher()