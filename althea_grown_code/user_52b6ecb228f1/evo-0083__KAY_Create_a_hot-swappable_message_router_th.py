import inspect
import threading
from typing import Callable, Dict, Any, Optional
from functools import wraps

class MessageRouter:
    """Late-binding message dispatcher - rebind methods while running"""
    
    def __init__(self):
        self._routes: Dict[str, Callable] = {}
        self._lock = threading.RLock()
        self._middleware: list[Callable] = []
        self._history: list[tuple[str, str]] = []
    
    def bind(self, message: str, handler: Callable) -> None:
        """Bind or rebind a message to a handler at runtime"""
        with self._lock:
            old = self._routes.get(message, None)
            self._routes[message] = handler
            self._history.append((message, f"rebound" if old else "bound"))
    
    def unbind(self, message: str) -> Optional[Callable]:
        """Remove a binding and return the old handler"""
        with self._lock:
            return self._routes.pop(message, None)
    
    def add_middleware(self, fn: Callable) -> None:
        """Add middleware to transform messages in flight"""
        with self._lock:
            self._middleware.append(fn)
    
    def send(self, message: str, *args, **kwargs) -> Any:
        """Send a message through the routing system"""
        with self._lock:
            handler = self._routes.get(message)
            if not handler:
                raise ValueError(f"No handler bound for message: {message}")
            
            # Apply middleware transformations
            context = {"message": message, "args": args, "kwargs": kwargs}
            for mw in self._middleware:
                context = mw(context) or context
            
            return handler(*context["args"], **context["kwargs"])
    
    def introspect(self) -> Dict[str, Any]:
        """Examine current routing state"""
        with self._lock:
            return {
                "routes": {k: inspect.signature(v) for k, v in self._routes.items()},
                "middleware_count": len(self._middleware),
                "history": self._history[-20:]
            }
    
    def replace_self(self, new_router: 'MessageRouter') -> None:
        """Hot-swap the entire routing table"""
        with self._lock:
            self._routes = new_router._routes.copy()
            self._middleware = new_router._middleware.copy()
            self._history.append(("SYSTEM", "hot_swap_complete"))

# Global singleton for runtime modification
ROUTER = MessageRouter()