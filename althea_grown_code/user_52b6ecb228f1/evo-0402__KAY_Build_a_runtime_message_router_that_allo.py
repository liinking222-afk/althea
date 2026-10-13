#!/usr/bin/env python3
import json
import time
from typing import Any, Callable, Dict, Optional
from collections import defaultdict
from threading import RLock

class MessageRouter:
    """Late-binding message router enabling runtime module replacement."""
    
    def __init__(self):
        self.handlers: Dict[str, Callable] = {}
        self.message_queue: list = []
        self.interceptors: Dict[str, list] = defaultdict(list)
        self.lock = RLock()
        self.routing_table: Dict[str, str] = {}
        
    def register(self, message_type: str, handler: Callable, alias: Optional[str] = None):
        """Register a handler for a message type with optional aliasing."""
        with self.lock:
            key = alias or message_type
            self.handlers[key] = handler
            self.routing_table[message_type] = key
            
    def hot_swap(self, message_type: str, new_handler: Callable) -> Callable:
        """Replace handler at runtime, return old handler for rollback."""
        with self.lock:
            route_key = self.routing_table.get(message_type, message_type)
            old_handler = self.handlers.get(route_key)
            self.handlers[route_key] = new_handler
            return old_handler
            
    def intercept(self, message_type: str, interceptor: Callable):
        """Add message interceptor for observation/transformation."""
        with self.lock:
            self.interceptors[message_type].append(interceptor)
            
    def send(self, message_type: str, payload: Any) -> Any:
        """Send message through routing system with late binding."""
        with self.lock:
            route_key = self.routing_table.get(message_type, message_type)
            handler = self.handlers.get(route_key)
            
            if not handler:
                self.message_queue.append((message_type, payload, time.time()))
                return {"status": "queued", "reason": "no_handler"}
            
            # Apply interceptors
            modified_payload = payload
            for interceptor in self.interceptors.get(message_type, []):
                modified_payload = interceptor(modified_payload)
            
            return handler(modified_payload)
    
    def introspect(self) -> Dict[str, Any]:
        """Return current routing configuration for runtime inspection."""
        with self.lock:
            return {
                "handlers": list(self.handlers.keys()),
                "routes": self.routing_table.copy(),
                "queued": len(self.message_queue),
                "interceptors": {k: len(v) for k, v in self.interceptors.items()}
            }

if __name__ == "__main__":
    router = MessageRouter()
    router.register("perception", lambda x: f"v1:{x}")
    print(router.send("perception", "test"))
    router.hot_swap("perception", lambda x: f"v2:{x.upper()}")
    print(router.send("perception", "test"))
    print(json.dumps(router.introspect(), indent=2))