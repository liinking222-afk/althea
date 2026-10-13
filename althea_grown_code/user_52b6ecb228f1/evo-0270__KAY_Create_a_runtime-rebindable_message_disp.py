import threading
from typing import Dict, Callable, Any, Optional
from dataclasses import dataclass
from datetime import datetime

@dataclass
class Message:
    type: str
    payload: Any
    timestamp: float = None
    
    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = datetime.now().timestamp()

class RuntimeDispatcher:
    """Late-binding message dispatcher - handlers can be replaced at runtime"""
    
    def __init__(self):
        self._handlers: Dict[str, Callable] = {}
        self._lock = threading.RLock()
        self._history = []
        self._max_history = 100
    
    def bind(self, message_type: str, handler: Callable) -> None:
        """Bind or rebind a handler for a message type at runtime"""
        with self._lock:
            self._handlers[message_type] = handler
            self._log(f"bound:{message_type}")
    
    def unbind(self, message_type: str) -> Optional[Callable]:
        """Remove a handler, returning it for potential restoration"""
        with self._lock:
            handler = self._handlers.pop(message_type, None)
            if handler:
                self._log(f"unbound:{message_type}")
            return handler
    
    def send(self, message: Message) -> Any:
        """Send a message - handler is resolved at call time (late binding)"""
        with self._lock:
            handler = self._handlers.get(message.type)
            self._history.append((message, handler is not None))
            if len(self._history) > self._max_history:
                self._history.pop(0)
        
        if handler:
            return handler(message)
        return None
    
    def introspect(self) -> Dict[str, Any]:
        """Reflect on current state - handlers, history, bindings"""
        with self._lock:
            return {
                "handlers": list(self._handlers.keys()),
                "history_size": len(self._history),
                "recent_unhandled": [msg.type for msg, handled in self._history[-10:] if not handled]
            }
    
    def _log(self, event: str):
        self._history.append((event, True))

# Global instance for runtime modification
dispatcher = RuntimeDispatcher()