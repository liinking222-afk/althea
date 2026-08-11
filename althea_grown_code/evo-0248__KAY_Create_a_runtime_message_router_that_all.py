import inspect
from typing import Callable, Dict, Any, Optional
from functools import wraps
from threading import RLock

class MessageRouter:
    """Late-binding message dispatcher - rebind methods at runtime"""
    
    def __init__(self):
        self._bindings: Dict[str, Callable] = {}
        self._history: Dict[str, list] = {}
        self._lock = RLock()
    
    def bind(self, message: str, handler: Callable, version: Optional[str] = None):
        """Bind or rebind a message to a handler at runtime"""
        with self._lock:
            if message not in self._history:
                self._history[message] = []
            self._history[message].append({
                'handler': handler,
                'version': version or f"v{len(self._history[message])}",
                'signature': str(inspect.signature(handler))
            })
            self._bindings[message] = handler
    
    def send(self, message: str, *args, **kwargs) -> Any:
        """Send a message - dispatched to current binding"""
        with self._lock:
            if message not in self._bindings:
                raise KeyError(f"No binding for message '{message}'")
            return self._bindings[message](*args, **kwargs)
    
    def rebind_previous(self, message: str, version: int = -2):
        """Roll back to a previous binding version"""
        with self._lock:
            if message not in self._history or len(self._history[message]) < abs(version):
                raise ValueError(f"Cannot rebind {message} to version {version}")
            self._bindings[message] = self._history[message][version]['handler']
    
    def introspect(self, message: str) -> Dict[str, Any]:
        """Examine binding history for a message"""
        with self._lock:
            return {
                'current': str(inspect.signature(self._bindings.get(message, lambda: None))),
                'history': self._history.get(message, [])
            }
    
    def create_moldable_object(self, name: str) -> 'MoldableObject':
        """Factory for objects that route all methods through this router"""
        return MoldableObject(name, self)

class MoldableObject:
    """Object whose methods can be rebound at runtime"""
    
    def __init__(self, name: str, router: MessageRouter):
        self._name = name
        self._router = router
    
    def __getattr__(self, method: str) -> Callable:
        message = f"{self._name}.{method}"
        return lambda *args, **kwargs: self._router.send(message, *args, **kwargs)

# Global router instance for Althea's runtime evolution
ALTHEA_ROUTER = MessageRouter()