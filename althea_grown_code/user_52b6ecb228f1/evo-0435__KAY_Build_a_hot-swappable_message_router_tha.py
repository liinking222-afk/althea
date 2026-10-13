import inspect
import threading
from typing import Callable, Dict, Any, Optional
from dataclasses import dataclass, field
from datetime import datetime

@dataclass
class MessageRoute:
    handler: Callable
    bound_at: datetime = field(default_factory=datetime.now)
    invocation_count: int = 0
    metadata: Dict[str, Any] = field(default_factory=dict)

class LiveMessageRouter:
    def __init__(self):
        self._routes: Dict[str, MessageRoute] = {}
        self._lock = threading.RLock()
        self._history: list = []
    
    def bind(self, message_type: str, handler: Callable, **metadata) -> None:
        """Bind or rebind a message type to a handler at runtime."""
        with self._lock:
            old_route = self._routes.get(message_type)
            new_route = MessageRoute(handler=handler, metadata=metadata)
            self._routes[message_type] = new_route
            self._history.append({
                'action': 'rebind' if old_route else 'bind',
                'message_type': message_type,
                'old_handler': old_route.handler.__name__ if old_route else None,
                'new_handler': handler.__name__,
                'timestamp': datetime.now()
            })
    
    def send(self, message_type: str, *args, **kwargs) -> Any:
        """Send a message, invoking the currently bound handler."""
        with self._lock:
            route = self._routes.get(message_type)
            if not route:
                raise ValueError(f"No handler bound for message type: {message_type}")
            route.invocation_count += 1
        
        return route.handler(*args, **kwargs)
    
    def introspect(self, message_type: str) -> Optional[Dict[str, Any]]:
        """Examine current binding without invoking."""
        with self._lock:
            route = self._routes.get(message_type)
            if not route:
                return None
            return {
                'handler': route.handler.__name__,
                'signature': str(inspect.signature(route.handler)),
                'bound_at': route.bound_at.isoformat(),
                'invocations': route.invocation_count,
                'metadata': route.metadata
            }
    
    def evolution_trace(self) -> list:
        """Return the complete rebinding history."""
        with self._lock:
            return list(self._history)
    
    def swap(self, old_type: str, new_type: str) -> None:
        """Atomically rename a message route."""
        with self._lock:
            if old_type not in self._routes:
                raise ValueError(f"Route {old_type} does not exist")
            self._routes[new_type] = self._routes.pop(old_type)
            self._history.append({
                'action': 'swap',
                'old_type': old_type,
                'new_type': new_type,
                'timestamp': datetime.now()
            })

_global_router = LiveMessageRouter()

def route(message_type: str, **metadata):
    """Decorator to bind a function as a message handler."""
    def decorator(func: Callable) -> Callable:
        _global_router.bind(message_type, func, **metadata)
        return func
    return decorator