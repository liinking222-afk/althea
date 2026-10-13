import inspect
from typing import Any, Callable, Dict, Optional
from functools import wraps

class MessageRouter:
    """Late-binding message dispatcher - modules are messages, bindings are fluid."""
    
    def __init__(self):
        self._bindings: Dict[str, Callable] = {}
        self._interceptors: list[Callable] = []
        self._history: list[tuple[str, Any]] = []
    
    def bind(self, message: str, handler: Callable) -> None:
        """Bind a message to a handler at runtime."""
        self._bindings[message] = handler
    
    def rebind(self, message: str, new_handler: Callable) -> Callable:
        """Replace binding while preserving old handler."""
        old = self._bindings.get(message)
        self._bindings[message] = new_handler
        return old
    
    def intercept(self, interceptor: Callable) -> None:
        """Add message interceptor for transformation/logging."""
        self._interceptors.append(interceptor)
    
    def send(self, message: str, *args, **kwargs) -> Any:
        """Send message to current binding."""
        if message not in self._bindings:
            raise ValueError(f"Unbound message: {message}")
        
        payload = {"message": message, "args": args, "kwargs": kwargs}
        
        for interceptor in self._interceptors:
            payload = interceptor(payload) or payload
        
        handler = self._bindings[payload["message"]]
        result = handler(*payload["args"], **payload["kwargs"])
        
        self._history.append((message, result))
        return result
    
    def introspect(self, message: str) -> Dict[str, Any]:
        """Examine current binding."""
        if message not in self._bindings:
            return {"bound": False}
        
        handler = self._bindings[message]
        return {
            "bound": True,
            "handler": handler.__name__,
            "signature": str(inspect.signature(handler)),
            "source": inspect.getsource(handler) if not inspect.isbuiltin(handler) else None
        }
    
    def evolve(self, message: str, modifier: Callable[[Callable], Callable]) -> None:
        """Transform a binding through a higher-order function."""
        if message in self._bindings:
            self._bindings[message] = modifier(self._bindings[message])

router = MessageRouter()