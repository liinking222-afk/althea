import inspect
import threading
from typing import Any, Callable, Dict, Optional
from functools import wraps

class MessageRouter:
    """Kay-inspired late-binding message dispatcher for runtime module swapping."""
    
    def __init__(self):
        self._routes: Dict[str, Callable] = {}
        self._lock = threading.RLock()
        self._call_history: list = []
        
    def register(self, message: str, handler: Callable) -> None:
        """Register or replace a message handler at runtime."""
        with self._lock:
            self._routes[message] = handler
    
    def send(self, message: str, *args, **kwargs) -> Any:
        """Send message to current handler, late-bound at call time."""
        with self._lock:
            handler = self._routes.get(message)
            if handler is None:
                raise ValueError(f"No handler registered for message: {message}")
            self._call_history.append((message, args, kwargs))
            return handler(*args, **kwargs)
    
    def swap(self, message: str, new_handler: Callable) -> Callable:
        """Hot-swap handler and return previous one."""
        with self._lock:
            old_handler = self._routes.get(message)
            self._routes[message] = new_handler
            return old_handler
    
    def replay_last(self, count: int = 1) -> list:
        """Replay last N messages with current handlers (runtime reinterpretation)."""
        with self._lock:
            results = []
            for msg, args, kwargs in self._call_history[-count:]:
                handler = self._routes.get(msg)
                if handler:
                    results.append(handler(*args, **kwargs))
            return results

def routable(router: MessageRouter, message: str):
    """Decorator to make a method routable through the message system."""
    def decorator(func: Callable) -> Callable:
        router.register(message, func)
        
        @wraps(func)
        def wrapper(*args, **kwargs):
            return router.send(message, *args, **kwargs)
        return wrapper
    return decorator

# Global router for Althea's runtime message passing
ALTHEA_ROUTER = MessageRouter()

def evolve_module(module_name: str, new_implementation: Callable) -> None:
    """Evolve a module by swapping its implementation while Althea runs."""
    ALTHEA_ROUTER.swap(module_name, new_implementation)