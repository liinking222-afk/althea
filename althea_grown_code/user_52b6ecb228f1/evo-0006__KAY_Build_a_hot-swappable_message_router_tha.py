import inspect
import threading
from typing import Callable, Dict, Any, List, Optional

class MessageRouter:
    def __init__(self):
        self._routes: Dict[str, List[Callable]] = {}
        self._lock = threading.RLock()
        self._middleware: List[Callable] = []
        
    def bind(self, message_type: str, handler: Callable) -> None:
        """Late-bind a handler to a message type at runtime"""
        with self._lock:
            if message_type not in self._routes:
                self._routes[message_type] = []
            self._routes[message_type].append(handler)
    
    def unbind(self, message_type: str, handler: Callable) -> bool:
        """Remove a specific handler binding while system runs"""
        with self._lock:
            if message_type in self._routes:
                try:
                    self._routes[message_type].remove(handler)
                    return True
                except ValueError:
                    pass
        return False
    
    def rebind(self, message_type: str, old_handler: Callable, new_handler: Callable) -> bool:
        """Atomically swap handler implementations without dropping messages"""
        with self._lock:
            if message_type in self._routes:
                try:
                    idx = self._routes[message_type].index(old_handler)
                    self._routes[message_type][idx] = new_handler
                    return True
                except ValueError:
                    pass
        return False
    
    def send(self, message_type: str, payload: Any = None) -> List[Any]:
        """Message-passing dispatch to all bound handlers"""
        handlers = []
        with self._lock:
            handlers = self._routes.get(message_type, []).copy()
            middleware = self._middleware.copy()
        
        processed_payload = payload
        for mw in middleware:
            processed_payload = mw(message_type, processed_payload)
        
        results = []
        for handler in handlers:
            try:
                result = handler(processed_payload)
                results.append(result)
            except Exception as e:
                results.append({"error": str(e), "handler": handler.__name__})
        return results
    
    def add_middleware(self, transformer: Callable) -> None:
        """Add runtime transformation pipeline stage"""
        with self._lock:
            self._middleware.append(transformer)
    
    def introspect(self) -> Dict[str, List[str]]:
        """Reveal current system wiring for runtime inspection"""
        with self._lock:
            return {
                msg_type: [h.__name__ for h in handlers]
                for msg_type, handlers in self._routes.items()
            }