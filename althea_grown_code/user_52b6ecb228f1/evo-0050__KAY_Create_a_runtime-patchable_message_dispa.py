import inspect
import threading
from typing import Callable, Dict, Any, Optional

class MessageDispatcher:
    """Kay-inspired late-binding message dispatcher for runtime method rebinding."""
    
    def __init__(self):
        self._bindings: Dict[str, Callable] = {}
        self._lock = threading.RLock()
        self._message_log: list = []
        self._max_log = 1000
    
    def bind(self, message: str, handler: Callable) -> None:
        """Bind a message to a handler at runtime."""
        with self._lock:
            self._bindings[message] = handler
    
    def unbind(self, message: str) -> None:
        """Remove a message binding."""
        with self._lock:
            self._bindings.pop(message, None)
    
    def rebind(self, message: str, new_handler: Callable) -> Optional[Callable]:
        """Rebind message to new handler, returning old handler."""
        with self._lock:
            old = self._bindings.get(message)
            self._bindings[message] = new_handler
            return old
    
    def send(self, message: str, *args, **kwargs) -> Any:
        """Send a message and dispatch to current binding."""
        with self._lock:
            handler = self._bindings.get(message)
            self._message_log.append({
                'message': message,
                'bound': handler is not None,
                'args_count': len(args),
                'kwargs_keys': list(kwargs.keys())
            })
            if len(self._message_log) > self._max_log:
                self._message_log.pop(0)
        
        if handler is None:
            return self._handle_unknown(message, *args, **kwargs)
        
        return handler(*args, **kwargs)
    
    def _handle_unknown(self, message: str, *args, **kwargs) -> None:
        """Default handler for unbound messages."""
        pass
    
    def introspect(self) -> Dict[str, Any]:
        """Return current bindings and recent message traffic."""
        with self._lock:
            return {
                'bindings': {k: inspect.signature(v) for k, v in self._bindings.items()},
                'recent_messages': self._message_log[-20:],
                'total_bindings': len(self._bindings)
            }
    
    def snapshot(self) -> Dict[str, Callable]:
        """Capture current binding state."""
        with self._lock:
            return self._bindings.copy()
    
    def restore(self, snapshot: Dict[str, Callable]) -> None:
        """Restore bindings from snapshot."""
        with self._lock:
            self._bindings = snapshot.copy()

_global_dispatcher = MessageDispatcher()

def dispatch(message: str, *args, **kwargs):
    return _global_dispatcher.send(message, *args, **kwargs)

def bind_message(message: str, handler: Callable):
    _global_dispatcher.bind(message, handler)