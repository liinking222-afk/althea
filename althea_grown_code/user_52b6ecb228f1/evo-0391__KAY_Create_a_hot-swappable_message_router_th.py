import inspect
from typing import Callable, Dict, Any, Optional
from functools import wraps
from threading import RLock

class LiveMessageRouter:
    """Kay-style late-binding message dispatcher with runtime mutation."""
    
    def __init__(self):
        self._handlers: Dict[str, Callable] = {}
        self._lock = RLock()
        self._message_log: list = []
        self._intercepts: Dict[str, list] = {}
    
    def register(self, message_name: str, handler: Callable):
        """Bind or rebind a message handler at runtime."""
        with self._lock:
            old = self._handlers.get(message_name)
            self._handlers[message_name] = handler
            if old:
                self._log(f"REBOUND: {message_name} from {old.__name__} to {handler.__name__}")
            return self
    
    def send(self, message_name: str, *args, **kwargs) -> Any:
        """Late-bound message dispatch with interception."""
        with self._lock:
            # Run interceptors
            for intercept in self._intercepts.get(message_name, []):
                intercept(message_name, args, kwargs)
            
            handler = self._handlers.get(message_name)
            if not handler:
                raise KeyError(f"No handler for message: {message_name}")
            
            self._log(f"DISPATCH: {message_name}")
            return handler(*args, **kwargs)
    
    def intercept(self, message_name: str, hook: Callable):
        """Add runtime interception without modifying handler."""
        with self._lock:
            if message_name not in self._intercepts:
                self._intercepts[message_name] = []
            self._intercepts[message_name].append(hook)
        return self
    
    def introspect(self, message_name: str) -> Optional[Dict[str, Any]]:
        """Examine current binding without invoking."""
        handler = self._handlers.get(message_name)
        if not handler:
            return None
        sig = inspect.signature(handler)
        return {
            "handler": handler.__name__,
            "signature": str(sig),
            "params": len(sig.parameters),
            "source": inspect.getsource(handler) if not inspect.isbuiltin(handler) else None
        }
    
    def _log(self, entry: str):
        self._message_log.append(entry)
    
    def audit_trail(self) -> list:
        """Return all binding mutations and dispatches."""
        return self._message_log.copy()

# Global router instance for Althea subsystems
ROUTER = LiveMessageRouter()