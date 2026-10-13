import inspect
import types
from typing import Any, Callable, Dict, Optional
from functools import wraps

class MessageRouter:
    def __init__(self):
        self._routes: Dict[str, Callable] = {}
        self._interceptors: Dict[str, list] = {}
        self._version_map: Dict[str, int] = {}
    
    def register(self, message_type: str, handler: Callable, version: int = 1):
        """Late-bind a handler to a message type"""
        self._routes[message_type] = handler
        self._version_map[message_type] = version
        if message_type not in self._interceptors:
            self._interceptors[message_type] = []
        return self
    
    def intercept(self, message_type: str, interceptor: Callable):
        """Add runtime interception layer"""
        if message_type not in self._interceptors:
            self._interceptors[message_type] = []
        self._interceptors[message_type].append(interceptor)
        return self
    
    def send(self, message_type: str, payload: Any) -> Any:
        """Send message with late-bound dispatch"""
        if message_type not in self._routes:
            raise KeyError(f"No handler for message type: {message_type}")
        
        modified_payload = payload
        for interceptor in self._interceptors.get(message_type, []):
            modified_payload = interceptor(modified_payload)
        
        handler = self._routes[message_type]
        return handler(modified_payload)
    
    def hot_swap(self, message_type: str, new_handler: Callable):
        """Replace handler without stopping the system"""
        old_version = self._version_map.get(message_type, 0)
        self.register(message_type, new_handler, old_version + 1)
        return old_version + 1
    
    def introspect(self, message_type: str) -> Dict[str, Any]:
        """Runtime reflection of handler state"""
        if message_type not in self._routes:
            return {}
        
        handler = self._routes[message_type]
        return {
            "signature": str(inspect.signature(handler)),
            "version": self._version_map.get(message_type, 0),
            "interceptors": len(self._interceptors.get(message_type, [])),
            "source": inspect.getsource(handler) if not isinstance(handler, types.BuiltinFunctionType) else "builtin"
        }
    
    def create_proxy(self, message_type: str) -> Callable:
        """Generate callable proxy for message passing"""
        @wraps(self._routes.get(message_type, lambda: None))
        def proxy(*args, **kwargs):
            payload = {"args": args, "kwargs": kwargs}
            result = self.send(message_type, payload)
            return result
        return proxy

router = MessageRouter()